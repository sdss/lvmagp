
import asyncio
import click
from clu.command import Command
from . import parser
from clu.client import AMQPClient

async def lvmtan_connection_check(command):
    checkcmd = await (await command.actor.send_command("test.first.focus_stage", "ping"))
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
@click.argument("STEPS", type=int)
async def moverel(command: Command, steps: int):
    connection = await lvmtan_connection_check(command)
    if not connection:
        return command.fail(text="Cannot find lvmtan actor.")

    ismove = await send_message(command, "test.first.focus_stage", "ismoving", returnval=True, body="Moving")

    if ismove == True:
        return command.fail(text="Motor is moving.")

    movecmd = await send_message(command, "test.first.focus_stage", "moverelative %d" % steps)
    if movecmd:
        return command.finish(text="Move completed.")

@focus.command()
@click.argument("POSITION", type=int)
async def moveabs(command: Command, position: int):
    connection = await lvmtan_connection_check(command)
    if not connection:
        return command.fail(text="Cannot find lvmtan actor.")

    ismove = await send_message(command, "test.first.focus_stage", "ismoving", returnval=True, body="Moving")

    if ismove == True:
        return command.fail(text="Motor is moving.")

    movecmd = await send_message(command, "test.first.focus_stage", "moveabsolute %d" % position)
    if movecmd:
        return command.finish(text="Move completed.")

@focus.command()
async def home(command: Command):
    connection = await lvmtan_connection_check(command)
    if not connection:
        return command.fail(text="Cannot find lvmtan actor.")

    ishome = await send_message(command, "test.first.focus_stage", "movetohome")
    if ishome:
        return command.finish(text="Motor is at home position.")
    else:
        return command.fail(text="Commend is not complete due to unknown error.")

@focus.command()
async def status(command: Command):
    connection = await lvmtan_connection_check(command)
    if not connection:
        return command.fail(text="Cannot find lvmtan actor.")

    pos = await send_message(command, "test.first.focus_stage", "getposition", returnval=True, body="Position")
    vel = await send_message(command, "test.first.focus_stage", "getvelocity", returnval=True, body="Velocity")
    ismove = await send_message(command, "test.first.focus_stage", "ismoving", returnval=True, body="Moving")

    stat = {"Position" : pos, "Velocity" : vel, "IsMoving" : ismove}

    return command.finish(STATUS=stat)

@focus.command()
async def ismoving(command: Command):
    connection = await lvmtan_connection_check(command)
    if not connection:
        return command.fail(text="Cannot find lvmtan actor.")

    ismove = await send_message(command, "test.first.focus_stage", "ismoving", returnval=True, body="Moving")

    return command.finish(isMoving=ismove)