from __future__ import absolute_import, annotations, division, print_function

from clu.actor import AMQPActor

from .commands import parser as lvm_command_python

from lvmagp.actor.commfunc import LVMTANInstrument,LVMTelescope,LVMEastCamera,LVMWestCamera,LVMFibsel,LVMFocuser,LVMKMirror


# from scpactor import __version__

__all__ = ["lvmagp"]
tel_list = ['sci', 'skye', 'skyw', 'spec']


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
        telescopes: tuple[LVMTelescope, ...] = (),
        eastcameras: tuple[LVMEastCamera, ...] = (),
        westcameras: tuple[LVMEastCamera, ...] = (),
        focusers: tuple[LVMFocuser, ...] = (),
        kmirrors: tuple[LVMKMirror, ...] = (),
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.schema = {
            "type": "object",
            "properties": {
                "fail" : {"type": "string"},
                "Img_ra2000": {"type": "string"},
                "Img_dec2000": {"type": "string"},
                "Img_pa": {"type": "string"},
                "offset_ra": {"type": "string"},
                "offset_dec": {"type": "string"},
            },
            "additionalProperties": False,
        }
        self.load_schema(self.schema, is_file=False)

        self.telescopes = {s.name: s for s in telescopes}
        self.eastcameras = {s.name: s for s in eastcameras}
        self.westcameras = {s.name: s for s in westcameras}
        self.focusers = {s.name: s for s in focusers}
        self.kmirrors = {s.name: s for s in kmirrors}

    @classmethod
    def from_config(cls, config, *args, **kwargs):
        instance = super(lvmagp, cls).from_config(config, *args, **kwargs)
        assert isinstance(instance, lvmagp)
        assert isinstance(instance.config, dict)

        for (ctrname, ctr) in instance.config.items():
            if ctrname in tel_list:
                #print(ctrname, ctr)
                instance.telescopes.update({ctrname: LVMTelescope(ctrname)})
                instance.telescopes[ctrname].latitude = ctr['tel']['latitude']
                instance.telescopes[ctrname].longitude = ctr['tel']['longitude']

                instance.eastcameras.update({ctrname: LVMEastCamera(ctrname)})
                instance.eastcameras[ctrname].pixelscale = ctr['age']['pixelscale']
                instance.eastcameras[ctrname].offset_x = ctr['age']['offset_x']
                instance.eastcameras[ctrname].offset_y = ctr['age']['offset_y']

                instance.westcameras.update({ctrname: LVMWestCamera(ctrname)})
                instance.westcameras[ctrname].pixelscale = ctr['agw']['pixelscale']
                instance.westcameras[ctrname].offset_x = ctr['agw']['offset_x']
                instance.westcameras[ctrname].offset_y = ctr['agw']['offset_y']

                instance.focusers.update({ctrname: LVMFocuser(ctrname)})

                instance.kmirrors.update({ctrname: LVMKMirror(ctrname)})

                #print(ctrname,ctr)

        #print(instance.telescopes)

        instance.parser_args = [instance.telescopes, instance.eastcameras, instance.westcameras, instance.focusers, instance.kmirrors]
        return instance