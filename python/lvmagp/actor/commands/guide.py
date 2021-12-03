import os
import click
from clu.command import Command

from lvmagp.actor.commfunc import *  # noqa: F403
from lvmagp.actor.internalfunc import *  # noqa: F403
from lvmagp.actor.user_parameters import usrpars

from . import parser

question = "Is this develop branch?"

KHU_inner_test = True

@parser.group()
def guide(*args):
    pass


@guide.command()
@click.argument("TEL", type=str)
@click.option("--useteldata", type=float, is_flag=True)
async def start(command: Command,
                telescopes: dict[str, LVMTelescope], eastcameras: dict[str, LVMEastCamera],
                westcameras: dict[str, LVMWestCamera],
                focusers: dict[str, LVMFocuser], kmirrors: dict[str, LVMKMirror],
                tel: str, useteldata: bool):
    """
    Start the autoguide sequence.

    Parameters
    ----------
    tel
        Telescope to autoguide
    useteldata
        If ``useteldata`` is flagged, the sequence will use the pixel scale and rotation angle from LVMTelescope.
        Otherwise, the sequence will get pixel scale from LVMCamera and it assumes that the camera is north-oriented.
    """

    if tel in telescopes:
        try:
            telescopes[tel].ag_task = asyncio.wait_for(autoguide_supervisor(command, telescopes, eastcameras,
                    westcameras, focusers, kmirrors, tel, useteldata), timeout=3600)
            await telescopes[tel].ag_task

        except asyncio.TimeoutError:
            command.error("Autoguide timeout")

        finally:
            telescopes[tel].ag_task = None
    else:
        return command.fail(text="Telescope '%s' does not exist" % tel)

    return command.finish('Guide stopped')


@guide.command()
@click.argument("TEL", type=str)
async def stop(command: Command, telescopes: dict[str, LVMTelescope], eastcameras: dict[str, LVMEastCamera],
                      westcameras: dict[str, LVMWestCamera], focusers: dict[str, LVMFocuser], kmirrors: dict[str, LVMKMirror], tel: str):
    """
    Stop the autoguide sequence.

    Parameters
    ----------
    tel
        Telescope to stop autoguide
    """
    if tel in telescopes:
        if telescopes[tel].ag_task is not None:
            telescopes[tel].ag_break = True
        else:
            return command.fail(text="There is no autoguiding loop for telescope '%s'" % tel)
    else:
        return command.fail(text="Telescope '%s' does not exist" % tel)

    return command.finish()


@guide.command()
@click.argument("TEL", type=str)
async def calibration(command: Command, telescopes: dict[str, LVMTelescope], eastcameras: dict[str, LVMEastCamera],
                      westcameras: dict[str, LVMWestCamera], focusers: dict[str, LVMFocuser], kmirrors: dict[str, LVMKMirror],
                      tel: str):
    """
    Run calibration sequence to calculate the transformation from the equatorial coordinates to the xy coordinates of the image.

    Parameters
    ----------
    tel
        Telescope to be calibrated
    """
    global KHU_inner_test
    offset_per_step = usrpars.ag_cal_offset_per_step
    num_step = usrpars.ag_cal_num_step

    if tel not in telescopes:
        return command.fail(text="Telescope '%s' does not exist" % tel)

    xpositions, ypositions = [], []

    initposition, initflux = await find_guide_stars(command, telescopes, eastcameras, westcameras, focusers, kmirrors, tel)
    xpositions.append(initposition[:, 0])
    ypositions.append(initposition[:, 1])

    # dec axis calibration
    for step in range(1,num_step+1):
        await telescopes[tel].offset_radec(command, 0, offset_per_step)
        position, flux = await find_guide_stars(command, telescopes, eastcameras, westcameras, focusers,
                                                       kmirrors, tel)
        xpositions.append(position[:, 0])
        ypositions.append(position[:, 1])

    await telescopes[tel].offset_radec(command, 0, -num_step*offset_per_step)

    xpositions = np.array(xpositions) - xpositions[0]
    ypositions = np.array(ypositions) - ypositions[0]
    xscale_dec = np.sum(xpositions/np.arange(num_step+1))/(num_step)  # displacement along x-axis by ra offset in pixel per arcsecond. exclude the first index (0,0)
    yscale_dec = np.sum(ypositions/np.arange(num_step+1))/(num_step)  # exclude the first index (0,0)

    # ra axis calibration
    xpositions = [initposition[:, 0]]
    ypositions = [initposition[:, 1]]

    for step in range(1,num_step+1):
        await telescopes[tel].offset_radec(command, offset_per_step, 0)
        position, flux = await find_guide_stars(command, telescopes, eastcameras, westcameras, focusers,
                                                       kmirrors, tel)
        xpositions.append(position[:, 0])
        ypositions.append(position[:, 1])

    await telescopes[tel].offset_radec(command, -num_step*offset_per_step, 0)

    decj2000_deg = telescopes[tel].get_dec2000_deg()

    xpositions = np.array(xpositions) - xpositions[0]
    ypositions = np.array(ypositions) - ypositions[0]
    xscale_ra = np.sum(xpositions*np.arange(num_step+1))/(num_step)/np.cos(decj2000_deg)  # exclude the first index (0,0)
    yscale_ra = np.sum(ypositions*np.arange(num_step+1))/(num_step)/np.cos(decj2000_deg)  # exclude the first index (0,0)

    telescopes[tel].scale_matrix = np.matrix([[xscale_ra, yscale_ra],[xscale_dec, yscale_dec]])
    return command.finish(xscale_ra="%.3f pixel/arcsec"%xscale_ra, yscale_ra="%.3f pixel/arcsec"%yscale_ra,
                          xscale_dec="%.3f pixel/arcsec"%xscale_dec, ysclae_dec="%.3f pixel/arcsec"%yscale_dec)


async def autoguide_supervisor(command, telescopes: dict[str, LVMTelescope], eastcameras: dict[str, LVMEastCamera],
                      westcameras: dict[str, LVMWestCamera], focusers: dict[str, LVMFocuser], kmirrors: dict[str, LVMKMirror], tel, useteldata):
    """
    Manage the autoguide sequence.
    It starts real autoguide loop and keeps it until the break signal comes.

    Parameters
    ----------
    tel
        Telescope to autoguide
    useteldata
        If ``useteldata`` is flagged, the sequence will use the pixel scale and rotation angle from LVMTelescope.
        Otherwise, the sequence will get pixel scale from LVMCamera and it assumes that the camera is north-oriented.
    """
    global KHU_inner_test
    if KHU_inner_test:
        i = 0
    else:
        initposition, initflux = await find_guide_stars(command, telescopes, eastcameras,
                                                        westcameras, focusers, kmirrors, tel)

    while 1:
        if KHU_inner_test:
            command.info("%s %d" % (tel, i))
            i = i + 1
            await asyncio.sleep(8)
        else:
            await autoguiding(command, telescopes, eastcameras,
                              westcameras, focusers, kmirrors, tel, initposition, initflux, useteldata)

        if telescopes[tel].ag_break is True:
            telescopes[tel].ag_break = False
            break

    return True


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
                               tel, positionguess=None):
    """
    Expose an image, and find three guide stars from the image.
    Also calculate the center coordinates and flux of found stars.

    Parameters
    ----------
    tel
        Telescope to autoguide
    positionguess
        Initial guess of guidestar position. It should be given in np.ndarray as [[x1, y1], [x2, y2], ...]
        If ``positionguess`` is not None, ``find_guide_stars`` only conduct center finding based on ``positionguess`` without finding new stars.
    """
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
                      tel, initposition, initflux, useteldata):
    """
    Expose an image, and calculate offset from the image and initial values.
    Compensate the offset.

    Parameters
    ----------
    tel
        Telescope to autoguide
    initposition
        Position of guide stars when the autoguide is started
    initflux
        Flux of guide stars when the autoguide is started
    positionguess
        Initial guess of guidestar position. It should be given in np.ndarray as [[x1, y1], [x2, y2], ...]
        If ``positionguess`` is not None, ``find_guide_stars`` only conduct center finding based on ``positionguess`` without finding new stars.
    """
    starposition, starflux = await find_guide_stars(command, telescopes, eastcameras,
                westcameras, focusers, kmirrors, tel, positionguess=initposition)

    if np.abs(np.average(starflux/initflux - 1), weight=np.log10(initflux)) > usrpars.ag_flux_tolerance:
        return command.error("Star flux variation is too large.")

    offset = np.mean(starposition - initposition, axis=0) # in x,y [pixel]

    if useteldata:
        offset_arcsec = np.matmul(telescopes[tel].scale_matrix.I, offset.T)  # in x,y(=ra,dec) [arcsec]
        offset_arcsec = np.array(offset_arcsec)
    else:
        offset_arcsec = offset * westcameras[tel].pixelscale  # in x,y(=ra,dec) [arcsec]

    decj2000_deg = telescopes[tel].get_dec2000_deg()
    offset_arcsec[0] = offset_arcsec[0]/np.cos(decj2000_deg)

    if (np.sqrt(offset[0]**2+offset[1]**2)) > usrpars.ag_min_offset:
        print("compensate: ra %.2f arcsec dec %.2f arcsec   x %.2f pixel y %.2f pixel" %
              (offset_arcsec[0], offset_arcsec[1], offset[0], offset[1]))
        await telescopes[tel].offset_radec(command, *offset_arcsec)
        return offset_arcsec

    else:
        return [0.,0.]