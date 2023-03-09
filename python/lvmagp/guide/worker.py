from math import cos

import asyncio

import click
import numpy as np

from astropy.coordinates import SkyCoord, Angle

from sdsstools import get_logger
from sdsstools.logger import SDSSLogger
from clu.command import Command
from clu.actor import AMQPActor

from lvmtipo.actors import lvm

from lvmagp.actor.statemachine import ActorState, ActorStateMachine
from lvmagp.images import Image

from lvmagp.guide.offset import GuideOffset, GuideOffsetPWI
from lvmagp.guide.calc import GuideCalc, GuideCalcAstrometry

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
                 actor: AMQPActor = None,
                 exptime:float = 5.0,
                 logger: SDSSLogger = get_logger("guiding")
                ):
        self.actor=actor
        self.telsubsystems = telsubsystems
        self.statemachine = statemachine
        self.logger = logger
        self.exptime = exptime
        self.offest_mount = GuideOffsetPWI(telsubsystems.pwi)
        self.offest_calc = GuideCalcAstrometry(logger=logger)


    async def expose(self, exptime):
        """ expose cameras """
        try:
            filenames = (await self.telsubsystems.agc.expose(exptime)).flatten().unpack("*.filename")
#                self.logger.debug(f"filenames: {filenames}")
            return [ Image.from_file(f) for f in filenames ]

        except Exception as e:
            self.logger.error(e)
            raise e

        return images


    async def work(self, exptime=nan, pause=False):
        """ guider worker """
        try:
            self.logger.debug(f"start guiding {self.statemachine.state}")
            self.statemachine.state = ActorState.GUIDE if not pause else ActorState.PAUSE

            if exptime is nan: exptime = self.exptime

            reference_images = await self.expose(exptime)
            reference_position = await self.offest_calc.reference_images(reference_images)

            while self.statemachine.state in (ActorState.GUIDE, ActorState.PAUSE):

                current_images = await self.expose(exptime)

                current_position = await self.offest_calc.find_offset(current_images)
                self.logger.info(f"current position: {current_position}")

                if self.statemachine.state is ActorState.GUIDE:
                    await self.offest_mount.offset(reference_position, current_position)
                    await asyncio.sleep(2.0)

        except Exception as e:
            self.logger.error(f"error: {e}")
            self.statemachine.state = ActorState.IDLE

