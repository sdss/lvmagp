import asyncio

import click
import numpy as np
from clu.command import Command

from . import parser
from lvmagp.guide import GuideState

async def guideTick(telsubsystems, guide_state, delta_time, logger):
    
    guide_state.state = "GUIDING"
    
    while guide_state.state == "GUIDING":
        try:
            logger.debug(f"active guiding {guide_state.state}")
            
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
    guide_state = command.actor.guide_state

    try:
        await guide_state.start(guideTick(telsubsystems, guide_state, delta_time, logger))

        logger.debug(f"start guiding {guide_state.state} {telsubsystems.foc.status()}")

    except Exception as e:
        return command.fail(error=e)

    return command.finish(state = guide_state.state)
            
            

@parser.command("guideStop")
async def guideStop(
    command: Command,
    telsubsystems,
):
    """Stop guiding"""
    try:
        logger = command.actor.log
        guide_state = command.actor.guide_state

        logger.debug(f"stop guiding {guide_state}")

        await guide_state.stop()

    except Exception as e:
        return command.fail(error=e)

    return command.finish(state = guide_state.state)
        

@parser.command("guideStatus")
async def guideStop(
    command: Command,
    telsubsystems,
):
    """Status guiding"""
    guide_state = command.actor.guide_state
    
    return command.finish(state = guide_state.state)
        

