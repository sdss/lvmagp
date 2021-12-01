import os
import click
from clu.command import Command

from lvmagp.actor.commfunc import *  # noqa: F403
from lvmagp.actor.internalfunc import *  # noqa: F403
from lvmagp.actor.user_parameters import usrpars

from . import parser

KHU_inner_test = True

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

    if tel in telescopes:
        try:
            telescopes[tel].ag_task = asyncio.wait_for(autoguide_supervisor(command, telescopes, eastcameras,
                    westcameras, focusers, kmirrors, tel), timeout=3600)
            await telescopes[tel].ag_task

        except asyncio.TimeoutError:
            command.error("Autoguide timeout")

        finally:
            telescopes[tel].ag_task = None
    else:
        return command.fail(text="Telescope '%s' does not exist" % tel)


@guide.command()
@click.argument("TEL", type=str)
async def stop(command: Command, telescopes: dict[str, LVMTelescope], eastcameras: dict[str, LVMEastCamera],
                      westcameras: dict[str, LVMWestCamera], focusers: dict[str, LVMFocuser], kmirrors: dict[str, LVMKMirror], tel: str):
    if tel in telescopes:
        if telescopes[tel].ag_task is not None:
            telescopes[tel].ag_break = True
        else:
            return command.fail(text="There is no autoguiding loop for telescope '%s'" % tel)
    else:
        return command.fail(text="Telescope '%s' does not exist" % tel)

    return True


async def autoguide_supervisor(command, telescopes: dict[str, LVMTelescope], eastcameras: dict[str, LVMEastCamera],
                      westcameras: dict[str, LVMWestCamera], focusers: dict[str, LVMFocuser], kmirrors: dict[str, LVMKMirror], tel):

    global KHU_inner_test
    if KHU_inner_test:
        i = 0
    else:
        initposition, initflux = await find_guide_stars(command, telescopes, eastcameras,
                                                        westcameras, focusers, kmirrors, tel, register=True)

    while 1:
        if KHU_inner_test:
            command.info("%s %d" % (tel, i))
            i = i + 1
            await asyncio.sleep(8)
        else:
            await autoguiding(command, telescopes, eastcameras,
                              westcameras, focusers, kmirrors, tel, initposition, initflux)

        if telescopes[tel].ag_break is True:
            telescopes[tel].ag_break = False
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
async def find_guide_stars(command, telescopes: dict[str, LVMTelescope], eastcameras: dict[str, LVMEastCamera],
                               westcameras: dict[str, LVMWestCamera], focusers: dict[str, LVMFocuser], kmirrors: dict[str, LVMKMirror],
                               tel, positionguess=None)
    global KHU_inner_test
    command.info("Taking image...")
    # take an image for astrometry
    try:
        imgcmd = []
        imgcmd.append(westcameras[tel].single_exposure(command, usrpars.ag_exptime))

        if not KHU_inner_test:
            imgcmd.append(eastcameras[tel].single_exposure(command, usrpars.ag_exptime))

        guideimgpath = await asyncio.gather(*imgcmd)

    except Exception as e:
        return command.fail(fail="Camera error")

    westguideimg = GuideImage(guideimgpath[0])
    eastguideimg = westguideimg

    if not KHU_inner_test:
        eastguideimg = GuideImage(guideimgpath[1])

    if positionguess is None:
        starposition = westguideimg.findstars()
    else:
        westguideimg.guidestarposition = positionguess
        westguideimg.update_guidestar_properties()
        starposition = westguideimg.guidestarposition
    starflux = westguideimg.guidestarflux

    return starposition, starflux


async def autoguiding(command, telescopes: dict[str, LVMTelescope], eastcameras: dict[str, LVMEastCamera],
                      westcameras: dict[str, LVMWestCamera], focusers: dict[str, LVMFocuser], kmirrors: dict[str, LVMKMirror],
                      tel, initposition, initflux):

    starposition, starflux = await find_guide_stars(command, telescopes, eastcameras,
                westcameras, focusers, kmirrors, tel, positionguess=initposition)

    if np.abs(np.average(starflux/initflux - 1), weight=np.log10(initflux)) > usrpars.ag_flux_tolerance:
        return command.error("Star flux variation is too large.")

    offset = np.mean(starposition - initposition, axis=0) # in x,y [pixel]
    offset_arcsec = offset*eastcameras[tel].pixelscale # in x,y(=ra,dec) [arcsec]

    if (np.sqrt(offset[0]**2+offset[1]**2)) > usrpars.ag_min_offset:
        await telescopes[tel].offset_radec(command, *offset_arcsec)
        return offset_arcsec

    else:
        return [0.,0.]