# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: lvm/tel/calibration.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from lvm.actors import lvm, lvm_amqpc, invoke, unpack, asyncio, logger, LoggerCommand

import sep
from astropy.io import fits

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
        
        for ra_off, dec_off in [(0, offset), (offset, 0)]:
            
            command.debug(text=f"expose cameras {exptime}")
            rc = await telsubsys.agc.expose(exptime)
            for camera in rc:
                files[camera] = [rc[camera]["filename"]]
    
            command.debug(text=f"telescope offset {ra_off}, {dec_off}")
            await telsubsys.pwi.offset(ra_add_arcsec = ra_off, dec_add_arcsec = dec_off)

            rc = await telsubsys.pwi.status()
            logger.debug(f"tel dist to target arcsec {rc['axis0']['dist_to_target_arcsec']}{rc['axis1']['dist_to_target_arcsec']}")

            rc = await telsubsys.agc.expose(exptime)
            for camera in rc:
                files[camera].append(rc[camera]["filename"])

            for camera in files:
                o0, o0_peak_idx = sep_objects(fits.open(files[camera][0])[0].data.astype(float))
                o1, o1_peak_idx = sep_objects(fits.open(files[camera][1])[0].data.astype(float))
                
                # pick the briqhtest - hoping that its the same star. TODO: Maybe centroiding on the first position is better.
                s0 = o0[o0_peak_idx[0]]
                s1 = o1[o1_peak_idx[0]]
                
                delta = [s0['x']-s1['x'],s0['y']-s1['y']]
                logger.debug(f"delta {camera} {delta} pos {s0['x']:2f}:{s0['y']} -> {s1['x']}:{s1['y']}")

   
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

    parser.add_argument("-o", '--offset', type=float, default=5.0,
                        help="telescope offset in arcsec float")

    args = parser.parse_args()
    
    telsubsys = lvm.execute(lvm.from_string(args.telsubsys))

    lvm.execute(calibrate(telsubsys, args.exptime, args.offset), verbose=args.verbose)

            
if __name__ == '__main__':

    main()


