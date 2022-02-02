from __future__ import absolute_import, annotations, division, print_function

from clu.actor import AMQPActor

from lvmagp.actor.commands import parser as lvm_command_python

from lvmagp import __version__
# from scpactor import __version__

__all__ = ["lvmagp"]


class lvmagp(AMQPActor):
    """AGP actor.
    In addition to the normal arguments and keyword parameters for
    `~clu.actor.AMQPActor`, the class accepts the following parameters.
    """

    parser = lvm_command_python

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.schema = {
            "type": "object",
            "properties": {
                "fail": {"type": "string"},
                "Img_ra2000": {"type": "string"},
                "Img_dec2000": {"type": "string"},
                "Img_pa": {"type": "string"},
                "offset_ra": {"type": "string"},
                "offset_dec": {"type": "string"},
                "xscale_ra": {"type": "string"},
                "yscale_ra": {"type": "string"},
                "xscale_dec": {"type": "string"},
                "yscale_dec": {"type": "string"},
            },
            "additionalProperties": False,
        }
        self.load_schema(self.schema, is_file=False)

    @classmethod
    def from_config(cls, config, *args, **kwargs):
        instance = super(lvmagp, cls).from_config(config, *args, **kwargs)
        assert isinstance(instance, lvmagp)
        assert isinstance(instance.config, dict)

        return instance
