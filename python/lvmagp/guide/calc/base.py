from typing import Tuple, List
from lvmagp.images import Image


class GuideCalc:
    """Base class for guide series helper classes."""

    async def reference_target(self, images: List[Image]) -> None:
        """Analyse given images.
        """
        raise NotImplementedError

    async def find_offset(self, images: List[Image]) -> Tuple[float, float]:
        """Find guide offset from analysed images

        Returns:
            Tuple of new guide correction
        """
        raise NotImplementedError


__all__ = ["GuideCalc"]
