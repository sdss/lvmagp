from __future__ import absolute_import, annotations, division, print_function

from logging import DEBUG

from sdsstools.logger import StreamFormatter  
from sdsstools import get_logger, read_yaml_file
from sdsstools.logger import SDSSLogger

from clu.actor import AMQPActor

from lvmtipo.actors import lvm

from lvmagp import __version__

from .commands  import parser
from .statemachine import ActorStateMachine, ActorState

from cluplus.proxy import Proxy

from lvmagp.focus import Focus
from lvmagp.guide.worker import GuiderWorker


__all__ = ["LvmagpActor"]


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

        self.statemachine = ActorStateMachine()
        self.telsubsystems = None
        self.guider = None
        self.focus = None

        
        self.schema = { #TODO add schema
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

        Proxy.setDefaultAmqpc(self)
        
        self.telsubsystems = await lvm.from_string(self.config["ag"]["system"]).start()
        self.guider = GuiderWorker(self.telsubsystems, self.statemachine, logger=self.log)
        self.focus = Focus(self.telsubsystems, level=DEBUG)

        self.log.debug("Start done")


    async def stop(self):
        """Stop actor."""
        await super().stop()

        self.log.debug("Stop done")
