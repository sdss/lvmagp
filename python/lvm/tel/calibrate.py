# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: lvm/tel/calibration.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from lvm.actors import lvm, lvm_amqpc, invoke, unpack, asyncio, logger, LoggerCommand

import numpy as np

import sep
from astropy.io import fits
from photutils.centroids import centroid_com, centroid_quadratic
from photutils.centroids import centroid_1dg, centroid_2dg


# TODO: this should be somewhere in lvmtipo or a parameter actor command in lvmcam
pix_scale = 1.01       # arcsec per pixel - taken from SDSS-V_0129_LVMi_PDR.pdf Table 13

def sep_objects(data):
        bkg = sep.Background(data)
        data_sub = data - bkg
        objects = sep.extract(data_sub, 1.5, err=bkg.globalrms)
        object_index_sorted_by_peak = list({k: v for k, v in sorted({idx: objects['peak'][idx] for idx in range(len(objects))}.items(), key=lambda item: item[1], reverse=True)}.keys())
        return objects, object_index_sorted_by_peak


# ... just pick the brightest inside dist rect
def pick_one_object(data, dist, objects, objects_peak_idx):
        for i, opi in enumerate(objects_peak_idx):
            o0 = objects[opi]
            x0, y0 = int(o0['x']), int(o0['y'])
            
            if dist[0] > x0  or x0 > data.shape[0] - dist[0] or dist[1] > y0 or y0 < data.shape[1] - dist[1]:
                logger.debug(f"pick #{i} xy:{x0}:{y0}")
                return np.array([x0, y0])


async def calibrate(telsubsys, exptime, offset, command = LoggerCommand(logger)):
    try:
        logger.debug(f"calibrate {telsubsys.agc.client.name}")

        files={}
        crect = 15

        # we do expect same binning in x and y
        rc = await telsubsys.agc.binning()
        binned_img_scale = {}
        for camera in rc:
            binned_img_scale[camera] = pix_scale * rc[camera]["binning"][0]
            
        #logger.debug(f"binning {binned_img_scale}")

        
        for ra_off, dec_off in [[offset, 0], [0, offset]]:

            #command.debug(text=f"expose cameras {exptime}")
            rc = await telsubsys.agc.expose(exptime)
            for camera in rc:
                files[camera] = [rc[camera]["filename"]]

            pix_offset = np.array([round(ra_off/binned_img_scale[camera]), round(dec_off/binned_img_scale[camera])])
            dist_border = [crect/2, -crect/2] - pix_offset

            logger.debug(f"telescope offset ra:dec {ra_off}:{dec_off}")
            await telsubsys.pwi.offset(ra_add_arcsec = ra_off, dec_add_arcsec = dec_off)

            rc = await telsubsys.pwi.status()

            rc = await telsubsys.agc.expose(exptime)
            for camera in rc:
                files[camera].append(rc[camera]["filename"])

            for camera in files:
                d0 = fits.open(files[camera][0])[0].data.astype(float)
                d1 = fits.open(files[camera][1])[0].data.astype(float)
                objects, objects_peak_idx = sep_objects(d0)
                o0 = pick_one_object(d0, dist_border, objects, objects_peak_idx)
                r0 = np.array([o0-crect, o0+crect])
                r1 = r0 + pix_offset
                #logger.debug(f"object {o0}")
                #logger.debug(f"pixel offset {pix_offset}")
                #logger.debug(f"o0 rect {r0.tolist()}")
                #logger.debug(f"o1 rect {r1.tolist()}")
                #logger.debug(f"o0 {d0[r0[0][1]:r0[1][1], r0[0][0]:r0[1][0]]}")
                #logger.debug(f"o0 {d1[r0[0][1]:r0[1][1], r0[0][0]:r0[1][0]]}")
                
                c0 = centroid_quadratic(d0[r0[0][1]:r0[1][1], r0[0][0]:r0[1][0]])
                c1 = centroid_quadratic(d1[r1[0][1]:r1[1][1], r1[0][0]:r1[1][0]])

                logger.debug(f"{camera} o:{o0} delta:{c0-c1}")
   
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

    parser.add_argument("-o", '--offset', type=float, default=50.0,
                        help="telescope offset in arcsec float")

    args = parser.parse_args()
    
    telsubsys = lvm.execute(lvm.from_string(args.telsubsys))

    lvm.execute(calibrate(telsubsys, args.exptime, args.offset), verbose=args.verbose)

            
if __name__ == '__main__':

    main()


