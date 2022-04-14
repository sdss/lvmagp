# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: statemachine.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import enum
import asyncio

#TODO: Using something like pytransition whould be way more clean
#  https://github.com/pytransitions/transitions/blob/master/README.md
#  https://github.com/pytransitions/transitions#async


class ActorState(enum.Enum):
    """Enumeration of states."""

    IDLE = "IDLE"
    STARTED = "STARTED"
    STOP = "STOP"
    PAUSE = "PAUSE"
    GUIDING = "GUIDING"
    FOCUSING = "FOCUSING"

class WrongStateTypeException(Exception):
    """The state should be of type ActorState"""

class ActorStateMachine:
    def __init__(self):
        self.task = None
        self.state = ActorState.IDLE

    def isIdle(self):
        return self.state == ActorState.IDLE

    @property
    def state(self):
        return self.__state
    
    @state.setter
    def state(self, s):
        if isinstance(s, ActorState):
            self.__state = s
            return
        raise WrongStateTypeException()
            
    async def start(self, coro):
        await self.stop()
        self.task = asyncio.create_task(coro)
        self.state = ActorState.STARTED

    async def stop(self):
        if not self.task:
            return

        self.state = ActorState.STOP

        try:
            await asyncio.wait_for(self.task, timeout=5)

        except asyncio.TimeoutError:
            self.task.cancel()

        self.state = ActorState.IDLE
        self.task = None

        
