from __future__ import annotations, print_function, division, absolute_import

import asyncio
import os
import warnings
from contextlib import suppress

from clu.actor import AMQPActor
from .commands import parser as lvm_command_python

# from scpactor import __version__


__all__ = ["lvmagp"]


class lvmagp(AMQPActor):
    """SCP controller actor.
    In addition to the normal arguments and keyword parameters for
    `~clu.actor.AMQPActor`, the class accepts the following parameters.
    Parameters
    ----------
    controllers
        The list of `.SCP_Controller` instances to manage.
    """

    parser = lvm_command_python

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
