# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: lvm/tel/focus.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from lvmtipo.actors import lvm
from logging import DEBUG, INFO
from sdsstools import get_logger

from math import nan
from astropy.io import fits


class Focus():
    def __init__(self, telsubsys, logger = get_logger("lvm_tel_focus"), level = INFO):
        self.telsubsys = telsubsys
        
        #TODO: should go somewhere in a subclass
        self.logger=logger
        self.logger.sh.setLevel(level)
        
    async def offset(self, offset):
        try:
           self.logger.debug(f"foc move to {offset} um")
           await self.telsubsys.foc.moveRelative(offset, 'UM')
        
        except Exception as ex:
           self.logger.error(ex)
           raise ex

    async def fine(self, exptime):
        try:
            files = {}
            for p in [400, 200, 100, 0, -100]: #TODO: implement some focusing that makes sense.
                
                self.logger.debug(f"foc move to {p}")
                await self.telsubsys.foc.moveAbsolute(p)
                
                self.logger.debug(f"expose {exptime}")
                rc = await self.telsubsys.agc.expose(exptime)
                for camera in rc:
                    if files.get(camera, None):
                       files[camera].append(rc[camera]["filename"])
                    else:
                       files[camera] = [rc[camera]["filename"]]

            self.logger.info(f"{files}")

        except Exception as ex:
           self.logger.error(ex)
           raise ex

    async def nominal(self):
        try:
           temp2focus_pos = 42 #TODO: put here a function gathering focus based on temperature.

           await self.telsubsys.foc.moveAbsolute(temp2focus_pos)
        
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


