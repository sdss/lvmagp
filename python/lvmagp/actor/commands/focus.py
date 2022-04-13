import asyncio

import click
import numpy as np
from clu.command import Command

from . import parser

from lvmagp.actor.state import ActorState
from lvm.tel.focus import Focus
from lvmagp import exceptions


@parser.command("focusOffset")
@click.argument("offset", type=float)
async def focusOffset(
    command: Command,
    telsubsystems,
    offset: float,
):
    """Focus offest"""
    try:
        actor_state = command.actor.state
        focus = command.actor.focus

        await focus.offset(offset, command=command)
         
    except Exception as e:
        return command.fail(error=e)

    return command.finish(state = actor_state.state)


@parser.command("focusFine")
@click.argument("EXPOTIME", type=float, default=1.0)
async def focusFine(
    command: Command,
    telsubsystems,
    expotime: float,
):
    """Focus fine"""
    try:
        logger = command.actor.log
        actor_state = command.actor.state
        focus = command.actor.focus

        if not actor_state.isIdle():
            return command.fail(error = LvmagpIsNotIdle(), state = actor_state.state)

        actor_state.state = "FOCUSING"
        command.info(state = actor_state.state)
        
        logger.debug(f"start focusing {actor_state.state} {await telsubsystems.foc.status()}")
        await focus.fine(expotime, command=command)
    
    except Exception as e:
        return command.fail(error=e)

    actor_state.state = "IDLE"

    return command.finish(state = actor_state.state)


@parser.command("focusNominal")
async def focusNominal(
    command: Command,
    telsubsystems,
):
    """Focus nominal"""
    try:
        actor_state = command.actor.state
        focus = command.actor.focus

        await focus.nominal(command=command)

    except Exception as e:
        return command.fail(error=e)

    return command.finish(state = actor_state.state)
        

