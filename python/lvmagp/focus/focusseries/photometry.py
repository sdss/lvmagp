from typing import Tuple, Dict, List, Any
import numpy as np
import logging

from lvmagp.images.processors.detection import SourceDetection
from lvmagp.focus.focusseries.base import FocusSeries
from lvmagp.focus.curvefit import fit_hyperbola
from lvmagp.images import Image


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class PhotometryFocusSeries(FocusSeries):
    """Focus series based on source detection."""

    __module__ = "lvmagp.utils.focusseries"

    def __init__(self, source_detection: SourceDetection, radius_column: str = "radius", **kwargs: Any):
        """Initialize a new projection focus series.

        Args:
            source_detection: Photometry to use for estimating PSF sizes
        """

        # stuff
        self._source_detection: SourceDetection = source_detection()
        self._radius_col = radius_column
        self._data: List[Dict[str, float]] = []

    def reset(self) -> None:
        """Reset focus series."""
        self._data = []

    async def analyse_image(self, image: Image, focus_value: float) -> None:
        """Analyse given image.

        Args:
            image: Image to analyse
            focus_value: Value to fit along, e.g. focus value or its offset
        """

        # do photometry
        await self._source_detection(image)

        # filter
        sources = image.catalog
        sources.sort(self._radius_col)
        sources.reverse()

        if sources is None:
            return
#        sources = sources[sources["ellipticity"] < 0.1]
#        sources = sources[sources["peak"] > 1000]
        sources = sources[sources[self._radius_col] > 0]

        # calculate median radius
        radius = np.median(sources[self._radius_col[:20]])
        radius_err = np.std(sources[self._radius_col[:20]])

        # log it
        log.info("Found median radius of %.1f+-%.1f.", radius, radius_err)

        # add to list
        self._data.append({"focus": focus_value, "r": radius, "rerr": radius_err})

    def fit_focus(self) -> Tuple[float, float]:
        """Fit focus from analysed images

        Returns:
            Tuple of new focus and its error
        """

        # get data
        focus = [d["focus"] for d in self._data]
        r = [d["r"] for d in self._data]
        rerr = [d["rerr"] for d in self._data]

        # fit focus
        try:
            foc, err = fit_hyperbola(focus, r, rerr)
        except (RuntimeError, RuntimeWarning):
            raise ValueError("Could not find best focus.")

        # get min and max foci
        min_focus = np.min(focus)
        max_focus = np.max(focus)
        if foc < min_focus or foc > max_focus:
            raise ValueError("New focus out of bounds: {0:.3f}+-{1:.3f}mm.".format(foc, err))

        # return it
        return float(foc), float(err)


__all__ = ["PhotometryFocusSeries"]
