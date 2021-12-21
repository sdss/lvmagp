import os  # this should be removed after connecting lvmcam

import click
from clu.command import Command

from lvmagp.actor.commfunc import (LVMEastCamera, LVMFibsel,  # noqa: F401
                                   LVMFocuser, LVMKMirror, LVMTANInstrument,
                                   LVMTelescope, LVMWestCamera)
from lvmagp.actor.internalfunc import GuideImage, findfocus  # noqa: F403
from lvmagp.actor.user_parameters import usrpars
from . import parser


@parser.group()
def autofocus(*args):
    pass


@autofocus.command()
@click.argument("TEL", type=str)
async def coarse(command: Command,
    telescopes: dict[str, LVMTelescope],
    eastcameras: dict[str, LVMEastCamera],
    westcameras: dict[str, LVMWestCamera],
    focusers: dict[str, LVMFocuser],
    kmirrors: dict[str, LVMKMirror],
    tel: str,):
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
async def fine(command: Command,
    telescopes: dict[str, LVMTelescope],
    eastcameras: dict[str, LVMEastCamera],
    westcameras: dict[str, LVMWestCamera],
    focusers: dict[str, LVMFocuser],
    kmirrors: dict[str, LVMKMirror],
    tel: str):
    """
    Find the optimal focus position which is near the current position.

    Parameters
    ----------
    tel
        The telescope to be focused
    """
    position, fwhm = [], []
    incremental = usrpars.af_incremental
    repeat = usrpars.af_repeat

    '''
    # For test
    pwd = os.path.dirname(os.path.abspath(__file__))
    agpwd = pwd + "/../../../../"

    guideimglist = [
        agpwd +
        "testimg/focus_series/synthetic_image_median_field_5s_seeing_02.5.fits",  # noqa: E501
        agpwd +
        "testimg/focus_series/synthetic_image_median_field_5s_seeing_03.0.fits",  # noqa: E501
        agpwd +
        "testimg/focus_series/synthetic_image_median_field_5s_seeing_04.0.fits",  # noqa: E501
        agpwd +
        "testimg/focus_series/synthetic_image_median_field_5s_seeing_05.0.fits",  # noqa: E501
        agpwd +
        "testimg/focus_series/synthetic_image_median_field_5s_seeing_06.0.fits",  # noqa: E501
    ]
    guideimgidx = [0, 1, 2, 4]
    '''
    # get current pos of focus stage
    currentposition = await focusers[tel].getposition(command)

    # Move focus
    """
    # For test
    reachablelow = await send_message(command, lvmtan, "isreachable %d" % (currentposition - (incremental * (repeat - 1)) / 2.0), returnval=True,  # noqa: E501
                                   body="Reachable")
    reachablehigh = await send_message(command, lvmtan, "isreachable %d" % (currentposition + (incremental * (repeat - 1)) / 2.0),  # noqa: E501
                                      returnval=True, body="Reachable")
    if not (reachablelow and reachablehigh):
        return command.fail(text="Target position is not reachable.")
    """
    targetposition = currentposition - (incremental * (repeat - 1)) / 2.0
    movecmd = await focusers[tel].moveabs(command, targetposition)

    if movecmd:
        currentposition = targetposition
        position.append(currentposition)
    else:
        return command.fail(text="Focus move failed")

    # Take picture
    """
    For test
    guideimg = GuideImage(guideimglist[3])  # noqa: F405
    """


    # Picture analysis
    fwhm_tmp = await get_fwhm(command,
                telescopes,
                eastcameras,
                westcameras,
                focusers,
                kmirrors,
                tel)
    fwhm.append(fwhm_tmp)

    for iteration in range(repeat - 1):
        targetposition = currentposition + incremental
        movecmd = await focusers[tel].moveabs(command, targetposition)

        if movecmd:
            currentposition = targetposition
            position.append(currentposition)
        else:
            return command.fail(text="Focus move failed")

        fwhm_tmp = await get_fwhm(command,
                telescopes,
                eastcameras,
                westcameras,
                focusers,
                kmirrors,
                tel,
                starlist=starposition)
        fwhm.append(fwhm_tmp)

    # Fitting
    bestposition, bestfocus = findfocus(position, fwhm)
    movecmd = await focusers[tel].moveabs(command, bestposition)
    return command.finish(text="Auto-focus done")


async def get_fwhm(command: Command,
    telescopes: dict[str, LVMTelescope],
    eastcameras: dict[str, LVMEastCamera],
    westcameras: dict[str, LVMWestCamera],
    focusers: dict[str, LVMFocuser],
    kmirrors: dict[str, LVMKMirror],
    tel: str,
    starlist=None):
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
    except Exception as e:
        return command.fail(fail='Camera error')

    guideimg = GuideImage(imgcmd)
    if starlist is not None:
        guideimg.guidestarposition = starlist
        guideimg.update_guidestar_properties()
    else:
        guideimg.findstars()

    return guideimg.FWHM