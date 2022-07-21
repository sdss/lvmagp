from abc import ABCMeta, abstractmethod
from typing import Any

from lvmagp.images import Image


class ImageProcessor(object, metaclass=ABCMeta):
    def __init__(self, **kwargs: Any):
        """Init new image processor."""

    @abstractmethod
    async def __call__(self, image: Image) -> Image:
        """Processes an image.

        Args:
            image: Image to process.

        Returns:
            Processed image.
        """
        ...

    async def reset(self) -> None:
        """Resets state of image processor"""
        pass


__all__ = ["ImageProcessor"]
