# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: lvm/tel/calibration.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from lvm.actors import lvm, lvm_amqpc, invoke, unpack, asyncio, logger, LoggerCommand

import sep
from astropy.io import fits
from photutils.centroids import centroid_com, centroid_quadratic
from photutils.centroids import centroid_1dg, centroid_2dg


def sep_objects(data):
        bkg = sep.Background(data)
        data_sub = data - bkg
        objects = sep.extract(data_sub, 1.5, err=bkg.globalrms)
        object_index_sorted_by_peak = list({k: v for k, v in sorted({idx: objects['peak'][idx] for idx in range(len(objects))}.items(), key=lambda item: item[1], reverse=True)}.keys())
        return objects, object_index_sorted_by_peak

async def calibrate(telsubsys, exptime, offset, command = LoggerCommand(logger)):
    try:
        logger.debug(f"calibrate {telsubsys.agc.client.name}")

        files={}
        crect = 20
        dist = crect/2 + 30
        
        for ra_off, dec_off in [(0, offset), (offset, 0)]:

            #command.debug(text=f"expose cameras {exptime}")
            rc = await telsubsys.agc.expose(exptime)
            for camera in rc:
                files[camera] = [rc[camera]["filename"]]

            logger.debug(f"telescope offset {ra_off}, {dec_off}")
            await telsubsys.pwi.offset(ra_add_arcsec = ra_off, dec_add_arcsec = dec_off)

            rc = await telsubsys.pwi.status()
            #logger.debug(f"tel dist to target arcsec {rc['axis0']['dist_to_target_arcsec']}{rc['axis1']['dist_to_target_arcsec']}")

            rc = await telsubsys.agc.expose(exptime)
            for camera in rc:
                files[camera].append(rc[camera]["filename"])

            for camera in files:
                d0 = fits.open(files[camera][0])[0].data.astype(float)
                d1 = fits.open(files[camera][1])[0].data.astype(float)
                o0, o0_peak_idx = sep_objects(d0)

                for opi in o0_peak_idx:
                   s0 = o0[opi]
                   x0, y0 = int(s0['x']), int(s0['y'])
                   if x0 > dist and x0 < d0.shape[0] - dist and y0 > dist and y0 < d0.shape[1] - dist:
                      break

                c0 = centroid_quadratic(d0[y0-crect:y0+crect, x0-crect:x0+crect])
                c1 = centroid_quadratic(d1[y0-crect:y0+crect, x0-crect:x0+crect])

                delta = [c0[0]-c1[0],c0[1]-c1[1]]
                logger.debug(f"delta {camera} s:{x0}:{y0} delta:{delta}")

   
        logger.debug(f"done ")
        
    except Exception as ex:
        logger.error(ex)
        raise ex


def main():
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", '--verbose', action='store_true',
                        help="print some notes to stdout")

    parser.add_argument("-t", '--telsubsys', type=str, default="sci",
                        help="Telescope subsystem: sci, skye, skyw or spec")

    parser.add_argument("-e", '--exptime', type=float, default=5.0,
                        help="Expose for for exptime seconds")

    parser.add_argument("-o", '--offset', type=float, default=10.0,
                        help="telescope offset in arcsec float")

    args = parser.parse_args()
    
    telsubsys = lvm.execute(lvm.from_string(args.telsubsys))

    lvm.execute(calibrate(telsubsys, args.exptime, args.offset), verbose=args.verbose)

            
if __name__ == '__main__':

    main()


