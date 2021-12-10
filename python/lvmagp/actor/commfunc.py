import numpy as np
from lvmtipo.site import Site

from lvmagp.actor.internalfunc import send_message


class LVMTANInstrument:
    """
    Class for the instruments using TAN.

    Parameters
    ----------
    tel
        Telescope to which the instrument belongs
    inst
        Type of the instrument
    """

    def __init__(self, tel, inst):
        if tel == "test" or inst == "test":
            self.lvmtan = "test.first.focus_stage"
        else:
            self.lvmtan = "lvm." + tel + "." + inst

    async def getposition(self, command, unit="STEPS"):
        """
        Get current position of device in given unit.

        Parameters
        ----------
        unit
            Unit of position
        """
        cmd = await send_message(
            command,
            self.lvmtan,
            "getPosition %s" % unit,
            returnval=True,
            body="Position",
        )
        return cmd

    async def moveabs(self, command, position, unit="STEPS"):
        """
        Move the device at given absolute position.

        Parameters
        ----------
        position
            Position for the device to be located
        unit
            Unit of position
        """
        cmd = await send_message(
            command, self.lvmtan, "moveAbsolute %d %s" % (position, unit)
        )
        return cmd

    async def moverel(self, command, position, unit="STEPS"):
        """
        Move the device at given relative position.

        Parameters
        ----------
        position
            Position for the device to be located
        unit
            Unit of position
        """
        cmd = await send_message(
            command, self.lvmtan, "moveRelative %d %s" % (position, unit)
        )
        return cmd


"""

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
"""


class LVMFocuser(LVMTANInstrument):
    """
    Class for the focusers

    Parameters
    ----------
    tel
        Telescope to which the focuser belongs
    """

    def __init__(self, tel):
        super().__init__(tel, "foc")
        # print(self.lvmtan)


class LVMKMirror(LVMTANInstrument):
    """
    Class for the K-mirros

    Parameters
    ----------
    tel
        Telescope to which the focuser belongs
    """

    def __init__(self, tel):
        super().__init__(tel, "km")

    async def cal_traj(self, command):
        pass


class LVMFibsel(LVMTANInstrument):
    """
    Class for the fiber selectors

    Parameters
    ----------
    tel
        Telescope to which the focuser belongs
    """

    def __init__(self):
        super().__init__("spec", "fibsel")


class LVMTelescope:
    """
    Class for the telescopes (Planewave mounts)

    Parameters
    ----------
    tel
        The name of the telescope
    """

    def __init__(self, tel, sitename="LCO"):
        if tel == "test":
            self.lvmpwi = "lvm.pwi"
        else:
            self.lvmpwi = "lvm." + tel + ".pwi"

        site = Site(name=sitename)
        self.latitude = site.lat
        self.longitude = site.long

        self.scale_matrix = np.matrix(
            [[1, 1], [1, 1]]  # [x_ra , y_ra ]
        )  # [x_dec, y_dec]

        self.ag_task = None
        self.ag_break = False

    async def slew_radec2000(self, command, target_ra_h, target_dec_d):
        """
        Slew the telescope to given equatorial coordinates whose epoch is J2000.

        Parameters
        ----------
        target_ra_h
            Target right ascension in hours in J2000 epoch
        target_dec_d
            Target declination in degrees in J2000 epoch
        """
        cmd = await send_message(
            command, self.lvmpwi, "gotoRaDecJ2000 %f %f" % (target_ra_h, target_dec_d)
        )
        return cmd

    async def reset_offset_radec(self, command):
        """
        Reset the offset of both axes to zero.
        """
        await send_message(command, self.lvmpwi, "offset --ra_reset")
        await send_message(command, self.lvmpwi, "offset --dec_reset")

        return True

    async def offset_radec(self, command, ra_arcsec, dec_arcsec):
        """
        Give some offset to the mount

        Parameters
        ----------
        ra_arcsec
            Distance to move along right ascension axis in arcseconds
        dec_arcsec
            Distance to move along declination axis in arcseconds
        """
        await send_message(
            command, self.lvmpwi, "offset --ra_add_arcsec %f" % ra_arcsec
        )
        await send_message(
            command, self.lvmpwi, "offset --dec_add_arcsec %f" % dec_arcsec
        )

        return True

    async def get_dec2000_deg(self, command):
        """
        Return the declination (J2000) of current position in degrees
        """
        dec2000 = await send_message(
            command, self.lvmpwi, "status", returnval=True, body="dec_j2000_degs"
        )
        return dec2000


# Functions for camera
class LVMCamera:
    """
    Class for the FLIR guide cameras
    """

    def __init__(self):
        self.lvmcam = "lvmcam"
        self.cam = "lvmcam"
        self.offset_x = -999
        self.offset_y = -999
        self.pixelscale = -999
        self.rotationangle = -999
        self.lvmcampath = ""

    async def single_exposure(self, command, exptime):
        """
        Take a single exposure

        Parameters
        ----------
        exptime
            Exposure time
        """
        path = await send_message(
            command,
            self.lvmcam,
            "expose %f 1 %s" % (exptime, self.cam),
            returnval=True,
            body="PATH",
        )
        return path["0"]

    async def test_exposure(self, command, exptime):
        """
        Take a test exposure using ``-t`` option of lvmcam.
        The image file (Temp.fits) is overwritten whenever this command is executed.

        Parameters
        ----------
        exptime
            Exposure time
        """
        path = await send_message(
            command,
            self.lvmcam,
            "expose -t %f 1 %s" % (exptime, self.cam),
            returnval=True,
            body="PATH",
        )
        return path["0"]


class LVMEastCamera(LVMCamera):
    """
    Class for the FLIR guide cameras installed in east side

    Parameters
    ----------
    tel
        Telescope to which the camera belongs
    """

    def __init__(self, tel):
        super().__init__()
        self.cam = tel + ".age"


class LVMWestCamera(LVMCamera):
    """
    Class for the FLIR guide cameras installed in west side

    Parameters
    ----------
    tel
        Telescope to which the camera belongs
    """

    def __init__(self, tel):
        super().__init__()
        self.cam = tel + ".agw"
