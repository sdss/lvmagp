from clu.command import Command

from lvmagp.actor.commfunc import (LVMEastCamera, LVMFibsel,  # noqa: F401
                                   LVMFocuser, LVMKMirror, LVMTANInstrument,
                                   LVMTelescope, LVMWestCamera)
from lvmagp.actor.internalfunc import GuideImage
from lvmagp.actor.user_parameters import usrpars  # noqa: F401
import numpy as np
#from . import parser

import sys
import uuid
from cluplus.proxy import Proxy, ProxyPartialInvokeException, invoke, unpack
from clu import AMQPClient, CommandStatus


# import logging
# from sdsstools import get_logger


test_KHU = True

# log = get_logger("sdss-lvmagp")
# log.sh.setLevel(logging.DEBUG)


#@parser.command()
# @click.argument("TEL", type=str)
async def test(
    command: Command,
    telescopes: dict[str, LVMTelescope],
    eastcameras: dict[str, LVMEastCamera],
    westcameras: dict[str, LVMWestCamera],
    focusers: dict[str, LVMFocuser],
    kmirrors: dict[str, LVMKMirror],
):

    '''
    try:
        amqpc = AMQPClient(name=f"{sys.argv[0]}.proxy-{uuid.uuid4().hex[:8]}")
        await amqpc.start()
        tcs = Proxy(amqpc, 'lvm.sci.foc')
        await tcs.start()
    except Exception as e:
        amqpc.log.error(f"Exception: {e}")

    try:
        # sequential
        result = await tcs.ping()
        #await tcs.ping()

        # parallel
        #await invoke(
        #    lvm_sci_pwi.ping(),
        #    lvm_sci_foc.ping()
        #)

    except Exception as e:
        amqpc.log.error(f"Exception: {e}")

    #result = await tcs.ping()
    command.finish(result["text"])
    '''
    filepath = \
        "/home/hojae/Desktop/lvmagp/testimg/autoguide_sample/assets/lvm/sci/agw/20211203/lvm.sci.agw-00000170.fits"
    guideimg1 = GuideImage(filepath)

    filepath = \
        "/home/hojae/Desktop/lvmagp/testimg/autoguide_sample/assets/lvm/sci/agw/20211203/lvm.sci.agw-00000170.fits"
    guideimg2 = GuideImage(filepath)

    pos = guideimg1.findstars()
    print(pos, guideimg1.guidestarflux)

    guideimg2.guidestarposition = pos
    guideimg2.update_guidestar_properties()
    starposition = guideimg2.guidestarposition
    print(starposition, guideimg2.guidestarflux)


def test1():
    filepath = \
        "/home/hojae/Desktop/lvmagp/testimg/autoguide_sample/assets/lvm/sci/agw/20211203/lvm.sci.agw-00000170.fits"
    guideimg1 = GuideImage(filepath)

    filepath = \
        "/home/hojae/Desktop/lvmagp/testimg/autoguide_sample/assets/lvm/sci/agw/20211203/lvm.sci.agw-00000172.fits"
    guideimg2 = GuideImage(filepath)

    global KHU_inner_test
    offset_per_step = usrpars.ag_cal_offset_per_step
    num_step = usrpars.ag_cal_num_step

    decj2000_deg = 60.0

    xpositions, ypositions = [], []

    xpositions = [[100, 500, 1200]]
    ypositions = [[40, 150, 700]]

    # dec axis calibration
    xpositions = [[100, 500, 1200], [101.1, 501.0, 1201.2], [102.1, 502.1, 1202.3], [103.2, 503.5, 1203.1]]
    ypositions = [[40, 150, 700], [42.2, 152.0, 701.9], [44.0, 153.8, 703.8], [45.9, 155.9, 706.3]]

    xpositions = np.array(xpositions) - xpositions[0]
    ypositions = np.array(ypositions) - ypositions[0]
    xscale_dec = (
            np.average(xpositions[1:] / np.array([[i] * 3 for i in range(1, num_step + 1)])) /
            offset_per_step
    )  # displacement along x-axis by ra offset in pixel per arcsec. exclude the first index (0,0)
    yscale_dec = (
            np.average(ypositions[1:] / np.array([[i] * 3 for i in range(1, num_step + 1)])) /
            offset_per_step
    )  # exclude the first index (0,0)

    # ra axis calibration
    xpositions = [[100, 500, 1200]]
    ypositions = [[40, 150, 700]]

    xpositions = [[100, 500, 1200], [102.2, 502.0, 1201.9], [104.0, 503.8, 1203.8], [105.9, 505.9, 1206.3]]
    ypositions = [[40, 150, 700], [38.9, 148.8, 699.1], [38.0, 147.7, 698.1], [37.1, 147.1, 696.9]]

    xpositions = np.array(xpositions) - xpositions[0]
    ypositions = np.array(ypositions) - ypositions[0]
    xscale_ra = (
            np.average(xpositions[1:] / np.array([[i] * 3 for i in range(1, num_step + 1)])) /
            offset_per_step
    )  # exclude the first index (0,0)
    yscale_ra = (
            np.average(ypositions[1:] / np.array([[i] * 3 for i in range(1, num_step + 1)])) /
            offset_per_step
    )  # exclude the first index (0,0)

    #scale_matrix = np.linalg.inv(np.array(
    #    [[xscale_ra, xscale_dec], [yscale_ra, yscale_dec]]
    #))
    scale_matrix = np.linalg.inv(np.array(
        [[0.2, 0.4], [0.4, -0.2]]
    ))

    offset = np.array([0.4, 0.2])
    offset_arcsec = np.dot(
        scale_matrix, offset
    )  # in x,y(=ra,dec) [arcsec]
    correction_arcsec = -np.array(offset_arcsec)[0]

    return scale_matrix, offset_arcsec



if (__name__ == "__main__"):
    scale_matrix, offset_arcsec = test1()
    print(scale_matrix)
    print (offset_arcsec)