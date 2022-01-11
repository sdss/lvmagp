import sys
import uuid

import numpy as np
from clu import AMQPClient
from cluplus.proxy import Proxy, invoke
from lvmtipo.site import Site

from lvmagp.actor.internalfunc import GuideImage, findfocus, send_message
from lvmagp.actor.user_parameters import temp_vs_focus, usrpars
from lvmagp.exceptions import LvmagpFocuserError


class LVMFocuser:
    """
    Class for the focusers

    Parameters
    ----------
    tel
        Telescope unit to which the focuser belongs
    amqpc
        AMQP client to be used for actor communication
    """

    def __init__(self, tel, amqpc):
        self.amqpc = amqpc
        self._foc = None

        try:
            self._foc = Proxy(self.amqpc, "lvm." + tel + ".foc")
            self._foc.start()

        except Exception as e:
            self.amqpc.log.error(f"Exception: {e}")

    def focusoffset(self, delta_f=None):
        """
        Apply a relative telescope focus offset.

        Parameters:
            delta_f (float): focus offset value in steps
        """

        try:
            self._foc.moveRelative(delta_f, unit="STEPS")

        except Exception as e:
            self.amqpc.log.error(f"Exception: {e}")
            return False

        return True

    def focus(self, value=None, temperature=None):
        """
        Move focus to a particular value or a first guess given a temperature

        Parameters:
            value (float): if provided, focus stage moves to this step value
            temperature (float): if 'value' is not provided or 'value=None',
            focus stage moves to best guess based on focus vs temperature model
        Returns:
            None
        """
        try:
            if value is not None:
                self._foc.moveAbsolute(value, unit="STEPS")
            else:
                temp_value = temp_vs_focus(temperature=temperature)
                self._foc.moveAbsolute(temp_value, unit="STEPS")

        except Exception as e:
            self.amqpc.log.error(f"Exception: {e}")

    def getfocusposition(self, unit="STEPS"):
        """
        Get current position of device in given unit.

        Parameters
        ----------
        unit
            Unit of position
        """
        try:
            position = self._foc.getPosition(unit=unit)["Position"]
        except Exception as e:
            self.amqpc.log.error(f"Exception: {e}")
            raise LvmagpFocuserError

        return position


class LVMKMirror:
    """
    Class for the K-mirros

    Parameters
    ----------
    tel
        Telescope unit to which the focuser belongs
    """

    def __init__(self, tel, amqpc):
        self.amqpc = amqpc
        self._km = None

        try:
            self._km = Proxy(self.amqpc, "lvm." + tel + ".km")
            self._km.start()

        except Exception as e:
            self.amqpc.log.error(f"Exception: {e}")

    async def cal_traj(self, command):
        pass


class LVMFibselector:
    """
    Class for the fiber selectors

    Parameters
    ----------
    tel
        Telescope unit to which the focuser belongs
    """

    def __init__(self, tel, amqpc):
        self.amqpc = amqpc
        self._fibsel = None

        try:
            self._fibsel = Proxy(self.amqpc, "lvm." + tel + ".fibsel")
            self._fibsel.start()

        except Exception as e:
            self.amqpc.log.error(f"Exception: {e}")


class LVMTelescope:
    """
    Class for the telescopes (Planewave mounts)

    Parameters
    ----------
    tel
        The name of the telescope
    """

    def __init__(self, tel, amqpc, sitename="LCO"):
        self.amqpc = amqpc
        self.lvmpwi = "lvm." + tel + ".pwi"
        self._pwi = None

        site = Site(name=sitename)
        self.latitude = site.lat
        self.longitude = site.long

        self.scale_matrix = np.array(
            [[0, 0], [0, 0]]
        )  # (ra, dec) = (scale_matrix)*(x, y)

        self.ag_task = None
        self.ag_break = False

        try:
            self._pwi = Proxy(self.amqpc, self.lvmpwi)
            self._pwi.start()

        except Exception as e:
            self.amqpc.log.error(f"Exception: {e}")

    def goto_park(self):
        """
        Move telescope to safe park position.

        ======
        Comments and desired actions:
        - Check dome safety interlock:
            - if interlock is engaged, do not move the telescope. Return error message (assume people are inside dome)
        - run status (LVMI_interface) to check instrument status
            - if not idle (i.e. carrying out any observations or calibrations), abort observation (halt in LVMI_interface) and park telescope
            (in this case, we assume user wants to park due to an emergency)
        """
        pass

    def goto_zenith(self):
        """
        Point telescope to zenith

        ======
        Comments and desired actions:
        - Check dome safety interlock:
            - if interlock is engaged, do not move the telescope. Return error message (assume people are inside dome)
        - run status (LVMI_interface) to check instrument status
            - if not idle (i.e. carrying out any observations or calibrations), repeat status command regularly until it returns idle,
              then move telescope. Regularly give updates (i.e. "waiting for instrument to become idle before moving telescope")
        """

    pass

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
        try:
            self._pwi.gotoRaDecJ2000()
        except Exception as e:
            self.amqpc.log.error(f"Exception: {e}")

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
            command, self.lvmpwi, "offset --dec_add_arcsec %f" % dec_arcsec
        )

        await send_message(
            command, self.lvmpwi, "offset --ra_add_arcsec %f" % ra_arcsec
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


class LVMCamera:
    """
    Class for the FLIR guide cameras
    """

    def __init__(self, amqpc):
        self.lvmcam = "lvmcam"  # actor name
        self.camname = ""  # cam name
        self.offset_x = -999
        self.offset_y = -999
        self.pixelscale = -999
        self.rotationangle = -999
        self.lvmcampath = ""

        self.amqpc = amqpc
        self._cam = None

    def single_exposure(self, exptime):
        """
        Take a single exposure

        Parameters
        ----------
        exptime
            Exposure time
        """
        path = self._cam.expose(exptime=exptime, num=1, camname=self.camname)["PATH"]

        return path["0"]

    def test_exposure(self, exptime):
        """
        Take a test exposure using ``-t`` option of lvmcam.
        The image file (Temp.fits) will be overwritten whenever this command is executed.

        Parameters
        ----------
        exptime
            Exposure time
        """
        path = self._cam.expose(
            exptime=exptime, num=1, camname=self.camname, testshot=True
        )["PATH"]

        return path["0"]

    def bias_exposure(self, repeat):
        """
        Take a test exposure using ``-t`` option of lvmcam.
        The image file (Temp.fits) will be overwritten whenever this command is executed.

        Parameters
        ----------
        repeat
            The number of bias images
        """
        path = self._cam.expose(exptime=0, num=repeat, camname=self.camname)["PATH"]

        return path.values()


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
        self.lvmcam = "lvm." + tel + ".age"
        self.camname = tel + ".age"

        try:
            self._cam = Proxy(self.amqpc, self.lvmcam)
            self._cam.start()
        except Exception as e:
            self.amqpc.log.error(f"Exception: {e}")


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
        self.lvmcam = "lvm." + tel + ".agw"
        self.camname = tel + ".agw"

        try:
            self._cam = Proxy(self.amqpc, self.lvmcam)
            self._cam.start()
        except Exception as e:
            self.amqpc.log.error(f"Exception: {e}")


class LVMTelescopeUnit(
    LVMTelescope, LVMFocuser, LVMWestCamera, LVMEastCamera, LVMFibselector, LVMKMirror
):
    def __init__(
        self,
        tel,
        enable_pwi=True,
        enable_foc=True,
        enable_agw=True,
        enable_age=True,
        enable_fibsel=False,
        enable_km=True,
    ):
        self.name = tel
        self.amqpc = AMQPClient(name=f"{sys.argv[0]}.proxy-{uuid.uuid4().hex[:8]}")

        try:
            if enable_pwi is True:
                LVMTelescope.__init__(self.name, self.amqpc)

            if enable_foc is True:
                LVMFocuser.__init__(self.name, self.amqpc)

            if enable_agw is True:
                self.agw = LVMWestCamera(self.name)

            if enable_age is True:
                self.age = LVMEastCamera(self.name)

            if enable_fibsel is True:
                LVMFibselector.__init__(self.name, self.amqpc)

            if enable_km is True:
                LVMKMirror.__init__(self.name, self.amqpc)

        except Exception as e:
            self.amqpc.log.error(f"Exception: {e}")

    def __del__(self):
        self.amqpc.stop()

    ############# Autofocus functions #########################
    def coarse_autofocus(self):
        """
        Find the focus coarsely by scanning whole reachable position.
        """
        pass

    def fine_autofocus(self):
        """
        Find the optimal focus position which is near the current position.
        """
        position, FWHM = [], []
        incremental = usrpars.af_incremental
        repeat = usrpars.af_repeat

        # get current pos of focus stage
        currentposition = self.getfocusposition(unit="STEPS")

        # Move focus
        targetposition = currentposition - (incremental * (repeat - 1)) / 2.0
        self.focus(value=targetposition)

        currentposition = targetposition
        position.append(currentposition)

        # Take picture & picture analysis
        FWHM_tmp = self.__get_fwhm()
        FWHM.append(FWHM_tmp)

        for iteration in range(repeat - 1):
            targetposition = currentposition + incremental
            self.focus(value=targetposition)

            currentposition = targetposition
            position.append(currentposition)

            FWHM_tmp = self.__get_fwhm()
            FWHM.append(FWHM_tmp)

        # Fitting
        bestposition, bestfocus = findfocus(position, FWHM)
        self.focus(value=bestposition)

        return bestposition, bestfocus

    def __get_fwhm(self):
        """
        Take a testshot using both guide image camera and return FWHM of the image.
        """
        exptime = usrpars.af_exptime
        imgcmd_w, imgcmd_e = None, None

        try:
            if self.name != "phot":
                imgcmd_w, imgcmd_e = invoke(
                    self.agw.single_exposure(exptime=exptime),
                    self.age.single_exposure(exptime=exptime),
                )
            else:
                imgcmd_w = self.agw.single_exposure(exptime=exptime)
                imgcmd_e = imgcmd_w

        except Exception as e:
            self.amqpc.log.error(f"Exception: {e}")

        guideimg_w = GuideImage(imgcmd_w["PATH"]["0"])
        guideimg_w.findstars()
        guideimg_e = GuideImage(imgcmd_e["PATH"]["0"])
        guideimg_e.findstars()
        FWHM = 0.5 * (guideimg_w.FWHM + guideimg_e.FWHM)

        return FWHM

    ############# Slew functions #########################
    def goto_eq(self, ra, dec, PA=0, target="optical_axis", deg=True):
        """
        Point telescope to position using RA and dec

        ======
        Comments and desired actions:
        - Check dome safety interlock:
            - if interlock is engaged, do not move the telescope. Return error message (assume people are inside dome)
        - run status (LVMI_interface) to check instrument status
            - if not idle (i.e. carrying out any observations or calibrations), repeat status command regularly until it returns idle,
              then move telescope. Regularly give updates (i.e. "waiting for instrument to become idle before moving telescope")
        """

    pass

    def goto_aa(self, alt, az, PA=0, target="optical_axis", deg=True):
        """
        Point telescope to position using alt/az (i.e. point to screen or manually park)

        ======
        Comments and desired actions:
        - Check dome safety interlock:
            - if interlock is engaged, do not move the telescope. Return error message (assume people are inside dome)
        - run status (LVMI_interface) to check instrument status
            - if not idle (i.e. carrying out any observations or calibrations), repeat status command regularly until it returns idle,
              then move telescope. Regularly give updates (i.e. "waiting for instrument to become idle before moving telescope")
        """

    pass

    def goto_screen(self):
        """
        Point telescope to screen for dome flats

        ======
        Comments and desired actions:
        - Check dome safety interlock:
            - if interlock is engaged, do not move the telescope. Return error message (assume people are inside dome)
        - run status (LVMI_interface) to check instrument status
            - if not idle (i.e. carrying out any observations or calibrations), repeat status command regularly until it returns idle,
              then move telescope. Regularly give updates (i.e. "waiting for instrument to become idle before moving telescope")
        """

    pass

    ############# Autoguide functions #########################
    def offset(
        self,
        target=None,
        delta_ra=None,
        delta_dec=None,
        delta_x=None,
        delta_y=None,
        offset_gbox=False,
    ):
        """
        Pointing offset: change track rates

        ======
        Comments and desired actions:
        """
        pass

    def guide_offset(
        self, target=None, delta_ra=None, delta_dec=None, delta_x=None, delta_y=None
    ):
        """
        Guiding offset: do NOT change track rates

        ======
        Comments and desired actions:
        """

    pass

    def offset_gbox(self, delta_x=None, delta_y=None, delta_pa=None):
        """
        move the guider set points by specified amount; used to move accurate
        offsets by letting the guider do the work. used, e.g., for dithering.
        ======
        Comments and desired actions:
        """

    pass

    def paoffset(self, delta_PA=None):
        """
        Apply a relative rotation offset by moving the K-mirror

        Parameters:
            delta_PA (float): rotation offset in degrees (+/- = E/W)

        Returns:
            None
        """

    pass
