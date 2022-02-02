import click
from clu.command import Command

from lvmagp.actor.commfunc import LVMTelescopeUnit

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
    telunit = LVMTelescopeUnit(tel)
    telunit.fine_autofocus()
    del telunit

    return command.finish(text="Auto-focus done")
