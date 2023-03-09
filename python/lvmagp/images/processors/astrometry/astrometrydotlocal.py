from abc import ABCMeta, abstractmethod
from typing import Any

from astropy.wcs import WCS

from lvmagp.images import Image
from lvmagp.images.processor import ImageProcessor

import astrometry

from .astrometry import Astrometry
import logging

log = logging.getLogger(__name__)

class AstrometryDotLocal(Astrometry):
    """Perform astrometry using python astrometry.net"""

    __module__ = "lvmagp.images.processors.astrometry"
    solver = None

    def __init__(
        self,
        source_count: int = 42,
        radius: float = 3.0,
        cache_directory: str = "astrometry_cache",
        scales={5,6},
        exceptions: bool = True,
        **kwargs: Any,
    ):
        """Init new astronomy.net processor.

        Args:
            source_count: Number of sources to send.
            radius: Radius to search in.
            exceptions: Whether to raise Exceptions.
        """

        self.source_count = source_count
        self.radius = radius
        self.exceptions = exceptions

        if not AstrometryDotLocal.solver:
            AstrometryDotLocal.solver = astrometry.Solver(
                astrometry.series_5200.index_files(
                    cache_directory=cache_directory,
                    scales=scales,
                )
            )

    def source_solve_default(self, image):
        solution = AstrometryDotLocal.solver.solve(
            stars=image.catalog['x', 'y'],
            size_hint=astrometry.SizeHint(
                lower_arcsec_per_pixel=0.9,
                upper_arcsec_per_pixel=1.1,
            ),
            position_hint=astrometry.PositionHint(
                ra_deg=image.header['RA'],
                dec_deg=image.header['DEC'],
                radius_deg=self.radius,
            ),
            solution_parameters=astrometry.SolutionParameters(
                logodds_callback=lambda logodds_list: astrometry.Action.STOP,
            ),
        )

        if solution.has_match():
            wcs = WCS(solution.best_match().wcs_fields)
            return wcs


    def __call__(self, image: Image, sort_by="peak") -> Image:
        """Find astrometric solution on given image.

        Args:
            image: Image to analyse.
        """

        # copy image
        img = image.copy()

        # get catalog
        if img.catalog is None:
            log.warning("No catalog found in image.")
            return img

#        cat = img.catalog[["x", "y", "flux", "peak"]].to_pandas().dropna()
        cat = img.catalog["x", "y", "flux", "peak"]

        # nothing?
        if cat is None or len(cat) < 3:
            log.warning("Not enough sources for astrometry.")
            img.header["WCSERR"] = 1
            return img

        # sort it, remove saturated stars and take N brightest sources
        cat.sort(sort_by)
        cat.reverse()
        cat = cat[cat["peak"] < 60000]
        cat = cat[:self.source_count]

        img.catalog = cat

#        print(img.catalog["x", "y"])
        img.astrometric_wcs = self.source_solve_default(img)
        log.debug(img.astrometric_wcs)

        # finished
        return img

__all__ = ["AstrometryDotLocal"]
