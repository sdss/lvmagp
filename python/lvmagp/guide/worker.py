import asyncio

import click
import numpy as np

from sdsstools import get_logger
from sdsstools.logger import SDSSLogger
from clu.command import Command

from lvmtipo.actors import lvm

from lvmagp.actor.statemachine import ActorState, ActorStateMachine
from lvmagp.images import Image
from lvmagp.images.processors.detection import DaophotSourceDetection, SepSourceDetection
from lvmagp.images.processors.astrometry import AstrometryDotNet

from lvmagp.guide.offset import GuideOffsetSimple

from math import nan

# TODO: this whould be good to have in clu
from basecam.notifier import EventNotifier


class GuiderWorker():
    def __init__(self, telsubsystems: lvm.TelSubSystem, statemachine: ActorStateMachine, logger:SDSSLogger=get_logger("guiding")):
        self.telsubsystems = telsubsystems
        self.statemachine = statemachine
        self.logger = logger
        self.notifier = EventNotifier()
        self.exptime = 10.0
        self.logger.info("init")
        self.offsetcalc = GuideOffsetSimple(SepSourceDetection)

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
                await self.offsetcalc.find_offset(images)
                await asyncio.sleep(1.0)

        except Exception as e:
            self.logger.error(f"error: {e}")
            self.statemachine.state = ActorState.IDLE

