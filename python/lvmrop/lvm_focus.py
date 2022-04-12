# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: lvm_focus.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from lvmrop.lvm_actors import lvm, lvm_amqpc, invoke, unpack, asyncio, logger

from math import nan

class Focus:
    @staticmethod
    async def nominal(telsubsys, temp):
        try:
           temp2focuspos = temp # put here a function gathering focus based on temperature.
           await telsubsys.foc.moveAbsolute(temp)
        
        except Exception as ex:
           logger.error(ex)
           raise ex

    @staticmethod
    async def fine(telsubsys):
        try:
            east="east"
            west="west"
            files={east:[], west:[]}
            for p in [400, 200, 100, 0]: # implement something making sense.
                logger.debug(f"foc move to {p}")
                await telsubsys.foc.moveAbsolute(p)
                logger.debug(f"expose 1")
                rc = await telsubsys.agc.expose(1)
                files[east].append(rc[east]["filename"])
                files[west].append(rc[west]["filename"])
                
            logger.debug(str(files))

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

    parser.add_argument("-n", '--nominal', type=float, default=nan,
                        help="Nominal focus based on temp")

    parser.add_argument("-f", '--fine', action='store_true',
                        help="Fine focus")


    args = parser.parse_args()
    
    telsubsys = lvm.from_string(args.telsubsys)

    if args.nominal is not nan:
        lvm.execute(Focus.nominal, telsubsys, args.nominal, verbose=args.verbose)

    if args.fine:
        lvm.execute(Focus.fine, telsubsys, verbose=args.verbose)

if __name__ == '__main__':

    main()


