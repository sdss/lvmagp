# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: lvm/tel/focus.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from lvm.actors import lvm, lvm_amqpc, invoke, unpack, asyncio, logger

from math import nan

import json

class Focus:
    def __init__(self, telsubsys):
        self.telsubsys = telsubsys

    async def offset(self, offset):
        try:
           await self.telsubsys.foc.moveRelative(offset)
        
        except Exception as ex:
           logger.error(ex)
           raise ex

    async def nominal(self, temp):
        try:
           temp2focuspos = temp # put here a function gathering focus based on temperature.
           await self.telsubsys.foc.moveAbsolute(temp)
        
        except Exception as ex:
           logger.error(ex)
           raise ex


    async def fine(self, exptime=1):
        try:
            east="east"
            west="west"
            files={east:[], west:[]}
            for p in [400, 200, 100, 0]: # implement something making sense.
                
                logger.debug(f"foc move to {p}")
                await self.telsubsys.foc.moveAbsolute(p)
                
                logger.debug(f"expose 1")
                rc = await self.telsubsys.agc.expose(exptime)
                files[east].append(rc[east]["filename"])
                files[west].append(rc[west]["filename"])
                
            logger.debug(f"Files used: {json.dumps(files, sort_keys=True, indent=2)}")

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

    parser.add_argument("-o", '--offset', type=float, default=nan,
                        help="Offset focus")

    parser.add_argument("-n", '--nominal', type=float, default=nan,
                        help="Nominal focus based on temp")

    parser.add_argument("-f", '--fine', action='store_true',
                        help="Fine focus with expotime - default 1.0 sec")

    parser.add_argument("-e", '--expotime', type=float, default=1.0,
                        help="Exposure time")


    args = parser.parse_args()
    
    telsubsys = lvm.execute(lvm.from_string(args.telsubsys))
    
    focus = Focus(telsubsys)

    if args.offset is not nan:
        lvm.execute(focus.offset(args.offset), verbose=args.verbose)

    if args.nominal is not nan:
        lvm.execute(focus.nominal(args.nominal), verbose=args.verbose)

    if args.fine:
        lvm.execute(focus.fine(args.expotime), verbose=args.verbose)

if __name__ == '__main__':

    main()


