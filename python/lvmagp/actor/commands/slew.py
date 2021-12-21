import asyncio
import os

import click
import numpy as np
from astropy import units as u
from astropy.coordinates import Angle
from clu.command import Command

from lvmagp.actor.commfunc import (LVMEastCamera, LVMFibsel,  # noqa: F401
                                   LVMFocuser, LVMKMirror, LVMTANInstrument,
                                   LVMTelescope, LVMWestCamera)
from lvmagp.actor.internalfunc import GuideImage, cal_pa, check_target
from lvmagp.actor.user_parameters import usrpars

from . import parser


@parser.command()
@click.argument("TEL", type=str)
@click.argument("TARGET_RA_H", type=float)
@click.argument("TARGET_DEC_D", type=float)
async def slew(
    command: Command,
    telescopes: dict[str, LVMTelescope],
    eastcameras: dict[str, LVMEastCamera],
    westcameras: dict[str, LVMWestCamera],
    focusers: dict[str, LVMFocuser],
    kmirrors: dict[str, LVMKMirror],
    tel: str,
    target_ra_h: float,
    target_dec_d: float,
):
    """
    Slew the telescope to the given equatorial coordinate (J2000).

    Parameters
    ----------
    tel
        Telescope to slew
    target_ra_h
        The right ascension (J2000) of the target in hours
    target_dec_d
        The declination (J2000) of the target in degrees
    """

    test_KHU = True
    long_d = telescopes[tel].longitude
    lat_d = telescopes[tel].latitude

    cmd = []

    # Check the target is in reachable area
    if not check_target(target_ra_h, target_dec_d, long_d, lat_d):
        return command.fail(fail="Target is over the limit")

    # Calculate position angle and rotate K-mirror  :: should be changed to traj method.
    target_pa_d = cal_pa(target_ra_h, target_dec_d, long_d, lat_d)
    command.info("Rotate K-mirror to pa = %.3f deg" % target_pa_d)
    cmd.append(kmirrors[tel].moveabs(command, target_pa_d, "DEG"))

    # send slew command to lvmpwi
    try:
        await telescopes[tel].reset_offset_radec(command)
        command.info("Telescope slewing ...")
        cmd.append(telescopes[tel].slew_radec2000(command, target_ra_h, target_dec_d))

    except Exception:
        return command.fail(fail="Telescope error")
    await asyncio.gather(*cmd)

    command.info("Initial slew completed.")

    for iter in range(usrpars.aqu_max_iter + 1):
        command.info("Taking image...")
        # take an image for astrometry
        try:
            imgcmd = []
            imgcmd.append(westcameras[tel].test_exposure(command, usrpars.aqu_exptime))
            # imgcmd.append(westcameras[tel].single_exposure(command, usrpars.aqu_exptime))
            if not test_KHU:
                imgcmd.append(
                    eastcameras[tel].test_exposure(command, usrpars.aqu_exptime)
                )
            guideimgpath = await asyncio.gather(*imgcmd)

        except Exception:
            return command.fail(fail="Camera error")

        command.info("Astrometry ...")

        if 0:  # Here should be changed to the camera version
            pwd = os.path.dirname(os.path.abspath(__file__))
            agpwd = pwd + "/../../../../"
            # Here lvmcam path and naming rule for finding latest guide image..

            guideimgpath = (
                agpwd +
                "testimg/focus_series/synthetic_image_median_field_5s_seeing_02.5.fits"
            )  # noqa: E501

        westguideimg = GuideImage(guideimgpath[0])
        eastguideimg = westguideimg

        if not test_KHU:
            eastguideimg = GuideImage(guideimgpath[1])

        try:
            # await guideimg.astrometry(ra_h=13, dec_d=-55)
            astcmd = []
            astcmd.append(westguideimg.astrometry(ra_h=target_ra_h, dec_d=target_dec_d))
            if not test_KHU:
                astcmd.append(
                    eastguideimg.astrometry(ra_h=target_ra_h, dec_d=target_dec_d)
                )
            cmd = await asyncio.gather(*astcmd)

        except Exception:
            return command.fail(text="Astrometry timeout")

        ra2000_d = 0.5 * (eastguideimg.ra2000 + westguideimg.ra2000)
        dec2000_d = 0.5 * (eastguideimg.dec2000 + westguideimg.dec2000)
        pa_d = 0.5 * (eastguideimg.pa + westguideimg.pa)
        westcameras[tel].rotationangle = westguideimg.pa
        eastcameras[tel].rotationangle = eastguideimg.pa

        ra2000 = Angle(ra2000_d, u.degree)
        dec2000 = Angle(dec2000_d, u.degree)

        target_ra = Angle(target_ra_h, u.hour)
        target_dec = Angle(target_dec_d, u.degree)

        comp_ra_arcsec = (target_ra - ra2000).s
        comp_dec_arcsec = (target_dec - dec2000).s

        command.info(
            Img_ra2000=ra2000.to_string(unit=u.hour),
            Img_dec2000=dec2000.to_string(unit=u.degree),
            Img_pa="%.3f deg" % pa_d,
            offset_ra="%.3f arcsec" % comp_ra_arcsec,
            offset_dec="%.3f arcsec" % comp_dec_arcsec,
        )

        # Compensation  // Compensation for K-mirror based on astrometry result?
        # may be by offset method..

        if (
            np.sqrt(comp_ra_arcsec ** 2 + comp_dec_arcsec ** 2) >
            usrpars.aqu_tolerance_arcsec
        ):
            if iter >= usrpars.aqu_max_iter:
                return command.fail(fail="Compensation failed.")
            else:
                command.info(text="Compensating ...")
                cmd = []
                if not test_KHU:
                    cmd.append(kmirrors[tel].moverel(command, -pa_d, "DEG"))
                cmd.append(
                    telescopes[tel].offset_radec(
                        command, comp_ra_arcsec, comp_dec_arcsec
                    )
                )
                await asyncio.gather(*cmd)

        else:
            break

    return command.finish(text="Acquisition done")
