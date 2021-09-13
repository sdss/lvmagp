import asyncio
import os

import click
from clu.command import Command

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

    # send slew command to lvmpwi
    if tel == "test":
        lvmpwi = "lvm.pwi"
        lvmtan = "test.first.focus_stage"
    else:
        lvmpwi = "lvm." + tel + ".pwi"
        lvmtan = "lvm." + tel + ".foc"

    raoffsetcmd = await send_message(command, lvmpwi, "offset --ra_reset 0")
    decoffsetcmd = await send_message(command, lvmpwi, "offset --dec_reset 0")

    slewcmd = await send_message(
        command, lvmpwi, "goto-ra-dec-j2000 %f %f" % (target_ra_h, target_dec_d)
    )
    command.info("Telescope slewing ...")

    while 1:
        isslew = await send_message(
            command, lvmpwi, "status", returnval=True, body="is_slewing"
        )
        if isslew:  ##one-way comm. of PWI4: warning.
            await asyncio.sleep(0.5)
        else:
            break

    command.info("Initial slew completed.  Taking image...")

    # take an image for astrometry
    """
    imgcmd = await send_message(command, lvmcam, "goto_ra_dec_j2000 %f %f"%(target_ra_h, target_dec_d))
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
    comp_ra_sec = (target_ra_h * 15 - guideimg.ra2000) * 3600
    comp_dec_sec = (target_dec_d - guideimg.dec2000) * 3600

    command.info(
        Img_ra2000="%02dh %02dm %06.3fs"
        % (ra2000_hms[0], ra2000_hms[1], ra2000_hms[2]),
        Img_dec2000="%02dd %02dm %06.3fs"
        % (dec2000_dms[0], dec2000_dms[1], dec2000_dms[2]),
        Img_pa="%.3f deg" % guideimg.pa,
        offset_ra="%.3f arcsec" % comp_ra_sec,
        offset_dec="%.3f arcsec" % comp_dec_sec,
        text="Compensating ...",
    )

    # Compensation
    raoffsetcmd = await send_message(
        command, lvmpwi, "offset --ra_add_arcsec %f" % comp_ra_sec
    )
    decoffsetcmd = await send_message(
        command, lvmpwi, "offset --dec_add_arcsec %f" % comp_dec_sec
    )

    await asyncio.sleep(0.5)  # settle time

    return command.finish(text="Acquisition done")


@slew.command()
@click.argument("TEL", type=str)
@click.argument("TARGET_ALT", type=str)
@click.argument("TARGET_AZ", type=str)
async def altaz(command: Command, tel: str, target_alt: float, target_az: float):
    pass
