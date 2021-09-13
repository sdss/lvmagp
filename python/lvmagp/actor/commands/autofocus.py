import os  # this should be removed after connecting lvmcam

import click
from clu.command import Command

from lvmagp.actor.internalfunc import *  # noqa: F403

from . import parser


@parser.group()
def autofocus(*args):
    pass


@autofocus.command()
@click.argument("FOCUSER", type=str)
async def coarse(command: Command, focuser: str):
    pass


@autofocus.command()
@click.argument("FOCUSER", type=str)
async def fine(command: Command, focuser: str):
    position, fwhm = [], []
    incremental = 100
    repeat = 5
    if focuser == "test":
        lvmtan = "test.first.focus_stage"
    else:
        lvmtan = "lvm." + focuser + ".foc"

    # For test
    pwd = os.path.dirname(os.path.abspath(__file__))
    agpwd = pwd + "/../../../../"

    guideimglist = [
        agpwd + "testimg/focus_series/synthetic_image_median_field_5s_seeing_02.5.fits",  # noqa: E501
        agpwd + "testimg/focus_series/synthetic_image_median_field_5s_seeing_03.0.fits",  # noqa: E501
        agpwd + "testimg/focus_series/synthetic_image_median_field_5s_seeing_04.0.fits",  # noqa: E501
        agpwd + "testimg/focus_series/synthetic_image_median_field_5s_seeing_05.0.fits",  # noqa: E501
        agpwd + "testimg/focus_series/synthetic_image_median_field_5s_seeing_06.0.fits",  # noqa: E501
    ]
    guideimgidx = [0, 1, 2, 4]

    # get current pos of focus stage
    currentposition = await send_message(
        command, lvmtan, "getposition", returnval=True, body="Position"
    )

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
    movecmd = await send_message(command, lvmtan, "moveabsolute %d" % targetposition)
    if movecmd:
        currentposition = targetposition
        position.append(currentposition)
    else:
        return command.fail(text="Focus move failed")

    # Take picture
    guideimg = GuideImage(guideimglist[3])  # noqa: F405
    """
    send_messange(Command, lvmcam, )
    """

    # Picture anaysis
    starposition = guideimg.findstars()
    fwhm.append(guideimg.calfwhm())

    for iteration in range(repeat - 1):
        targetposition = currentposition + incremental
        movecmd = await send_message(
            command, lvmtan, "moveabsolute %d" % targetposition
        )
        if movecmd:
            currentposition = targetposition
            position.append(currentposition)
        else:
            return command.fail(text="Focus move failed")

        guideimg = GuideImage(guideimglist[guideimgidx[iteration]])  # noqa: F405
        guideimg.guidestarposition = starposition
        fwhm.append(guideimg.calfwhm())

    # Fitting
    bestposition, bestfocus = findfocus(position, fwhm)  # noqa: F405
    movecmd = await send_message(command, lvmtan, "moveabsolute %d" % bestposition)
    return command.finish(text="Auto-focus done")
