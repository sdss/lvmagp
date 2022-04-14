import asyncio

import click
import numpy as np
from clu.command import Command

from . import parser
from lvmagp.actor.statemachine import ActorState, ActorStateMachine
from lvmagp.exceptions import LvmagpIsNotIdle


async def guideTick(telsubsystems, actor_statemachine, delay, logger):
    
    actor_statemachine.state = ActorState.GUIDING

    while actor_statemachine.state == ActorState.GUIDING:
        try:
            logger.debug(f"active guiding {actor_statemachine.state}")
            
        except Exception as e:
            logger.errror(e)

        await asyncio.sleep(delay)


@parser.command("guideStart")
@click.argument("DELAY", type=float, default=1.0) #
async def guideStart(
    command: Command,
    telsubsystems,
    delay: float,
):
    """Start guiding"""
    logger = command.actor.log
    actor_statemachine = command.actor.statemachine

    try:
        if not actor_statemachine.isIdle():
            return command.fail(error = LvmagpIsNotIdle(), state = actor_statemachine.state)
        
        await actor_statemachine.start(guideTick(telsubsystems, actor_statemachine, delay, logger))

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
        

        

