from abc import ABCMeta, abstractmethod

from lvmagp.images import Image
from lvmagp.images.processor import ImageProcessor


class Background(ImageProcessor, metaclass=ABCMeta):
    """Base class for background."""

    __module__ = "lvmagp.images.processors.background"

    @abstractmethod
    def __call__(self, image: Image, **kwargs) -> Image:
        """Calculate background in given image and append bkg.

        Args:
            image: Image.

        Returns:
            Background in float.
        """
        ...


__all__ = ["Background"]
