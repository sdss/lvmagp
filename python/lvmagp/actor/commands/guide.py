import asyncio

import click
import numpy as np
from clu.command import Command

from . import parser
from lvmagp.actor.state import ActorState
from lvmagp import exceptions

async def guideTick(telsubsystems, actor_state, delta_time, logger):
    
    actor_state.state = "GUIDING"
    
    while actor_state.state == "GUIDING":
        try:
            logger.debug(f"active guiding {actor_state.state}")
            
        except Exception as e:
            logger.errror(e)

        await asyncio.sleep(delta_time)


@parser.command("guideStart")
@click.argument("DELTA_TIME", type=float, default=1.0)
async def guideStart(
    command: Command,
    telsubsystems,
    delta_time: float,
):
    """Start guiding"""
    logger = command.actor.log
    actor_state = command.actor.state

    try:
        if not actor_state.isIdle():
            return command.fail(error = LvmagpIsNotIdle(), state = actor_state.state)
        
        await actor_state.start(guideTick(telsubsystems, actor_state, delta_time, logger))

        logger.debug(f"start guiding {actor_state.state} {await telsubsystems.foc.status()}")

    except Exception as e:
        return command.fail(error=e)

    return command.finish(state = actor_state.state)
            

@parser.command("guideStop")
async def guideStop(
    command: Command,
    telsubsystems,
):
    """Stop guiding"""
    try:
        logger = command.actor.log
        actor_state = command.actor.state

        logger.debug(f"stop guiding {actor_state.state}")

        await actor_state.stop()

    except Exception as e:
        return command.fail(error=e)

    return command.finish(state = actor_state.state)
        

        

