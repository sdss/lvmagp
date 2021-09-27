import asyncio
import os

import click
from clu.command import Command
from clu import AMQPClient, CommandStatus
from lvmagp.actor.commfunc import *  # noqa: F403
from lvmagp.actor.internalfunc import *  # noqa: F403

from . import parser


async def deg_to_dms(deg):
    absdeg = np.abs(deg)
    d = np.floor(absdeg)
    m = np.floor((absdeg - d) * 60)
    s = (absdeg - d - m / 60) * 3600
    if deg < 0:
        d = -d
    return (d, m, s)


@parser.group()
def slew(*args):
    pass

@slew.command()
@click.argument("TEL", type=str)
@click.argument("TARGET_RA_H", type=float)
@click.argument("TARGET_DEC_D", type=float)
async def radec(command: Command, tel: str, target_ra_h: float, target_dec_d: float):
    lat_d = 38.0
    long_d = 127.0

    exptime = 3  # in seconds
    tol_ra_arcsec = 30
    tol_dec_arcdec = 30
    max_iter = 1

    # safety check?
    tel1 = LVMTelescope(tel)
    cam1 = LVMCamera(tel+'e')
    cam2 = LVMCamera(tel+'w')
    km1 = LVMKMirror(tel)
    cam1 = LVMCamera('test')  # for lab testing

    # Calculate position angle and rotate K-mirror
    pa = cal_pa(target_ra_h, target_dec_d, lat_d, long_d)
    command.info("Rotate K-mirror to pa = %.3f deg"%pa)
    try:
        kmtask = km1.moveabs(command, pa, 'DEG')
    except Exception as e:
        return command.fail(fail="Kmirror error")

    # send slew command to lvmpwi
    try:
        zerooffsetcmd = await tel1.offset_radec(command, 0, 0)
        command.info("Telescope slewing ...")

        slewtask = await tel1.slew_radec2000(command, target_ra_h, target_dec_d)

    except Exception as e:
        return command.fail(fail='Telescope error')

    await kmtask
    await slewtask
    command.info("Initial slew completed.")

    for iter in range(max_iter+1):
        command.info("Taking image...")
        # take an image for astrometry
        try:
            imgcmd = await cam1.single_exposure(command, exptime)
        except Exception as e:
            return command.fail(fail='Camera error')

        command.info("Astrometry ...")

        pwd = os.path.dirname(os.path.abspath(__file__))
        agpwd = pwd + "/../../../../"

        guideimgpath = (
            agpwd + "testimg/focus_series/synthetic_image_median_field_5s_seeing_02.5.fits"
        )  # noqa: E501
        guideimg = GuideImage(guideimgpath)  # noqa: F405

        try:
            await guideimg.astrometry(ra_h=target_ra_h, dec_d=target_dec_d)
            # await guideimg.astrometry(ra_h=13, dec_d=-55)
        except Exception as e:
            return command.fail(text="Astrometry timeout")

        ra2000_hms = await deg_to_dms(guideimg.ra2000 / 15)
        dec2000_dms = await deg_to_dms(guideimg.dec2000)
        comp_ra_arcsec = (target_ra_h * 15 - guideimg.ra2000) * 3600
        comp_dec_arcsec = (target_dec_d - guideimg.dec2000) * 3600

        command.info(
            Img_ra2000="%02dh %02dm %06.3fs"
            % (ra2000_hms[0], ra2000_hms[1], ra2000_hms[2]),
            Img_dec2000="%02dd %02dm %06.3fs"
            % (dec2000_dms[0], dec2000_dms[1], dec2000_dms[2]),
            Img_pa="%.3f deg" % guideimg.pa,
            offset_ra="%.3f arcsec" % comp_ra_arcsec,
            offset_dec="%.3f arcsec" % comp_dec_arcsec,
        )

        # Compensation
        if iter >= max_iter:
            return command.fail(fail="Compensation failed.")

        if (np.abs(comp_ra_arcsec)>tol_ra_arcsec) & (np.abs(comp_dec_arcsec)>tol_dec_arcdec):
            command.info(text="Compensating ...")
            #kmtask = km1.moveabs(command, pa, 'deg')
            kmtask_comp = km1.moverel(command, -guideimg.pa, 'DEG')
            await tel1.offset_radec(command, comp_ra_arcsec, comp_dec_arcsec)
            await kmtask_comp

        else:
            break

    return command.finish(text="Acquisition done")


@slew.command()
@click.argument("TEL", type=str)
@click.argument("TARGET_ALT", type=str)
@click.argument("TARGET_AZ", type=str)
async def altaz(command: Command, tel: str, target_alt_d: float, target_az_d: float):
    # safety check?
    tel1 = LVMTelescope(tel)
    cam1 = LVMCamera(tel + 'e')
    cam2 = LVMCamera(tel + 'w')
    if tel == 'test':
        cam1 = LVMCamera('test')

    # send slew command to lvmpwi
    try:
        zerooffsetcmd = await tel1.offset_radec(command, 0, 0)
        command.info("Telescope slewing ...")

        slewcmd = await tel1.slew_radec2000(command, target_alt_d, target_az_d)
        command.info("Initial slew completed.")

    except Exception as e:
        return command.fail(fail='Telescope error')

    return command.finish(text="Acquisition done")

@slew.command()
async def test(command: Command):
    pa = cal_pa(10.0,10.0,37.0,127.0)
    return command.finish(text=str(pa))