from abc import ABCMeta, abstractmethod

from lvmagp.images import Image
from lvmagp.images.processor import ImageProcessor


class Photometry(ImageProcessor, metaclass=ABCMeta):
    """Base class for photometry processors."""

    __module__ = "lvmagp.images.processors.photometry"

    @abstractmethod
    async def __call__(self, image: Image) -> Image:
        """Do aperture photometry on given image.

        Args:
            image: Image to do aperture photometry on.

        Returns:
            Image with attached catalog.
        """
        ...


__all__ = ["Photometry"]
