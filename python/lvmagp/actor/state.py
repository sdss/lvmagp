# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: lvm/tel/focus.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import asyncio


#TODO: Using something like pytransition whould be way more clean
#  https://github.com/pytransitions/transitions/blob/master/README.md
#  https://github.com/pytransitions/transitions#async

#TODO: Maybe enums and a dict with enum to string whould be better.

class ActorState:
    def __init__(self):
        self.task = None
        self.state = "IDLE"

    def isIdle(self):
        return self.state == "IDLE"

    @property
    def state(self):
        return self.__state
    
    @state.setter
    def state(self, s):
        self.__state = s #TODO: add some checks.

    async def start(self, coro):
        await self.stop()
        self.task = asyncio.create_task(coro)
        self.state = "STARTED"


    async def stop(self):
        if not self.task:
            return

        self.state = "STOP"

        try:
            await asyncio.wait_for(self.task, timeout=5)

        except asyncio.TimeoutError:
            self.task.cancel()

        self.state = "IDLE"
        self.task = None

        
