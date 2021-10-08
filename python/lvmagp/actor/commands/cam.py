import click
from clu.command import Command

from lvmagp.actor.internalfunc import send_message  # noqa: F403

from . import parser


lvmcam = "lvmcam"


@parser.group()
def cam(*args):
    pass


@cam.command()
# @click.argument("CAM", type=str)
async def connect(command: Command):
    await send_message(command, lvmcam, "connect")
    return command.finish()


@cam.command()
# @click.argument("CAM", type=str)
async def disconnect(command: Command):
    await send_message(command, lvmcam, "disconnect")
    return command.finish()


@cam.command()
@click.argument("CAM", type=str)
@click.argument("EXPTIME", type=float)
@click.argument("REPEAT", type=int)
async def expose(command: Command, cam: str, exptime: float, repeat: int):
    await send_message(command, lvmcam, "expose %f %d %s" % (exptime, repeat, cam))
    return command.finish()


@cam.command()
async def status(command: Command):
    await send_message(command, lvmcam, "status")
    return command.finish()
