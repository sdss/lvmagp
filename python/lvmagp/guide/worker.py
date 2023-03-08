from math import cos

import asyncio

import click
import numpy as np

from sdsstools import get_logger
from sdsstools.logger import SDSSLogger
from clu.command import Command
from clu.actor import AMQPActor

from lvmtipo.actors import lvm

from lvmagp.actor.statemachine import ActorState, ActorStateMachine
from lvmagp.images import Image

from lvmagp.guide.calc import GuideOffset, GuideOffsetPWI
from lvmagp.guide.offset import GuideCalc, GuideCalcAstrometry

from math import nan

# TODO: this whould be good to have in clu
from basecam.notifier import EventNotifier

async def statusTick(actor, data):

    try:
        actor.write(
            "i",
                {
                    "state": actor_statemachine.state.value,
                }
        )

    except Exception as e:

        actor.write("i", {"error": e})

class GuiderWorker():
    def __init__(self, 
                 telsubsystems: lvm.TelSubSystem,
                 statemachine: ActorStateMachine, 
                 offsetmount: GuideOffset = GuideOffsetPWI(),
                 offsetcalc: GuideCalc = GuideCalcAstrometry(),
                 actor: AMQPActor = None,
                 logger: SDSSLogger = get_logger("guiding")
                ):
        self.actor=actor
        self.telsubsystems = telsubsystems
        self.statemachine = statemachine
        self.logger = logger
        self.exptime = 5.0
        self.offsetmount = offsetcalc
        self.offsetcalc = offsetcalc

        self.logger.info("init")
       
    async def expose(self, exptime=nan):
            try:
                rc = await self.telsubsystems.agc.expose(exptime)
                return [ Image.from_file(v["filename"]) for k,v in rc.items() ]

            except Exception as e:
                self.logger.error(e)
                raise e

            return images


    async def work(self, exptime=nan, pause=False):

        try:
            self.statemachine.state = ActorState.GUIDE if not pause else ActorState.PAUSE

            if exptime is nan: exptime = self.exptime

            reference_images = await self.expose(exptime)
            await self.offsetcalc.reference_images(reference_images)

            self.logger.debug(f"activate guiding {self.statemachine.state}")
            while self.statemachine.state in (ActorState.GUIDE, ActorState.PAUSE):

                images = await self.expose(exptime)
                print(images[0].header)

                offset = await self.offsetcalc.find_offset(images)
                if self.statemachine.state is ActorState.GUIDE:
#                    await self.offset_mount(offset, images)
                    await asyncio.sleep(2.0)

        except Exception as e:
            self.logger.error(f"error: {e}")
            self.statemachine.state = ActorState.IDLE

