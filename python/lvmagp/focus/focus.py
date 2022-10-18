# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: lvm/tel/focus.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)


import asyncio
from typing import Optional, Callable

import numpy as np
from math import nan

from lvmtipo.actors import lvm
from logging import DEBUG, INFO
from sdsstools import get_logger

#from cluplus.proxy import invoke

from lvmagp.images import Image
from lvmagp.images.processors.detection import DaophotSourceDetection, SepSourceDetection
from lvmagp.images.processors.astrometry import AstrometryDotNet
from lvmagp.focus.focusseries import PhotometryFocusSeries, ProjectionFocusSeries


class Focus():
    def __init__(
        self, 
        telsubsys, offset: bool = False,
        guess:float = 42,
        source_detection = SepSourceDetection(),
        radius_column = "fwhm",
        logger = get_logger("lvm_tel_focus"),
        level = INFO
    ):
        """Initialize a focus system.

        Args:
            telsubsys: Name of subsystem.
            offset: If True, offsets are used instead of absolute focus values.
        """
        self.telsubsys = telsubsys
        self.fine_offset = offset
        self.fine_guess = 42
        self.radius_column = radius_column

        #TODO: should go somewhere in a subclass
        self.logger=logger
        self.logger.sh.setLevel(level)

        self._source_detection = source_detection

    async def offset(self, offset):
        try:
           self.logger.debug(f"foc move to {offset} um")
           await self.telsubsys.foc.moveRelative(offset, 'UM')
        
        except Exception as ex:
           self.logger.error(ex)
           raise ex

    async def fine(
        self,
        guess: float = 44,
        count: int = 3,
        step: float = 5.0,
        exposure_time: float = 5.0,
        callback: Optional[Callable[..., None]] = None
    ):
        try:
            camnum = len((await self.telsubsys.agc.status()).keys())

            focus_series = [PhotometryFocusSeries(self._source_detection, radius_column=self.radius_column) for c in range(camnum)]


            # define array of focus values to iterate
            if self.fine_offset:
                current = self.telsubsys.foc.getPosition()
                await self.telsubsys.foc.moveRelative(count * step)
                focus_values = np.linspace(0, 2 * count * step, 2 * count + 1)
            else:
                focus_values = np.linspace(guess - count * step, guess + count * step, 2 * count + 1)

            for foc in focus_values:
                if self.fine_offset:
                    await self.telsubsys.foc.moveRelative(foc)
                else:
                    await self.telsubsys.foc.moveAbsolute(foc)

                file_names = (await self.telsubsys.agc.expose(exposure_time)).flatten().unpack("*.filename")
                imgs = [Image.from_file(f) for f in file_names]

                for idx, img in enumerate(imgs):
                    imgs[idx] = await focus_series[idx].analyse_image(img, foc)
                    self.logger.info(f"cam: {img.header['CAMNAME']} focus: {foc} srcs: {len(imgs[idx].catalog)}")

                if callback:
                    callback(imgs)

            return [focus_series[idx].fit_focus() for idx in range(camnum)]

        except Exception as ex:
           self.logger.error(ex)
           raise ex

    async def nominal(self):
        try:
           temp2focus_pos = 42 #TODO: put here a function gathering focus based on temperature.

           await self.telsubsys.foc.moveAbsolute(temp2focus_pos)
        
        except Exception as ex:
           self.logger.error(f"{ex}")
           raise ex


async def main():
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", '--verbose', action='store_true',
                        help="print some notes to stdout")

    parser.add_argument("-t", '--telsubsys', type=str, default="sci",
                        help="Telescope subsystem: sci, skye, skyw or spec")

    parser.add_argument("-o", '--offset', type=float, default=nan,
                        help="Offset focus")

    parser.add_argument("-n", '--nominal', type=float, default=nan,
                        help="Nominal focus based on temp")

    parser.add_argument("-f", '--fine', action='store_true',
                        help="Fine focus with expotime - default 10.0 sec")

    parser.add_argument("-e", '--expotime', type=float, default=10.0,
                        help="Exposure time")


    args = parser.parse_args()

    telsubsys = await lvm.from_string(args.telsubsys)
    
    focus = Focus(telsubsys, level = DEBUG if args.verbose else INFO)

    if args.offset is not nan:
        await focus.offset(args.offset)

    if args.nominal is not nan:
        await focus.nominal(args.nominal)

    if args.fine:
        await focus.fine(args.expotime)


if __name__ == '__main__':

    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())


