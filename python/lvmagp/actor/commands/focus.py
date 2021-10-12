import click
from clu.command import Command

from lvmagp.actor.internalfunc import send_message  # noqa: F403

from . import parser


lvmtan = "lvm.sci.foc"


@parser.group()
def focus(*args):
    pass


@focus.command()
@click.argument("STEPS", type=int)
async def moverel(command: Command, steps: int):
    """
    pos = await send_message(
        command, lvmtan, "getposition", returnval=True, body="Position"
    )

    reachable = await send_message(
    command, lvmtan, "isreachable %d" % (pos+steps), returnval=True, body="Reachable"
    )
    if not reachable:
        return command.fail(text="Target position is not reachable.")
    """
    movecmd = await send_message(command, lvmtan, "moverelative %d" % steps)
    if movecmd:
        return command.finish(text="Move completed.")


@focus.command()
@click.argument("POSITION", type=int)
async def moveabs(command: Command, position: int):
    """
    reachable = await send_message(
    command, lvmtan, "isreachable %d" % position, returnval=True, body="Reachable"
    )
    if not reachable:
        return command.fail(text="Target position is not reachable.")
    """
    movecmd = await send_message(command, lvmtan, "moveabsolute %d" % position)
    if movecmd:
        return command.finish(text="Move completed.")


@focus.command()
async def home(command: Command):
    ishome = await send_message(command, lvmtan, "movetohome")
    if ishome:
        return command.finish(text="Motor is at home position.")
    else:
        return command.fail(text="Commend is not complete due to unknown error.")


@focus.command()
async def status(command: Command):
    pos = await send_message(
        command, lvmtan, "getposition", returnval=True, body="Position"
    )
    vel = await send_message(
        command, lvmtan, "getvelocity", returnval=True, body="Velocity"
    )
    ismove = await send_message(
        command, lvmtan, "ismoving", returnval=True, body="Moving"
    )

    stat = {"Position": pos, "Velocity": vel, "IsMoving": ismove}

    return command.finish(STATUS=stat)


@focus.command()
async def ismoving(command: Command):
    ismove = await send_message(
        command, lvmtan, "ismoving", returnval=True, body="Moving"
    )
    return command.finish(isMoving=ismove)


@focus.command()
@click.argument("POSITION", type=int)
async def isreachable(command: Command, position: int):
    isreach = await send_message(
        command, lvmtan, "isreachable %d" % position, returnval=True, body="Reachable"
    )
    return command.finish(isReachable=isreach)
