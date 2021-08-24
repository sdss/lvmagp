from clu.command import Command

from lvmagp.actor.internalfunc import *  # noqa: F403

from . import parser


lvmtan = "test.first.focus_stage"


async def send_message(command, actor, command_to_send, returnval=False, body=""):
    cmd = await command.actor.send_command(actor, command_to_send)

    if cmd.status.did_fail:
        return False

    if returnval:
        return cmd.replies[-1].body[body]

    return True


@parser.group()
def autofocus(*args):
    pass


@autofocus.command()
async def coarse(command: Command):
    pass


@autofocus.command()
async def fine(command: Command):
    position, fwhm = [], []
    incremental = 100
    repeat = 5

    # For test
    guideimglist = [
        "/home/hojae/Desktop/lvmagp/testimg/focus_series/synthetic_image_median_field_5s_seeing_02.5.fits",  # noqa: E501
        "/home/hojae/Desktop/lvmagp/testimg/focus_series/synthetic_image_median_field_5s_seeing_03.0.fits",  # noqa: E501
        "/home/hojae/Desktop/lvmagp/testimg/focus_series/synthetic_image_median_field_5s_seeing_04.0.fits",  # noqa: E501
        "/home/hojae/Desktop/lvmagp/testimg/focus_series/synthetic_image_median_field_5s_seeing_05.0.fits",  # noqa: E501
        "/home/hojae/Desktop/lvmagp/testimg/focus_series/synthetic_image_median_field_5s_seeing_06.0.fits",  # noqa: E501
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
    fwhm.append(guideimg.calfwhm(findstar=True))

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
        fwhm.append(guideimg.calfwhm())

    # Fitting
    bestposition, bestfocus = findfocus(position, fwhm)  # noqa: F405
    movecmd = await send_message(command, lvmtan, "moveabsolute %d" % bestposition)
    return command.finish(text="Auto-focus done")
