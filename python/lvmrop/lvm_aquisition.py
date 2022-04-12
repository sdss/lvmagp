# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: lvm_aquisition.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from lvmrop.lvm_actors import lvm, lvm_amqpc, invoke, unpack, asyncio, logger
from lvmrop.lvm_focus import Focus
from lvmrop.lvm_astrometry import Astrometry


async def aquisition(telsubsys, ra, dec, exptime, fine_focus=False):
    try:
        logger.debug(f"moving to {ra}:{dec}")
        focus_temperature = 42 # get from somewhere a temperature.
        
        await invoke(
            telsubsys.km.slewStart(ra, dec), 
            telsubsys.pwi.gotoRaDecJ2000(ra, dec),
            Focus.nominal(telsubsys, focus_temperature)
        )

        await Astrometry.calc(telsubsys)


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

    parser.add_argument("-r", '--ra', help="RA J2000 in hours")

    parser.add_argument("-d", '--dec', help="DEC J2000 in degrees")

    args = parser.parse_args()
    
    telsubsys = lvm.from_string(args.telsubsys)

    lvm.execute(aquisition, telsubsys, args.ra, args.dec, args.exptime, verbose=args.verbose)

            
if __name__ == '__main__':

    main()


