import asyncio
import click
from clu.command import Command
from . import parser
from clu.client import AMQPClient

lvmpwi = "lvmpwi"


async def lvmpwi_connection_check(command):
    checkcmd = await (await command.actor.send_command(lvmpwi, "ping"))
    if checkcmd.status.did_fail:
        return False

    return True


async def send_message(command, actor, command_to_send, returnval=False, body=""):
    cmd = await command.actor.send_command(actor, command_to_send)
    cmdwait = await cmd

    if cmd.status.did_fail:
        return False

    if returnval:
        return cmd.replies[-1].body[body]

    return True


@parser.group()
def focus(*args):
    pass


@focus.command()
async def connect(command: Command):
    pwiconnection = await lvmpwi_connection_check(command)
    if not pwiconnection:
        return command.fail(text="Cannot find lvmpwi actor.")

    connected = await send_message(command, lvmpwi, "connect")
    if connected:
        return command.finish(text="Connected.")
    else:
        return command.fail(error="Error code?")


@focus.command()
async def disconnect(command: Command):
    pwiconnection = await lvmpwi_connection_check(command)
    if not pwiconnection:
        return command.fail(text="Cannot find lvmpwi actor.")

    connected = await send_message(command, lvmpwi, "disconnect")
    if connected:
        return command.finish(text="Disconnected.")
    else:
        return command.fail(error="Error code?")


@focus.command()
@click.argument("STEPS", type=int)
async def goto_ra_dec_j2000(command: Command, steps: int):
    connection = await lvmtan_connection_check(command)
    if not connection:
        return command.fail(text="Cannot find lvmtan actor.")

    moving = await send_message(
        command, "test.first.focus_stage", "ismoving", returnval=True, body="Moving"
    )

    if moving:
        return command.fail(text="Motor is moving.")

    pos = await send_message(
        command,
        "test.first.focus_stage",
        "getposition",
        returnval=True,
        body="Position",
    )
    reachable = await send_message(
        command,
        "test.first.focus_stage",
        "isreachable %d" % (pos + steps),
        returnval=True,
        body="Reachable",
    )
    if not reachable:
        return command.fail(text="Target position is not reachable.")

    movecmd = await send_message(
        command, "test.first.focus_stage", "moverelative %d" % steps
    )
    if movecmd:
        return command.finish(text="Move completed.")
