# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: lvm/tel/calibration.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from lvm.actors import lvm, lvm_amqpc, invoke, unpack, asyncio, logger
from lvm.command import LoggerCommand


import numpy as np
from math import cos

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


# ... just picking the brightest inside border rect
def pick_one_object(data, border, objects, objects_peak_idx):
        for i, opi in enumerate(objects_peak_idx):
            o0 = objects[opi]
            x0, y0 = o0['x'], o0['y']
            
            if border > x0  or x0 > data.shape[0] - border or border > y0 or y0 > data.shape[1] - border:
                continue
            
#            logger.debug(f"pick #{i} xy:{x0}:{y0}")
            return np.array([x0, y0])


async def calibrate(telsubsys, exptime, offset, axis_error, command = LoggerCommand(logger)):
    try:
        logger.debug(f"calibrate {telsubsys.agc.client.name}")

        files={}
        center_rect = 8

        # we do expect same binning in x and y
        rc = await telsubsys.agc.binning()
        binned_img_scale = {}
        for camera in rc:
            binned_img_scale[camera] = pix_scale * rc[camera]["binning"][0]
            
        for ra_off_h, dec_off_d in [[offset, 0], [0, offset]]:

            rc = await telsubsys.agc.expose(exptime)
            for camera in rc:
                files[camera] = [rc[camera]["filename"]]

            pix_offset = np.array([round(ra_off_h / binned_img_scale[camera]), round(dec_off_d / binned_img_scale[camera])])
            border = center_rect/2 + max(map(abs,pix_offset))
            logger.info(f"telescope offset ra:dec {ra_off_h}:{dec_off_d} pixoff/border {pix_offset}/{border}")
            await telsubsys.pwi.offset(ra_add_arcsec = ra_off_h, dec_add_arcsec = dec_off_d, axis_error=axis_error)

            rc = await telsubsys.pwi.status()

            rc = await telsubsys.agc.expose(exptime)
            for camera in rc:
                files[camera].append(rc[camera]["filename"])

            for camera in files:
                d0 = fits.open(files[camera][0])[0].data.astype(float)
                d1 = fits.open(files[camera][1])[0].data.astype(float)
#                logger.debug(f"o0/1 file {files[camera][0]} {files[camera][1]}")
                
                objects, objects_peak_idx = sep_objects(d0)
                o0 = pick_one_object(d0, border, objects, objects_peak_idx)
                o1 = [o0[0] - pix_offset[0], o0[1] - pix_offset[1]]
                
                c0 = centroid_quadratic(d0, xpeak=o0[0], ypeak=o0[1], search_boxsize=center_rect)
                c1 = centroid_quadratic(d1, xpeak=o1[0], ypeak=o1[1], search_boxsize=center_rect)

                logger.debug(f"{camera} o:{o0} delta:{c0-c1}")
#                logger.debug(f"{camera} o:{c1} {o1}")
   
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

    parser.add_argument("-a", '--axis_error', type=float, default=0.4,
                        help="telescope axis_error for offset commands")

    args = parser.parse_args()
    
    telsubsys = lvm.execute(lvm.from_string(args.telsubsys))

    lvm.execute(calibrate(telsubsys, args.exptime, args.offset, args.axis_error), verbose=args.verbose)

            
if __name__ == '__main__':

    main()


