import click
from clu.command import Command

from lvmagp.actor.commfunc import (
    LVMEastCamera,
    LVMFibselector,  # noqa: F401
    LVMFocuser,
    LVMKMirror,
    LVMTelescope,
    LVMTelescopeUnit,
    LVMWestCamera,
)
from lvmagp.actor.internalfunc import GuideImage
from lvmagp.actor.user_parameters import usrpars

from . import command_parser as parser


@parser.group()
def autofocus(*args):
    pass


@autofocus.command()
@click.argument("TEL", type=str)
async def coarse(
    command: Command,
    telescopes: dict[str, LVMTelescope],
    eastcameras: dict[str, LVMEastCamera],
    westcameras: dict[str, LVMWestCamera],
    focusers: dict[str, LVMFocuser],
    kmirrors: dict[str, LVMKMirror],
    tel: str,
):
    """
    Find the focus coarsely by scanning whole reachable position.

    Parameters
    ----------
    tel
        The telescope to be focused
    """
    pass


@autofocus.command()
@click.argument("TEL", type=str)
async def fine(command: Command, tel: str):
    """
    Find the optimal focus position which is near the current position.

    Parameters
    ----------
    tel
        The telescope to be focused
    """
    telunit = LVMTelescopeUnit(tel)
    telunit.fine_autofocus()
    del telunit

    return command.finish(text="Auto-focus done")


async def get_fwhm(
    command: Command,
    telescopes: dict[str, LVMTelescope],
    eastcameras: dict[str, LVMEastCamera],
    westcameras: dict[str, LVMWestCamera],
    focusers: dict[str, LVMFocuser],
    kmirrors: dict[str, LVMKMirror],
    tel: str,
    starlist=None,
):
    """
    Take a testshot and return FWHM of the image.

    Parameters
    ----------
    tel
        The telescope to be focused
    starlist
        List of stars whose FWHMs will be measured
        If ''starlist`` is None, this function finds star in the testshot.
    """
    exptime = usrpars.af_exptime

    try:
        imgcmd = await westcameras[tel].test_exposure(command, exptime)
    except Exception:
        return command.fail(fail="Camera error")

    guideimg = GuideImage(imgcmd)
    if starlist is not None:
        guideimg.guidestarposition = starlist
        guideimg.update_guidestar_properties()
    else:
        guideimg.findstars()

    return guideimg.FWHM
