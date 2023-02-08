import asyncio
from functools import partial
from typing import Tuple, TYPE_CHECKING, Any, Optional

from lvmagp.images import Image
from .background import Background

class DarkImageBackground(Background):
    """Base class for background."""

    __module__ = "lvmagp.images.processors.background"

    def __init__(
        self,
        filename: str=None,
        **kwargs: Any,
    ):
        """Initializes a wrapper."""


    def __call__(self, image: Image, **kwargs) -> Image:
        """return given image substracted with fits dark image.

        Args:
            image: Image.

        Returns:
            Background in float.
        """
        ...


__all__ = ["DarkImageBackground"]
