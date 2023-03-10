from math import cos
from typing import Optional, Callable

import asyncio

import click
import numpy as np

import pandas as pd
import json
from pandas import json_normalize

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

debug = False

# debugging start
def fname(camera):
    idx = fname.start + fname.idx % fname.num
    return f"/data/lvm/skyw/agcam/{camera}/20230225/lvm.skyw.agcam.{camera}_00000{idx}.fits"

fname.cameras=["west", "east"]
fname.start=204
fname.start=254
fname.num=130
fname.idx=0

async def debug_files():
    """ expose cameras """

    try:
        filenames=[]
        for cam in fname.cameras:
            filenames.append(fname(cam))
        fname.idx+=1
#        print(filenames)
        return filenames

    except Exception as e:
        raise e

# debugging end

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
        self.exptime = self.default_exptime = exptime
        self.offest_mount = GuideOffsetPWI(telsubsystems.pwi)
        self.offest_calc = GuideCalcAstrometry(logger=logger)

    async def expose(self, exptime):
        """ expose cameras """
        try:
            if debug:
                filenames = await debug_files()
            else:
                filenames = (await self.telsubsystems.agc.expose(exptime)).flatten().unpack("*.filename")
#                self.logger.debug(f"filenames: {filenames}")
            return filenames, [Image.from_file(f) for f in filenames]

        except Exception as e:
            self.logger.error(e)
            raise e


    async def reference(self,
                   exptime=None,
                   ra_h: float=nan,
                   deg_d: float=nan,
                   pause:bool=False,
                   callback: Optional[Callable[..., None]] = None ):
        """ guider worker """
        try:
            self.statemachine.state = ActorState.START
            self.logger.debug(f"start guiding {self.statemachine.state}")

            self.exptime = exptime if exptime else self.default_exptime
            if exptime is nan: exptime = self.exptime

            self.reference_position = None

            reference_filenames, images = await self.expose(exptime)
            reference_images, self.reference_position = await self.offest_calc.reference_target(images)

            self.statemachine.state = ActorState.GUIDE if not pause else ActorState.PAUSE

            if callback:
                await callback(is_reference=True,
                               state=self.statemachine.state,
                               filenames=reference_filenames,
                               images=reference_images,
                               position=self.reference_position)

            return self.reference_position, reference_filenames

        except Exception as e:
            self.logger.error(f"error: {e}")
            self.statemachine.state = ActorState.IDLE
            if callback:
                await callback(is_reference=True,
                               state=self.statemachine.state,
                               filenames=reference_filenames,
                               images=reference_images,
                               position=self.reference_position)


    async def loop(self, callback: Optional[Callable[..., None]] = None ):
        """ guider worker """
        try:
            while self.statemachine.state in (ActorState.GUIDE, ActorState.PAUSE):

                current_filenames, images = await self.expose(self.exptime)
                current_images, current_position = await self.offest_calc.find_offset(images)

                if self.statemachine.state is ActorState.GUIDE:
                    correction = await self.offest_mount.offset(self.reference_position, current_position)
                    if debug:
                        await asyncio.sleep(2.0)

                if callback:
                    await callback(is_reference=False,
                                   state=self.statemachine.state,
                                   filenames=current_filenames,
                                   images=current_images,
                                   position=current_position,
                                   correction=correction)

        except Exception as e:
            self.logger.error(f"error: {e}")
            self.statemachine.state = ActorState.IDLE

