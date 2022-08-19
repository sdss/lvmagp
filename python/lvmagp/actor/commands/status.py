import asyncio

import click
import numpy as np
from clu.command import Command

from . import parser
from lvmagp.actor.statemachine import ActorState, ActorStateMachine
from lvmagp import exceptions


@parser.command("status")
async def status(
    command: Command,
):
    """Status information"""
    actor_statemachine = command.actor.statemachine
    
    status = {
        "state": actor_statemachine.state.value,
    }    

    return command.finish(status)
