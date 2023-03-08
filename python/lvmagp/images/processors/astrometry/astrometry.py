from abc import ABCMeta, abstractmethod

from lvmagp.images import Image
from lvmagp.images.processor import ImageProcessor


class Astrometry(ImageProcessor, metaclass=ABCMeta):
    """Base class for source astrometry."""

    __module__ = "lvmagp.images.processors.astrometry"
    @abstractmethod
    def __call__(self, image: Image) -> Image:
        """Find astrometric solution on given image.
        Args:
            image: Image to analyse.
        Returns:
            Processed image.
        """
        ...


__all__ = ["Astrometry"]
