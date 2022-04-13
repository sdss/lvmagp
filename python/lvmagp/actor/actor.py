from __future__ import absolute_import, annotations, division, print_function

from logging import DEBUG

from sdsstools.logger import StreamFormatter  
from sdsstools import get_logger, read_yaml_file
from sdsstools.logger import SDSSLogger

from clu.actor import AMQPActor

from .commands  import parser

from lvmagp import __version__

from lvm.actors import lvm

from lvmagp.guide import GuideState
from lvm.tel.focus import Focus

__all__ = ["LvmagpActor"]


SUBSYSTEMS=0

class LvmagpActor(AMQPActor):
    """AGP actor.
    In addition to the normal arguments and keyword parameters for
    `~clu.actor.AMQPActor`, the class accepts the following parameters.
    """
    
    parser = parser
    
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, version=__version__, **kwargs)

        self.guide_state = GuideState()
        self.focus = None
        
        self.schema = {
                    "type": "object",
                    "properties": {
                     },
                     "additionalProperties": True,
        }

        self.load_schema(self.schema, is_file=False)

        self.parser_args = [ None ]

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
        
        telsubsystems = await lvm.from_string(self.config["ag"]["system"], self)
        self.parser_args[SUBSYSTEMS] = telsubsystems
        self.focus = Focus(telsubsystems)


        self.log.debug("Start done")


    async def stop(self):
        """Stop actor."""
        await super().stop()

        self.log.debug("Stop done")
