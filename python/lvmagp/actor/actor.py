from __future__ import absolute_import, annotations, division, print_function

from clu.actor import AMQPActor

from .commands import parser as lvm_command_python


# from scpactor import __version__

__all__ = ["lvmagp"]


class lvmagp(AMQPActor):
    """AGP  actor.
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
