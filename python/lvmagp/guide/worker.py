import asyncio

import click
import numpy as np
from clu.command import Command

from lvmagp.actor.statemachine import ActorState, ActorStateMachine

# add some config parameters and more.

class GuiderWorker():
    def __init__(self):
        pass
    
    
    async def work(self, telsubsystems, actor_statemachine, delay, logger):
        
        actor_statemachine.state = ActorState.GUIDING

        logger.debug(f"active fake guiding {actor_statemachine.state}")
        while actor_statemachine.state == ActorState.GUIDING:
            try:
                rc = await telsubsystems.agc.expose(10.0)
                files = {}
                for camera in rc:
                    files[camera] = rc[camera]["filename"]
                    logger.debug(f"{camera}: {files[camera]}")
                
                
            except Exception as e:
                logger.error(e)

            await asyncio.sleep(delay)


