from clu.command import Command

from . import command_parser as parser


@parser.group()
def system(*args):
    pass


@system.command()
# @click.option("--telescope", type=bool, default=True)
async def bootup(command: Command):
    pass


async def shutdown(command: Command):
    pass
