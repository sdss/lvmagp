from typing import Tuple, Dict, List, Any
import numpy as np
import logging

from lvmagp.images import Image
from lvmagp.images.processors.detection import SourceDetection
from lvmagp.guide.offset.base import GuideOffset

from photutils.centroids import centroid_quadratic


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class GuideOffsetSimple(GuideOffset):
    """Guide offset based on source detection."""

    def __init__(self, source_detection: SourceDetection, **kwargs: Any):
        """Initialize"""

        self.source_detection: SourceDetection = source_detection()
        self.reference_centroids = None


    async def reference_images(self, images: List[Image]) -> None:
        """Analyse given images."""

        self.reference_centroids = []

        # do photometry
        for img in images:
            image = await self.source_detection(img)
            # filter
            sources = image.catalog
            sources.sort("peak")
            sources.reverse()
            sources = sources[:3]
            ref = np.array([sources['x'], sources['y']]).transpose()
            self.reference_centroids.append(np.array([centroid_quadratic(img.data, xpeak=x, ypeak=y, search_boxsize=9) for x,y in ref]))



    async def find_offset(self, images: List[Image]) -> Tuple[float, float]:
        """ Find guide offset """

        diff_centroids = []

        try:
            for idx, img in enumerate(images):
                current_centroids = np.array([centroid_quadratic(img.data, xpeak=x, ypeak=y, search_boxsize=9) for x,y in self.reference_centroids[idx]])
                diff_centroids.append(self.reference_centroids[idx]-current_centroids)

            print(f"{diff_centroids}")

        except Eception as ex:
            print("error {ex}")

        #print(self.lastest_stars[0])
        #print(self.reference_stars[0])

        #rs = np.array([self.reference_stars[0]['x'], self.reference_stars[0]['y']])
        #ls = np.array([self.lastest_stars[0]['x'], self.lastest_stars[0]['y']])
        #print(rs-ls)



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
