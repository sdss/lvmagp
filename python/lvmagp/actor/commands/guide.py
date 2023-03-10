import asyncio

import click
import numpy as np
import json

from logging import DEBUG
from math import nan
from functools import partial

from clu.command import Command
from clu.actor import AMQPActor

from . import parser

from astropy.coordinates import SkyCoord, Angle

from lvmagp.actor.statemachine import ActorState, ActorStateMachine
from lvmagp.exceptions import LvmagpIsNotIdle
from lvmagp.guide.worker import GuiderWorker
from lvmagp.json_serializers import serialize_skycoord


async def callback(actor:AMQPActor,
                   is_reference:bool,
                   state:ActorState,
                   filenames:list,
                   images:list,
                   position:SkyCoord,
                   correction:list=None):

    status = {"isreference": is_reference,
              "state": state.name,
              "filenames": filenames,
              "catalog": [json.loads(img.catalog.to_pandas().to_json()) for img in images],
              "position": serialize_skycoord(position)
             }

    if not is_reference:
        status.update({"correction": correction})

    actor.write("i", **status, validate = False)


@parser.command("guideStart")
@click.argument("exptime", type=float, default=nan)
@click.argument("ra_h", type=float, default=nan)
@click.argument("deg_d", type=float, default=nan)
@click.option("--pause", type=bool, default=False)
@click.option("--force", type=bool, default=True)
async def guideStart(
    command: Command,
    exptime: float,
    ra_h: float,
    deg_d: float,
    pause: bool,
    force: bool,
):
    """Start guiding"""
    logger = command.actor.log
    statemachine = command.actor.statemachine
    telsubsystems = command.actor.telsubsystems

    logger.debug(f"start guiding")

    guider = command.actor.guider

    try:
        if not statemachine.isIdle():
            if force and statemachine.state == ActorState.GUIDE:
                await statemachine.stop()
            else:
                return command.fail(error = LvmagpIsNotIdle(), state = statemachine.state.name)

        logger.debug(f"start guiding {statemachine.state}")

        await guider.reference(exptime, pause, callback=partial(callback, command.actor))

        await statemachine.start(guider.loop(callback=partial(callback, command.actor)))

        logger.debug(f"started guiding {statemachine.state}")

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
        



