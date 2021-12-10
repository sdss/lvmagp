from clu.command import Command

from lvmagp.actor.commfunc import (  # noqa: F401
    LVMEastCamera,
    LVMFibsel,
    LVMFocuser,
    LVMKMirror,
    LVMTANInstrument,
    LVMTelescope,
    LVMWestCamera,
)
from lvmagp.actor.internalfunc import GuideImage
from lvmagp.actor.user_parameters import usrpars   # noqa: F401

from . import parser

# import logging
# from sdsstools import get_logger


test_KHU = True

# log = get_logger("sdss-lvmagp")
# log.sh.setLevel(logging.DEBUG)


@parser.command()
# @click.argument("TEL", type=str)
async def test(
    command: Command,
    telescopes: dict[str, LVMTelescope],
    eastcameras: dict[str, LVMEastCamera],
    westcameras: dict[str, LVMWestCamera],
    focusers: dict[str, LVMFocuser],
    kmirrors: dict[str, LVMKMirror],
):

    filepath = \
        "/home/sumin/lvmcam/python/lvmcam/assets/lvm/sci/agw/20211203/lvm.sci.agw-00000107.fits"
    guideimg1 = GuideImage(filepath)

    filepath = \
        "/home/sumin/lvmcam/python/lvmcam/assets/lvm/sci/agw/20211203/lvm.sci.agw-00000110.fits"
    guideimg2 = GuideImage(filepath)
    pos = guideimg1.findstars()
    print(pos)

    guideimg2.guidestarposition = pos
    guideimg2.update_guidestar_properties()
    starposition = guideimg2.guidestarposition
    print(starposition)
