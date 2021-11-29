import os
import click
from clu.command import Command

from lvmagp.actor.commfunc import *  # noqa: F403
from lvmagp.actor.internalfunc import *  # noqa: F403
from lvmagp.actor.user_parameters import usrpars

from . import parser

@parser.group()
def guide(*args):
    pass


@guide.command()
@click.argument("TEL", type=str)
async def start(command: Command,
                telescopes: dict[str, LVMTelescope], eastcameras: dict[str, LVMEastCamera],
                westcameras: dict[str, LVMWestCamera],
                focusers: dict[str, LVMFocuser], kmirrors: dict[str, LVMKMirror],
                tel: str):


    global tasklist
    global breaklist
    tasklist = [0, 0, 0, 0]
    breaklist = [False, False, False, False]

    try:
        if tel == 'sci':
            tasklist[0] = asyncio.wait_for(autoguide_supervisor(command, telescopes, eastcameras,
                westcameras, focusers, kmirrors, tel), timeout=3600)
            await tasklist[0]
        elif tel == 'skye':
            tasklist[1] = asyncio.wait_for(autoguide_supervisor(command, telescopes, eastcameras,
                westcameras, focusers, kmirrors, tel), timeout=3600)
            await tasklist[1]
        elif tel == 'skyw':
            tasklist[2] = asyncio.wait_for(autoguide_supervisor(command, telescopes, eastcameras,
                westcameras, focusers, kmirrors, tel), timeout=3600)
            await tasklist[2]
        elif tel == 'spec':
            tasklist[3] = asyncio.wait_for(autoguide_supervisor(command, telescopes, eastcameras,
                westcameras, focusers, kmirrors, tel), timeout=3600)
            await tasklist[3]
        else:
            return command.fail("Wrong telescope name")
    except asyncio.TimeoutError:
        command.error("Autoguide timeout")


@guide.command()
@click.argument("TEL", type=str)
async def stop(command: Command, tel: str):
    if tel == 'sci':
        breaklist[0] = True
    elif tel == 'skye':
        breaklist[1] = True
    elif tel == 'skyw':
        breaklist[2] = True
    elif tel == 'phot':
        breaklist[3] = True
    else:
        return command.fail("Wrong telescope name")


async def autoguide_supervisor(command, telescopes: dict[str, LVMTelescope], eastcameras: dict[str, LVMEastCamera],
                      westcameras: dict[str, LVMWestCamera], focusers: dict[str, LVMFocuser], kmirrors: dict[str, LVMKMirror], tel):

    # initposition, initflux = await register_guide_stars(command, telescopes, eastcameras,
    #                 westcameras, focusers, kmirrors, tel)
    # while 1:
    #    await autoguiding(command, telescopes, eastcameras,
    #                 westcameras, focusers, kmirrors, tel, initposition, initflux)

    i = 0
    while 1:
        command.info("%s %d" % (tel, i))
        i = i + 1
        await asyncio.sleep(8)

        if tel == 'sci' and tasklist[0]!=0 and breaklist[0] is True:
            tasklist[0] = 0
            breaklist[0] = False
            break
        elif tel == 'skye' and tasklist[1]!=0 and breaklist[1] is True:
            tasklist[1] = 0
            breaklist[1] = False
            break
        elif tel == 'skyw' and tasklist[2]!=0 and breaklist[2] is True:
            tasklist[2] = 0
            breaklist[2] = False
            break
        elif tel == 'phot' and tasklist[3]!=0 and breaklist[3] is True:
            tasklist[3] = 0
            breaklist[3] = False
            break

    command.info('Guide stopped')


''' Here is old version using task.cancle
@guide.command()
@click.argument("TEL", type=str)
async def start(command: Command, tel: str):
    
    exptime = 3  # in seconds
    pixelscale = 0.5 # in arcsec/pixel
    halfboxsize = 15 # 1/2 of box in pixel
    min_snr = 5 # minimum star SNR

    ra_agr = 0.8
    ra_hys = 0.2
    dec_agr = 0.8
    min_dist = 0.3 #in pixel

    lvmcampath = ''

    # safety check?
    tel1 = LVMTelescope(tel)
    cam1 = LVMCamera(tel + "e")
    cam2 = LVMCamera(tel + "w")
    cam1 = LVMCamera("test")  # for lab testing
    
    global tasklist
    tasklist = [0,0,0,0]
    
    try:
        if tel == 'sci':
            tasklist[0] = asyncio.create_task(autoguide_supervisor(command, tel))
            await tasklist[0]
        elif tel == 'skye':
            tasklist[1] = asyncio.create_task(autoguide_supervisor(command, tel))
            await tasklist[1]
        elif tel == 'skyw':
            tasklist[2] = asyncio.create_task(autoguide_supervisor(command, tel))
            await tasklist[2]
        elif tel == 'phot':
            tasklist[3] = asyncio.create_task(autoguide_supervisor(command, tel))
            await tasklist[3]
        else:
            return command.fail("Wrong telescope name")
    
    except asyncio.CancelledError:
        command.info("cancelled_main")


@guide.command()
@click.argument("TEL", type=str)
async def stop(command: Command, tel: str):
    if tel == 'sci':
        tasklist[0].cancel()
    elif tel == 'skye':
        tasklist[1].cancel()
    elif tel == 'skyw':
        tasklist[2].cancel()
    elif tel == 'phot':
        tasklist[3].cancel()
    else:
        return command.fail("Wrong telescope name")

async def autoguide_supervisor(command, tel):
    lvmcampath = ''

    try:
        i = 0
        while 1:
            command.info("%d" % i)
            i=i+1
            await asyncio.sleep(5)

            if i==5:
                break

        
        #initposition, initflux = await register_guide_stars(command, tel)
        #while 1:
        #    await autoguiding(command,tel, initposition, initflux)
        
    except asyncio.CancelledError:
        # Something to abort exposure ..
        command.info('Guide stopped')
        raise
'''
async def register_guide_stars(command, telescopes: dict[str, LVMTelescope], eastcameras: dict[str, LVMEastCamera],
                      westcameras: dict[str, LVMWestCamera], focusers: dict[str, LVMFocuser], kmirrors: dict[str, LVMKMirror], tel):

    command.info("Taking image...")
    # take an image for astrometry
    try:
        imgcmd = await eastcameras[tel].single_exposure(command, usrpars.ag_exptime)
        '''
            imgcmd = []
            imgcmd.append(cam1.single_exposure(command, exptime))
            imgcmd.append(cam2.single_exposure(command, exptime))
            guideimgpath = await asyncio.gather(*imgcmd)
        '''
    except Exception as e:
        return command.fail(fail="Camera error")

    pwd = os.path.dirname(os.path.abspath(__file__))
    agpwd = pwd + "/../../../../"
    # Here lvmcam path and naming rule for finding latest guide image..

    guideimgpath = (
            agpwd + "testimg/focus_series/synthetic_image_median_field_5s_seeing_02.5.fits"
    )  # noqa: E501
    guideimg = GuideImage(guideimgpath)  # noqa: F405
    starposition = guideimg.findstars()
    starflux = guideimg.calflux()
    return starposition, starflux


async def autoguiding(command, telescopes: dict[str, LVMTelescope], eastcameras: dict[str, LVMEastCamera],
                      westcameras: dict[str, LVMWestCamera], focusers: dict[str, LVMFocuser], kmirrors: dict[str, LVMKMirror],
                      tel, initposition, initflux):

    fluxtolerance = 0.2 # tolerance for flux variation of guide star

    agressiveness = 0.8
    #ra_hys = 0.2
    min_dist = 0.3  # in pixel

    initposition = np.array(initposition)

    starposition, starflux = await register_guide_stars(command, telescopes, eastcameras,
                westcameras, focusers, kmirrors, tel)

    if np.abs(np.mean(1-np.array(starflux)/np.array(initflux))) > usrpars.ag_flux_tolerancefluxtolerance:
        return command.error("Star flux variation is too large.")

    offset = np.mean(np.array(starposition) - np.array(initposition), axis=0) # in x,y [pixel]
    offset_arcsec = offset*eastcameras[tel].pixelscale # in x,y(=ra,dec) [arcsec]

    if (np.sqrt(offset[0]**2+offset[1]**2)) > min_dist:
        await telescopes[tel].offset_radec(command, *offset_arcsec)
        return offset_arcsec

    else:
        return [0.,0.]