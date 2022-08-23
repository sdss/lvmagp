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
            sources = sources[:42]
            ref = np.array([sources['x'], sources['y']]).transpose()
            self.reference_centroids.append(np.array([centroid_quadratic(img.data, xpeak=x, ypeak=y, search_boxsize=9) for x,y in ref]))



    async def find_offset(self, images: List[Image]) -> Tuple[float, float]:
        """ Find guide offset """

        diff_centroids = []

        try:
            for idx, img in enumerate(images):
                current_centroids = [centroid_quadratic(img.data, xpeak=x, ypeak=y, search_boxsize=7) for x,y in self.reference_centroids[idx]]
                diff_centroids.append(self.reference_centroids[idx]-np.array(current_centroids))

#            print(f"{diff_centroids}")
            print(f"west: {np.median(diff_centroids[0], axis=0)} east: {np.median(diff_centroids[1], axis=0)}")

        except Exception as ex:
            print(f"error {ex}")


__all__ = ["GuideOffsetSimple"]
