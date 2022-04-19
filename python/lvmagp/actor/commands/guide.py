import asyncio

import click
import numpy as np
from clu.command import Command

from . import parser
from lvmagp.actor.statemachine import ActorState, ActorStateMachine
from lvmagp.exceptions import LvmagpIsNotIdle

from lvmagp.guide.worker import GuiderWorker
from math import nan

@parser.command("guideStart")
@click.argument("EXPTIME", type=float, default=nan) #
async def guideStart(
    command: Command,
    telsubsystems,
    exptime: float,
):
    """Start guiding"""
    logger = command.actor.log
    actor_statemachine = command.actor.statemachine

    guider = command.actor.guider

    try:
        if not actor_statemachine.isIdle():
            return command.fail(error = LvmagpIsNotIdle(), state = actor_statemachine.state)
        
        await actor_statemachine.start(guider.work(telsubsystems, actor_statemachine, exptime))

        logger.debug(f"start guiding {actor_statemachine.state} {await telsubsystems.foc.status()}")

    except Exception as e:
        return command.fail(error=e)

    return command.finish(state = actor_statemachine.state.value)
            

@parser.command("guideStop")
async def guideStop(
    command: Command,
    telsubsystems,
):
    """Stop guiding"""
    try:
        logger = command.actor.log
        actor_statemachine = command.actor.statemachine

        logger.debug(f"stop guiding {actor_statemachine.state}")

        await actor_statemachine.stop()

    except Exception as e:
        return command.fail(error=e)

    return command.finish(state = actor_statemachine.state.value)
        

        

