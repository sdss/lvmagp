class GuideOffset:
    """Base class for guide offsets."""


    async def offset(self, *args, **kwargs) -> None:
        """Offset telescope

        Returns:
            
        """
        raise NotImplementedError


__all__ = ["GuiderOffset"]
