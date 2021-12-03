# from clu import AMQPClient, CommandStatus
# from cluplus.proxy import Proxy, ProxyException, ProxyPlainMessagException, invoke, unpack

from lvmagp.actor.internalfunc import send_message
import datetime
import numpy as np
import asyncio


# Functions for focuser
class LVMTANInstrument:
    def __init__(self, tel, inst):
        if tel == "test" or inst == "test":
            self.lvmtan = "test.first.focus_stage"
        else:
            self.lvmtan = "lvm." + tel + "." + inst

    async def getposition(self, command, unit="STEPS"):
        cmd = await send_message(
            command,
            self.lvmtan,
            "getPosition %s" % unit,
            returnval=True,
            body="Position",
        )
        return cmd


    async def moveabs(self, command, position, unit='STEPS'):
        cmd = await send_message(command, self.lvmtan, "moveAbsolute %d %s" % (position, unit))
        return cmd

    async def moverel(self, command, position, unit='STEPS'):
        cmd = await send_message(command, self.lvmtan, "moveRelative %d %s" % (position, unit))
        return cmd
'''

    async def moveabs(self, command, position, unit="STEPS"):
        task = asyncio.create_task(
            send_message(
                command, self.lvmtan, "moveabsolute %.4f %s" % (float(position), unit)
            )
        )
        return task

    async def moverel(self, command, position, unit="STEPS"):
        task = asyncio.create_task(
            send_message(
                command, self.lvmtan, "moverelative %.4f %s" % (float(position), unit)
            )
        )
        return task
'''

class LVMFocuser(LVMTANInstrument):
    def __init__(self, tel):
        super().__init__(tel, "foc")
        #print(self.lvmtan)


class LVMKMirror(LVMTANInstrument):
    def __init__(self, tel):
        super().__init__(tel, "km")

    async def cal_traj(self, command):
        currenttime = datetime.datetime.now()
        #cmd = await send_message(command, self.lvmtan, "startProfile %d %s" % (position, unit))
        return currenttime
    '''
    async def startProfile(
            self,
            start_date: datetime.datetime,
            positions: list,
            frequency: int,
            samples_per_segment: int,
            max_error: int,
    '''

class LVMFibsel(LVMTANInstrument):
    def __init__(self):
        super().__init__("spec", "fibsel")


class LVMTelescope:
    def __init__(self, tel):
        if tel == "test":
            self.lvmpwi = "lvm.pwi"
        else:
            self.lvmpwi = "lvm." + tel + ".pwi"

        self.latitude = -999
        self.longitude = -999
        self.rotationangle = -999

        self.scale_matrix = np.matrix([[1,1],   #[x_ra , y_ra ]
                                       [1,1]])  #[x_dec, y_dec]

        self.ag_task = None
        self.ag_break = False

    async def slew_radec2000(self, command, target_ra_h, target_dec_d):
        cmd = await send_message(command,self.lvmpwi,"gotoRaDecJ2000 %f %f" % (target_ra_h, target_dec_d))
        return cmd

    async def reset_offset_radec(self, command):
        await send_message(
            command, self.lvmpwi, "offset --ra_reset"
        )
        await send_message(
            command, self.lvmpwi, "offset --dec_reset"
        )

        return True

    async def offset_radec(self, command, ra_arcsec, dec_arcsec):

        await send_message(
            command, self.lvmpwi, "offset --ra_add_arcsec %f" % ra_arcsec
        )
        await send_message(
            command, self.lvmpwi, "offset --dec_add_arcsec %f" % dec_arcsec
        )

        return True

    async def get_dec2000_deg(self, command):
        dec2000 = await send_message(
            command, self.lvmpwi, "status", returnval=True, body="dec_j2000_degs"
        )
        return dec2000


# Functions for camera
class LVMCamera:
    def __init__(self):
        self.lvmcam = "lvmcam"
        self.cam = "lvmcam"
        self.offset_x = -999
        self.offset_y = -999
        self.pixelscale = -999
        self.rotationangle = -999
        self.lvmcampath = ''

    async def single_exposure(self, command, exptime):
        path = await send_message(
            command, self.lvmcam, "expose %f 1 %s" % (exptime, self.cam), returnval=True, body="PATH"
        )
        return path["0"]

    async def test_exposure(self, command, exptime):
        path = await send_message(
            command, self.lvmcam, "expose -t %f 1 %s" % (exptime, self.cam), returnval=True, body="PATH"
        )
        return path["0"]

class LVMEastCamera(LVMCamera):
    def __init__(self, tel):
        super().__init__()
        self.cam = tel + '.age'

class LVMWestCamera(LVMCamera):
    def __init__(self, tel):
        super().__init__()
        self.cam = tel + '.agw'