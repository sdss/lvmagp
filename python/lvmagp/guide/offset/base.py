from typing import Tuple, List
from lvmagp.images import Image


class GuideOffset:
    """Base class for guide series helper classes."""

    def reset(self) -> None:
        """Reset reference images."""
        raise NotImplementedError

    async def analyse_images(self, images: List[Image]) -> None:
        """Analyse given images.
        """
        raise NotImplementedError

    async def find_offset(self) -> Tuple[float, float]:
        """Find guide offset from analysed images

        Returns:
            Tuple of new guide correction
        """
        raise NotImplementedError


__all__ = ["GuiderOffset"]
