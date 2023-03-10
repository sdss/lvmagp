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

from lvmagp.images import Image
from lvmagp.images.processors.detection import DaophotSourceDetection, SepSourceDetection
from lvmagp.focus.focusseries import PhotometryFocusSeries, ProjectionFocusSeries
from lvmtipo.focus import temp2focus

class Focus():
    def __init__(
        self, 
        telsubsys,
        offset: bool = False,
        guess: float = 42,
        source_detection = SepSourceDetection(threshold = 12.0, minarea = 24.0, deblend_nthresh = 1.4),
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
        self.fine_guess = guess
        self.radius_column = radius_column

        #TODO: should go somewhere in a subclass
        self.logger=logger
        self.logger.sh.setLevel(level)

        self._source_detection = source_detection

    async def nominal(self, temperature:float):
        try:
           return await self.telsubsys.foc.moveAbsolute(
               temp2focus(self.telsubsys.foc.actor,
                          temperature),
               'DT')

        except Exception as ex:
           self.logger.error(f"{ex}")
           raise ex

    async def position(self, position):
        try:
           self.logger.debug(f"foc move to position {position} dt")
           return await self.telsubsys.foc.moveAbsolute(position, 'DT')
        
        except Exception as ex:
           self.logger.error(ex)
           raise ex

    async def offset(self, offset):
        try:
           self.logger.debug(f"foc move relative {offset} dt")
           return await self.telsubsys.foc.moveRelative(offset, 'DT')

        except Exception as ex:
           self.logger.error(ex)
           raise ex


    async def fine(
        self,
        guess: float = 42,
        count: int = 2,
        step: float = 1.0,
        exposure_time: float = 5.0,
        source_detection = None,
        callback: Optional[Callable[..., None]] = None
    ):
        try:
            camnum = len((await self.telsubsys.agc.status()).keys())

            if not source_detection: source_detection = self._source_detection

            focus_series = [PhotometryFocusSeries(source_detection, radius_column=self.radius_column) for c in range(camnum)]

            # define array of focus values to iterate
            if self.fine_offset:
                current = self.telsubsys.foc.getPosition()
                await self.telsubsys.foc.moveRelative(count * step, 'DT')
                focus_values = np.linspace(0, 2 * count * step, 2 * count + 1)
            else:
                focus_values = np.linspace(guess - count * step, guess + count * step, 2 * count + 1)

            for foc in focus_values:
                if self.fine_offset:
                    await self.telsubsys.foc.moveRelative(foc, 'DT')
                else:
                    await self.telsubsys.foc.moveAbsolute(foc, 'DT')

                file_names = (await self.telsubsys.agc.expose(exposure_time)).flatten().unpack("*.filename")
                if isinstance(file_names, str): file_names=[file_names]
                imgs = [Image.from_file(f) for f in file_names]

                for idx, img in enumerate(imgs):
                    imgs[idx] = focus_series[idx].analyse_image(img, foc)
                    #self.logger.info(f"cam: {img.header['CAMNAME']} focus: {foc} srcs: {len(imgs[idx].catalog)}")

                if callback:
                    callback(imgs)

            if callback:
                 callback([(imgs[idx].header["CAMNAME"], fs._data) for idx, fs in enumerate(focus_series)])

            foc=[]
            for idx in range(camnum):
                try:
                    foc.append(focus_series[idx].fit_focus())
                except Exception as ex:
                    foc.append((nan,nan))

            return np.array(foc)
#            return [focus_series[idx].fit_focus() for idx in range(camnum)]

        except Exception as ex:
           self.logger.error(ex)
           raise ex



async def main():
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", '--verbose', action='store_true',
                        help="print some notes to stdout")

    parser.add_argument("-t", '--telsubsys', type=str, default="sci",
                        help="Telescope subsystem: sci, skye, skyw or spec")

    parser.add_argument("-p", '--position', type=float, default=nan,
                        help="Position focus")

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

    if args.position is not nan:
        await focus.position(args.position)

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


