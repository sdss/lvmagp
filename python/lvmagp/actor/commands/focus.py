import asyncio

import click
import numpy as np
from clu.command import Command

from . import parser
from lvmagp.guide import GuideState
from lvm.tel.focus import Focus


@parser.command("focusOffset")
@click.argument("offset", type=float)
async def focusOffset(
    command: Command,
    telsubsystems,
    offset: float,
):
    """Focus offest"""

    try:
        logger = command.actor.log
        guide_state = command.actor.guide_state
        focus = command.actor.focus

        if not guide_state.isIdle():
            return command.fail(error = LvmagpNoFocusingWhileGuiding())
        
        await focus.offset(offset)
         
    except Exception as e:
        return command.fail(error=e)

    return command.finish(state = guide_state.state)
            

@parser.command("focusFine")
async def focusFine(
    command: Command,
    telsubsystems,
):
    """Focus fine"""
    try:
        logger = command.actor.log
        guide_state = command.actor.guide_state
        focus = command.actor.focus

        if not guide_state.isIdle():
            return command.fail(error = LvmagpNoFocusingWhileGuiding())

        await focus.fine()
    
    except Exception as e:
        return command.fail(error=e)

    return command.finish(state = guide_state.state)
        

@parser.command("focusNominal")
async def focusNominal(
    command: Command,
    telsubsystems,
):
    """Focus nominal"""
    logger = command.actor.log
    guide_state = command.actor.guide_state
    
    try:
        logger = command.actor.log
        guide_state = command.actor.guide_state

        if not guide_state.isIdle():
            return command.fail(error = LvmagpNoFocusingWhileGuiding())
    
        await focus.nominal()

    except Exception as e:
        return command.fail(error=e)

    return command.finish(state = guide_state.state)
        

