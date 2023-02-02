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
from lvmagp.images.processors.detection import DaophotSourceDetection, SepSourceDetection

from lvmagp.guide.offset import GuideOffset, GuideOffsetSimple

from math import nan

# TODO: this whould be good to have in clu
from basecam.notifier import EventNotifier

#async def statusTick(command, pwi: PWI4, delta_time):

    #lock = command.actor.statusLock

    #while True:
        #try:
            #if not lock.locked():
                #status = await statusPWI(pwi, lock)

                #command.actor.write(
                        #"i",
                        #{
                            #"is_slewing": status.mount.is_slewing,
                        #}
                #)

        #except Exception as e:

            #command.actor.write("i", {"error": e})

        #await asyncio.sleep(delta_time)

class GuiderWorker():
    def __init__(self, 
                 telsubsystems: lvm.TelSubSystem,
                 statemachine: ActorStateMachine, 
                 offsetcalc: GuideOffset = GuideOffsetSimple(SepSourceDetection),
                 actor: AMQPActor = None,
                 logger: SDSSLogger = get_logger("guiding")
                ):
        self.actor=actor
        self.telsubsystems = telsubsystems
        self.statemachine = statemachine
        self.logger = logger
        self.notifier = EventNotifier()
        self.exptime = 10.0
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

    # TODO should go in a extra class with base class
    async def offset_mount(self, offset, images):
            """
            One or more of the following offsets can be specified as a keyword argument:

            AXIS_reset: Clear all position and rate offsets for this axis. Set this to any value to issue the command.
            AXIS_stop_rate: Set any active offset rate to zero. Set this to any value to issue the command.
            AXIS_add_arcsec: Increase the current position offset by the specified amount
            AXIS_set_rate_arcsec_per_sec: Continually increase the offset at the specified rate

            Where AXIS can be one of:

            ra: Offset the target Right Ascension coordinate
            dec: Offset the target Declination coordinate
            axis0: Offset the mount's primary axis position
                (roughly Azimuth on an Alt-Az mount, or RA on In equatorial mount)
            axis1: Offset the mount's secondary axis position
                (roughly Altitude on an Alt-Az mount, or Dec on an equatorial mount)
            path: Offset along the direction of travel for a moving target
            transverse: Offset perpendicular to the direction of travel for a moving target

            For example, to offset axis0 by -30 arcseconds and have it continually increase at 1
            arcsec/sec, and to also clear any existing offset in the transverse direction,
            you could call the method like this:

            mount_offset(axis0_add_arcsec=-30, axis0_set_rate_arcsec_per_sec=1, transverse_reset=0)

            """
            
            from astropy.coordinates import EarthLocation,SkyCoord
            from astropy.time import Time
            from astropy import units as u
            from astropy.coordinates import AltAz

            try:

                self.logger.info(f"{offset}")
                try:
                    self.actor.write(
                            "i",
                            {
                                "state": self.statemachine.state.name,
                                "offset_ra": offset[0],
                                "offset_dec": offset[1],
                            }
                    )

                except Exception as e:
                    self.actor.write("i", {"error": e})

                if self.statemachine.state == ActorState.GUIDE and (abs(offset) > [0.5, 0.5]).any():
                    offset *= [images[0].header['BINX'], images[0].header['BINY']]
                    offset *= [images[0].header['PIXELSC'], images[0].header['PIXELSC']]
                    offset /= [cos(np.deg2rad(images[0].header['DEC'])), 1.0]
                    offset *= -0.95
                    self.logger.debug(f"correcting {offset}")

                    await self.telsubsystems.pwi.offset(ra_add_arcsec = offset[0], dec_add_arcsec = offset[1])

                    from lvmtipo.site import Site
                    site = Site(name = images[0].header['OBSERVAT'])
                    observing_location = EarthLocation(lat=site.lat, lon=site.long, height=site.alt*u.m)  
                    observing_time = Time(images[0].header['DATE-OBS'])
                    aa = AltAz(location=observing_location, obstime=observing_time)

                    coord = SkyCoord()
                    coord.transform_to(aa)

                    await self.telsubsystems.pwi.offset(axis0_add_arcsec = offset[0], axis1_add_arcsec = offset[1])


            except Exception as e:
                self.logger.error(e)
                raise e

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
                await self.offset_mount(offset, images)
                await asyncio.sleep(1.0)

        except Exception as e:
            self.logger.error(f"error: {e}")
            self.statemachine.state = ActorState.IDLE

