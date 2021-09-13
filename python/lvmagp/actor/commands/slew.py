import asyncio
import os

import click
from clu.command import Command

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
    # safety check
    tel1 = LVMTelescope(tel)

    # send slew command to lvmpwi
    zerooffsetcmd = await tel1.offset_radec(command, 0, 0)
    slewcmd = await tel1.slew_radec2000(command, target_ra_h, target_dec_d)
    command.info("Telescope slewing ...")

    await tel1.wait_for_slew(command)
    command.info("Initial slew completed.  Taking image...")

    # take an image for astrometry
    """
    exptime = 5  # in seconds
    imgcmd = await take_single_image(command, tel, exptime)
    """

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
    except:
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
        text="Compensating ...",
    )

    # Compensation
    offsetcmd = await tel1.offset_radec(command, comp_ra_arcsec, comp_dec_arcsec)

    return command.finish(text="Acquisition done")


@slew.command()
@click.argument("TEL", type=str)
@click.argument("TARGET_ALT", type=str)
@click.argument("TARGET_AZ", type=str)
async def altaz(command: Command, tel: str, target_alt: float, target_az: float):
    pass
