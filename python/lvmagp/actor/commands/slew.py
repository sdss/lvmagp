import os
import click
from clu.command import Command

from lvmagp.actor.commfunc import *  # noqa: F403
from lvmagp.actor.internalfunc import *  # noqa: F403
from lvmagp.actor.user_parameters import usrpars

from . import parser


async def deg_to_dms(deg):
    absdeg = np.abs(deg)
    d = np.floor(absdeg)
    m = np.floor((absdeg - d) * 60)
    s = (absdeg - d - m / 60) * 3600
    if deg < 0:
        d = -d
    return (d, m, s)


@parser.command()
@click.argument("TEL", type=str)
@click.argument("TARGET_RA_H", type=float)
@click.argument("TARGET_DEC_D", type=float)
async def slew(command: Command,
               telescopes: dict[str, LVMTelescope], eastcameras: dict[str, LVMEastCamera], westcameras: dict[str, LVMWestCamera],
               focusers: dict[str, LVMFocuser], kmirrors: dict[str, LVMKMirror],
               tel: str, target_ra_h: float, target_dec_d: float):

    test_KHU = True
    long_d = telescopes[tel].longitude
    lat_d = telescopes[tel].latitude

    max_iter = 1

    cmd = []

    # Check the target is in reachable area
    if not check_target(target_ra_h, target_dec_d, long_d, lat_d):
        return command.fail(fail="Target is over the limit")

    # Calculate position angle and rotate K-mirror  :: should be changed to traj method.
    target_pa_d = cal_pa(target_ra_h, target_dec_d, long_d, lat_d)
    command.info("Rotate K-mirror to pa = %.3f deg" % target_pa_d)

    try:
        cmd.append(kmirrors[tel].moveabs(command, target_pa_d, "DEG"))
    except Exception as e:
        return command.fail(fail="Kmirror error")

    # send slew command to lvmpwi
    try:
        await telescopes[tel].offset_radec(command, 0, 0)
        command.info("Telescope slewing ...")
        cmd.append(telescopes[tel].slew_radec2000(command, target_ra_h, target_dec_d))

    except Exception as e:
        return command.fail(fail="Telescope error")
    await asyncio.gather(*cmd)

    command.info("Initial slew completed.")

    for iter in range(usrpars.aqu_max_iter + 1):
        command.info("Taking image...")
        # take an image for astrometry
        try:
            imgcmd = []
            imgcmd.append(westcameras[tel].single_exposure(command, usrpars.aqu_exptime))
            if test_KHU is not True:
                imgcmd.append(eastcameras[tel].single_exposure(command, usrpars.aqu_exptime))
            guideimgpath = await asyncio.gather(*imgcmd)

        except Exception as e:
            return command.fail(fail="Camera error")

        command.info("Astrometry ...")

        if 0:  #Here should be changed to the camera version
            pwd = os.path.dirname(os.path.abspath(__file__))
            agpwd = pwd + "/../../../../"
            # Here lvmcam path and naming rule for finding latest guide image..

            guideimgpath = (
                agpwd + "testimg/focus_series/synthetic_image_median_field_5s_seeing_02.5.fits"
            )  # noqa: E501

        westguideimg = GuideImage(guideimgpath[0])
        eastguideimg = westguideimg

        if test_KHU is not True:
            eastguideimg = GuideImage(guideimgpath[1])

        try:
            # await guideimg.astrometry(ra_h=13, dec_d=-55)

            astcmd = []
            astcmd.append(westguideimg.astrometry(ra_h=target_ra_h, dec_d=target_dec_d))
            if test_KHU is not True:
                astcmd.append(eastguideimg.astrometry(ra_h=target_ra_h, dec_d=target_dec_d))
            await asyncio.gather(*astcmd)

        except Exception as e:
            return command.fail(text="Astrometry timeout")


        ra2000_d = 0.5*(eastguideimg.ra2000 + westguideimg.dec2000)
        dec2000_d = 0.5*(eastguideimg.dec2000 + westguideimg.dec2000)
        pa_d = 0.5*(eastguideimg.pa + westguideimg.pa)

        ra2000_hms = await deg_to_dms(ra2000_d / 15)
        dec2000_dms = await deg_to_dms(dec2000_d)

        comp_ra_arcsec = (target_ra_h * 15 - ra2000_d) * 3600
        comp_dec_arcsec = (target_dec_d - dec2000_d) * 3600

        command.info(
            Img_ra2000="%02dh %02dm %06.3fs"
            % (ra2000_hms[0], ra2000_hms[1], ra2000_hms[2]),
            Img_dec2000="%02dd %02dm %06.3fs"
            % (dec2000_dms[0], dec2000_dms[1], dec2000_dms[2]),
            Img_pa="%.3f deg" % pa_d,
            offset_ra="%.3f arcsec" % comp_ra_arcsec,
            offset_dec="%.3f arcsec" % comp_dec_arcsec,
        )

        # Compensation  // Compensation for K-mirror based on astrometry result?  may be by offset method..
        if iter >= max_iter:
            return command.fail(fail="Compensation failed.")

        if (np.sqrt(comp_ra_arcsec**2+comp_dec_arcsec**2) > usrpars.aqu_tolerance_arcsec):
            command.info(text="Compensating ...")
            cmd = []
            cmd.append(kmirrors[tel].moverel(command, -pa_d, "DEG"))
            cmd.append(telescopes[tel].offset_radec(command, comp_ra_arcsec, comp_dec_arcsec))
            await asyncio.gather(*cmd)

        else:
            break

    return command.finish(text="Acquisition done")