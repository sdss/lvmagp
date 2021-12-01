import os
import click
from clu.command import Command

from lvmagp.actor.commfunc import *  # noqa: F403
from lvmagp.actor.internalfunc import *  # noqa: F403
from lvmagp.actor.user_parameters import usrpars

from . import parser

test_KHU = True

@parser.command()
#@click.argument("TEL", type=str)
async def test(command: Command,
               telescopes: dict[str, LVMTelescope], eastcameras: dict[str, LVMEastCamera], westcameras: dict[str, LVMWestCamera],
               focusers: dict[str, LVMFocuser], kmirrors: dict[str, LVMKMirror],
               ):
    global test_KHU
    resultpath = "/home/sumin/lvmagp/python/lvmagp/actor/astrometry_result.txt"

    ospassword = "0000"
    resultpath = os.path.dirname(os.path.abspath(__file__)) + "/../astrometry_result.txt"
    timeout = 30
    scalelow = 2
    scalehigh = 3
    radius = 1
    filepath = "/home/sumin/lvmcam/python/lvmcam/assets/2459550/sci.agw-00000075.fits"
    ra_h = 0.7
    dec_d = 41.3



    cmd = "echo %s | sudo -S /usr/local/astrometry/bin/solve-field %s --cpulimit %f --overwrite \
            --downsample 2 --scale-units arcsecperpix --scale-low %f --scale-high %f --ra %f --dec %f \
            --radius %f --no-plots > %s" % (  # noqa: E501
        ospassword,
        filepath,
        timeout,
        scalelow,
        scalehigh,
        ra_h * 15,
        dec_d,
        radius,
        resultpath,
    )

    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    await proc.communicate()

    print("end")
