from typing import Tuple, Dict, List, Any
import logging

import numpy as np

from lvmagp.guide.offset.base import GuideOffset
from astropy.coordinates import Angle, SkyCoord
from lvmtipo.pwimount import delta_radec2mot_axis

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class GuideOffsetPWI(GuideOffset):
    """Guide offset based on source detection."""

    def __init__(self, telescope_mount, corr_factor:float=0.8, min_offset:float=0.8):
        """ Initialize """

        self.telescope_mount = telescope_mount
        self.corr_factor = corr_factor
        self.min_offset = min_offset

    async def offset(self, reference_position:SkyCoord, current_position:SkyCoord):
        """ offset mount """

        status = None
        try:
            ra_diff, dec_diff = [f.arcsecond for f in reference_position.spherical_offsets_to(current_position)]
            log.debug(f"radec: {ra_diff} {dec_diff}")

            axis0_diff, axis1_diff = delta_radec2mot_axis(reference_position, current_position)
            log.debug(f"axis: {axis0_diff} {axis1_diff}")

            status = {"radec_diff": (ra_diff, dec_diff), "axis_diff": (axis0_diff.deg, axis1_diff.deg)}
            axis0_offset = axis0_diff.deg * self.corr_factor
            axis1_offset = axis1_diff.deg * self.corr_factor

            if(abs(axis0_offset) > self.min_offset or abs(axis1_offset) > self.min_offset):
                log.debug(f"correct axis: {axis0_offset} {axis1_offset}")
                await self.telescope_mount.offset(axis0_add_arcsec = axis0_offset,
                                                  axis1_add_arcsec = axis1_offset)
                status.update({"axis_offset": (axis0_offset, axis1_offset)})

            return status

        except Exception as ex:
            print(f"error: {type(ex)} {ex}")


__all__ = ["GuideOffsetPWI"]
