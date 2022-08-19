import asyncio

import click
import numpy as np

from logging import DEBUG

from clu.command import Command

from . import parser
from lvmagp.actor.statemachine import ActorState, ActorStateMachine
from lvmagp.exceptions import LvmagpIsNotIdle

from lvmagp.guide.worker import GuiderWorker
from math import nan


#@parser.command("guide", context_settings=dict(
    #ignore_unknown_options=True,)
#)
#@click.argument("cmd", type=click.Choice(['start', 'stop', 'pause', 'cont']), required=True) #
#@click.argument('extra_opts', nargs=-1, type=click.UNPROCESSED)
#def guide(
    #command: Command,
    #cmd,
    #extra_opts
#):
    #"""A wrapper around Python's extra_opts."""
    #logger = command.actor.log

    #d = dict([item.strip('--').split('=') for item in extra_opts])
    #logger.debug(f"{cmd} {d}")



@parser.command("guideStart")
@click.argument("exptime", type=float, default=nan)
@click.option("--pause", type=bool, default=False)
async def guideStart(
    command: Command,
    exptime: float,
    pause: bool,
):
    """Start guiding"""
    logger = command.actor.log
    statemachine = command.actor.statemachine
    telsubsystems = command.actor.telsubsystems

    guider = command.actor.guider

    try:
        if not statemachine.isIdle():
            return command.fail(error = LvmagpIsNotIdle(), state = statemachine.state)
        
        await statemachine.start(guider.work(exptime, pause))

        logger.debug(f"start guiding {statemachine.state} {await telsubsystems.foc.status()}")

    except Exception as e:
        return command.fail(error=e)

    return command.finish(state = statemachine.state.value)
            
@parser.command("guidePause")
@click.argument("pause", type=bool, default=True)
async def guidePause(
    command: Command,
    pause: bool,
):
    """Pause guiding"""
    logger = command.actor.log
    statemachine = command.actor.statemachine
    telsubsystems = command.actor.telsubsystems

    try:
        logger = command.actor.log
        statemachine = command.actor.statemachine

        await statemachine.pause(pause)

        logger.debug(f"state guiding {statemachine.state}")

    except Exception as e:
        return command.fail(error=e)

    return command.finish(state = statemachine.state.value)


@parser.command("guideStop")
async def guideStop(
    command: Command,
):
    """Stop guiding"""
    logger = command.actor.log
    statemachine = command.actor.statemachine
    telsubsystems = command.actor.telsubsystems

    try:
        logger.debug(f"stop guiding {statemachine.state}")

        await statemachine.stop()

    except Exception as e:
        return command.fail(error=e)

    return command.finish(state = statemachine.state.value)
        



