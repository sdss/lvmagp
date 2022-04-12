from __future__ import absolute_import, annotations, division, print_function

from clu.actor import AMQPActor

from .commands import command_parser as lvm_command_python


# from scpactor import __version__

__all__ = ["lvmagp"]


class LvmagpActor(AMQPActor):
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
                     },
                     "additionalProperties": True,
        }

        self.load_schema(self.schema, is_file=False)

        if kwargs['verbose']:
            self.log.sh.setLevel(DEBUG)
            self.log.sh.formatter = StreamFormatter(fmt='%(asctime)s %(name)s %(levelname)s %(filename)s:%(lineno)d: \033[1m%(message)s\033[21m') 

    @classmethod
    def from_config(cls, config, *args, **kwargs):
        instance = super(LvmagpActor, cls).from_config(config, *args, **kwargs)

        assert isinstance(instance, LvmagpActor)
        assert isinstance(instance.config, dict)

        return instance

    async def start(self):
        """Start actor."""
        await super().start()

        self.log.debug("Start done")
        
    async def stop(self):
        """Stop actor."""
        await super().stop()

        self.log.debug("Stop done")
