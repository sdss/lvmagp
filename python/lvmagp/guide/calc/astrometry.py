from typing import Tuple, Dict, List, Any

import logging

from asyncio import gather
from threading import Thread

import numpy as np
import astrometry

from scipy.ndimage import gaussian_filter
from scipy.ndimage import median_filter
from astropy.wcs import WCS
from astropy.stats import mad_std
from astropy.coordinates import SkyCoord, Angle

from sdsstools import get_logger
from sdsstools.logger import SDSSLogger

from lvmagp.images import Image

from lvmagp.guide.calc.base import GuideCalc
from lvmagp.images.processors.astrometry import Astrometry, AstrometryDotLocal
from lvmagp.images.processors.detection import DaophotSourceDetection, SepSourceDetection

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class GuideCalcAstrometry(GuideCalc):
    """Guide offset based on source detection."""

    solver = astrometry.Solver(
        astrometry.series_5200.index_files(
            cache_directory="astrometry_cache",
            scales={5,6},
        )
    )

    def __init__(self,
                 source_count = 42,
                 sort_by = "peak",
                 logger: SDSSLogger = get_logger("guideastrocalc"),
                 **kwargs: Any):
        """Initialize"""

        self.reference_images = None
        self.reference_midpoint = None
        self.source_count = source_count
        self.sort_by = sort_by
        self.logger = logger
        self.source_detection = DaophotSourceDetection(fwhm=8, threshold=8)
        self.source_astrometry = AstrometryDotLocal(source_count=source_count, radius=1.0)

    def calc_midpoint(self, images):
        cams={img.header["CAMNAME"]: idx for idx, img in enumerate(images)}
        image_num = len(images)
        if "east" in cams.keys() and "west" in cams.keys():
            pa = images[cams["east"]].center.position_angle(images[cams["west"]].center)
            sep = images[cams["east"]].center.separation(images[cams["west"]].center)
            return images[cams["east"]].center.directional_offset_by(pa, -sep/2)

        elif image_num == 1 and not cam.keys().isdisjoint(["east", "west"]):
            log.warning("single camera not implemented")

        else:
            raise Exception("unsupported camera image set: {cams}")


    # we do threading instead of asyncio tasks, because astrometry is written in C
    async def astrometric(self, images, sort_by="peak", source_count=42):
        class AstrometryThread(Thread):
            # constructor
            def __init__(self, parent, img):
                # execute the base constructor
                Thread.__init__(self)
                self.parent = parent
                self.image = img
                self.image.center = None

            # override the run function
            def run(self):
                self.image.data = median_filter(self.image.data, size=2)

#                self.parent.logger.debug(f"astrometric source detect {self.image.header['CAMNAME']}")
                self.image = self.parent.source_detection(self.image)
 #               self.parent.logger.debug(f"astrometric astronometry {self.image.header['CAMNAME']}")
                self.image = self.parent.source_astrometry(self.image)
  #              self.parent.logger.debug(f"astrometric done {self.image.header['CAMNAME']}")
                if self.image.astrometric_wcs:
                    self.image.center = self.image.astrometric_wcs.pixel_to_world(self.image.header['NAXIS1']//2, self.image.header['NAXIS2']//2)


        worker = [AstrometryThread(self, img) for img in images]
        [w.start() for w in worker]
        [w.join() for w in worker]
        images = [w.image for w in worker]

        midpoint = self.calc_midpoint(images)
#        self.logger.debug(f"midpoint: {midpoint}")
        return images, midpoint


    async def reference_target(self, images: List[Image]) -> SkyCoord:
        """Analyse given images."""

#        self.logger.debug(f"astrometric start")
        self.reference_images, self.reference_midpoint = await self.astrometric(images, sort_by=self.sort_by, source_count=self.source_count)
#        self.logger.debug(f"astrometric done")

        return self.reference_images, self.reference_midpoint


    async def find_offset(self, images: List[Image]) -> SkyCoord:
        """ Find guide offset """

        try:
            new_images, new_midpoint = await self.astrometric(images, sort_by=self.sort_by, source_count=self.source_count)

            return new_images, new_midpoint

        except Exception as ex:
            print(f"error: {type(ex)} {ex}")


__all__ = ["GuideCalcAstrometry"]
