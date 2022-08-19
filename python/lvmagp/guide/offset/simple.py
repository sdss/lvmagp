from typing import Tuple, Dict, List, Any
import numpy as np
import logging

from lvmagp.images import Image
from lvmagp.images.processors.detection import SourceDetection
from lvmagp.guide.offset.base import GuideOffset

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class GuideOffsetSimple(GuideOffset):
    """Guide offset based on source detection."""

    def __init__(self, source_detection: SourceDetection, **kwargs: Any):
        """Initialize"""

        self.source_detection: SourceDetection = source_detection()
        self.reset()

    def reset(self) -> None:
        """Reset reference image."""
        self.reference_stars = None
        self.lastest_stars = None

    async def analyse_image(self, images: List[Image]) -> None:
        """Analyse given images."""

        self.lastest_stars = []

        # do photometry
        for img in images:
            image = await self.source_detection(img)
            # filter
            sources = image.catalog
            sources.sort("peak")
            sources.reverse()
            self.lastest_stars.append(sources[:7])

        if not self.reference_stars:
            print("update ref")
            self.reference_stars = self.lastest_stars

    async def find_offset(self) -> Tuple[float, float]:
        """ Find guide offset """

        print(self.lastest_stars[0])
        print(self.reference_stars[0])

        rs = np.array([self.reference_stars[0]['x'], self.reference_stars[0]['y']])
        ls = np.array([self.lastest_stars[0]['x'], self.lastest_stars[0]['y']])
        print(rs-ls)



    #def fit_focus(self) -> Tuple[float, float]:
        #"""Fit focus from analysed images

        #Returns:
            #Tuple of new focus and its error
        #"""

        ## get data
        #focus = [d["focus"] for d in self._data]
        #r = [d["r"] for d in self._data]
        #rerr = [d["rerr"] for d in self._data]

        ## fit focus
        #try:
            #foc, err = fit_hyperbola(focus, r, rerr)
        #except (RuntimeError, RuntimeWarning):
            #raise ValueError("Could not find best focus.")

        ## get min and max foci
        #min_focus = np.min(focus)
        #max_focus = np.max(focus)
        #if foc < min_focus or foc > max_focus:
            #raise ValueError("New focus out of bounds: {0:.3f}+-{1:.3f}mm.".format(foc, err))

        ## return it
        #return float(foc), float(err)


__all__ = ["GuideOffsetSimple"]
