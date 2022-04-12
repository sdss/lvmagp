# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: lvm/tel/aquisition.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from lvmrop.lvm.actors import lvm, lvm_amqpc, invoke, unpack, asyncio, logger
from lvmrop.lvm.tel.focus import Focus
from lvmrop.lvm.tel.astrometry import Astrometry


async def aquisition(telsubsys, ra, dec, exptime, fine_focus=False):
    try:
        focus_temperature = 42 # get from somewhere a temperature.
        
        focus = Focus(telsubsys)

        logger.debug(f"move tel/km {ra}{dec} & temp2foc {focus_temperature}")
        await invoke(
            telsubsys.km.slewStart(ra, dec), 
            telsubsys.pwi.gotoRaDecJ2000(ra, dec),
            focus.nominal(focus_temperature)
        )

        logger.debug(f"astrometry at radec {ra}{dec}")

        ra_offset, dec_offset, refocus_offset, km_offset = await Astrometry.calc(telsubsys, ra, dec)

        logger.debug(f"correct tel/km {ra_offset, dec_offset}{km_offset} & temp2foc {focus_temperature}")

        await invoke( # there is now offsetting km
            telsubsys.pwi.offset(ra_add_arcsec = ra_offset, dec_add_arcsec = dec_offset),
            focus.offset(refocus_offset)
        )

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
    
    telsubsys = lvm.execute(lvm.from_string(args.telsubsys))

    lvm.execute(aquisition(telsubsys, args.ra, args.dec, args.exptime), verbose=args.verbose)

            
if __name__ == '__main__':

    main()


