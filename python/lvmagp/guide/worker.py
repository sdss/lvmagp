import asyncio

import click
import numpy as np
from clu.command import Command

from lvmagp.actor.statemachine import ActorState, ActorStateMachine

from math import nan

# TODO: this whould be good to have in clu
from basecam.notifier import EventNotifier

# add some config parameters and more.


# TODO: improve it.
class GuiderWorker():
    def __init__(self, logger):
        self.logger = logger
        self.notifier = EventNotifier()
        self.exptime = 10.0
    
    async def work(self, telsubsystems, actor_statemachine, exptime=nan):
        
        actor_statemachine.state = ActorState.GUIDING
        if exptime is nan: exptime = self.exptime

        self.logger.debug(f"active fake guiding {actor_statemachine.state}")
        while actor_statemachine.state == ActorState.GUIDING:
            try:
                rc = await telsubsystems.agc.expose(exptime)
                files = {}
                for camera in rc:
                    files[camera] = rc[camera]["filename"]
                    self.logger.debug(f"{camera}: {files[camera]}")
                
                
            except Exception as e:
                self.logger.error(e)

            await asyncio.sleep(1.0)


