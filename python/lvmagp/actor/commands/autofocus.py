import os  # this should be removed after connecting lvmcam

import click
from clu.command import Command

from lvmagp.actor.commfunc import *  # noqa: F403
from lvmagp.actor.internalfunc import *  # noqa: F403

from . import parser


@parser.group()
def autofocus(*args):
    pass


@autofocus.command()
@click.argument("TEL", type=str)
async def coarse(command: Command, tel: str):
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
    position, fwhm = [], []
    incremental = 100
    repeat = 5
    exptime = 3  # noqa: F841  # in seconds

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

    # get current pos of focus stage
    foc1 = LVMFocuser(tel)  # noqa: F405
    cam1 = LVMCamera(tel + "e")  # noqa: F405
    cam2 = LVMCamera(tel + "w")  # noqa: F405, F841
    cam1 = LVMCamera("test")  # noqa: F405, F841  # this is for lab test..

    currentposition = await foc1.getposition(command)

    # Move focus
    """
    reachablelow = await send_message(command, lvmtan, "isreachable %d" % (currentposition - (incremental * (repeat - 1)) / 2.0), returnval=True,  # noqa: E501
                                   body="Reachable")
    reachablehigh = await send_message(command, lvmtan, "isreachable %d" % (currentposition + (incremental * (repeat - 1)) / 2.0),  # noqa: E501
                                      returnval=True, body="Reachable")
    if not (reachablelow and reachablehigh):
        return command.fail(text="Target position is not reachable.")
    """
    targetposition = currentposition - (incremental * (repeat - 1)) / 2.0
    movecmd = await foc1.moveabs(command, targetposition)

    if movecmd:
        currentposition = targetposition
        position.append(currentposition)
    else:
        return command.fail(text="Focus move failed")

    # Take picture
    guideimg = GuideImage(guideimglist[3])  # noqa: F405
    """
    try:
        imgcmd = await cam1.single_exposure(command, tel, exptime)
    except Exception as e:
        return command.fail(fail='Camera error')
    """

    # Picture analysis
    starposition = guideimg.findstars()
    guideimg.update_guidestar_properties()
    fwhm.append(guideimg.FWHM)

    for iteration in range(repeat - 1):
        targetposition = currentposition + incremental
        movecmd = await foc1.moveabs(command, targetposition)

        if movecmd:
            currentposition = targetposition
            position.append(currentposition)
        else:
            return command.fail(text="Focus move failed")

        guideimg = GuideImage(guideimglist[guideimgidx[iteration]])  # noqa: F405
        guideimg.guidestarposition = starposition
        guideimg.update_guidestar_properties()
        fwhm.append(guideimg.FWHM)

    # Fitting
    bestposition, bestfocus = findfocus(position, fwhm)  # noqa: F405
    movecmd = await foc1.moveabs(command, bestposition)
    return command.finish(text="Auto-focus done")
