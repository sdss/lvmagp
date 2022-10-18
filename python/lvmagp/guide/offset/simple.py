from typing import Tuple, Dict, List, Any
import logging

import numpy as np


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
        self.max_sources = 42
        self.search_boxsize = 9

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
            sources = sources[:self.max_sources]
            ref = np.array([sources['x'], sources['y']]).transpose()
            self.reference_centroids.append(
                np.array(
                    [centroid_quadratic(img.data, xpeak=x, ypeak=y, search_boxsize=self.search_boxsize) 
                        for x, y in ref]))
        print(f"{len(self.reference_centroids[0])} {len(self.reference_centroids[1])}")

    async def find_offset(self, images: List[Image]) -> float:
        """ Find guide offset """

        diff_centroids = []

        try:
            for im_idx, img in enumerate(images):
                ref_cen = self.reference_centroids[im_idx]
                diff_cen = []
                for c_idx, xy in enumerate(ref_cen):
                   x, y = xy
                   centroid = centroid_quadratic(img.data, xpeak=x, ypeak=y, search_boxsize=self.search_boxsize)
                   if not np.isnan(centroid).any():
                       diff_cen.append(ref_cen[c_idx] - centroid)
                diff_centroids.append(np.array(diff_cen))
            print(f"{images[0].header['CAMNAME']}: {np.median(diff_centroids[0], axis=0)} {images[1].header['CAMNAME']}: {np.median(diff_centroids[1], axis=0)}px")
            diff =  np.median(np.concatenate((diff_centroids[0], diff_centroids[1])), axis=0)
            return diff
        

        except Exception as ex:
            print(f"error: {type(ex)} {ex}")


__all__ = ["GuideOffsetSimple"]
