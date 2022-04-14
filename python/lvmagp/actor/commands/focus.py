import asyncio

import click
import numpy as np
from clu.command import Command

from cluplus.proxy import unpack

from . import parser

from lvmagp.actor.statemachine import ActorState, ActorStateMachine
from lvm.tel.focus import Focus
from lvmagp.exceptions import LvmagpIsNotIdle


@parser.command("focusOffset")
@click.argument("offset", type=float)
async def focusOffset(
    command: Command,
    telsubsystems,
    offset: float,
):
    """Focus offest"""
    try:
        actor_statemachine = command.actor.statemachine
        focus = command.actor.focus

        await focus.offset(offset, command=command)
         
    except Exception as e:
        return command.fail(error=e)

    return command.finish(state = actor_statemachine.state.value)


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
        actor_statemachine = command.actor.statemachine
        focus = command.actor.focus

        if not actor_statemachine.isIdle():
            return command.fail(error = LvmagpIsNotIdle(), state = actor_statemachine.state.value)

        actor_statemachine.state = ActorState.FOCUSING
        command.info(state = actor_statemachine.state.value)
        
        logger.debug(f"start focusing {actor_statemachine.state.value} {await telsubsystems.foc.status()}")
        await focus.fine(expotime, command=command)
    
    except Exception as e:
        return command.fail(error=e)

    actor_statemachine.state = ActorState.IDLE

    return command.finish(state = actor_statemachine.state.value)


@parser.command("focusNominal")
async def focusNominal(
    command: Command,
    telsubsystems,
):
    """Focus nominal"""
    try:
        actor_statemachine = command.actor.statemachine
        focus = command.actor.focus

        await focus.nominal(command=command)

    except Exception as e:
        return command.fail(error=e)

    return command.finish(state = actor_statemachine.state.value)
        

