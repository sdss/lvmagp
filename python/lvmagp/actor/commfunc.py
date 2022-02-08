import datetime
import logging
import sys
import uuid
from multiprocessing import Manager, Process

import astropy.units as u
import numpy as np
from astropy.coordinates import Angle
from clu import AMQPClient
from cluplus.proxy import Proxy, invoke
from lvmtipo.site import Site

from sdsstools import get_logger

from lvmagp.actor.internalfunc import (
    GuideImage,
    cal_pa,
    check_target,
    define_visb_limit,
    findfocus,
)
from lvmagp.actor.user_parameters import temp_vs_focus, usrpars
from lvmagp.exceptions import (
    LvmagpAcquisitionFailed,
    LvmagpActorMissing,
    LvmagpInterlockEngaged,
    LvmagpTargetOverTheLimit,
)


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
            self.amqpc.log.error(f"{datetime.datetime.now()} | {e}")
            raise

    def focusoffset(self, delta_f=None):
        """
        Apply a relative telescope focus offset.

        Parameters:
            delta_f (float): focus offset value in steps
        """

        try:
            self.amqpc.log.debug(f"{datetime.datetime.now()} | Move focus by {delta_f}")
            self._foc.moveRelative(delta_f, unit="STEPS")

        except Exception as e:
            self.amqpc.log.error(f"{datetime.datetime.now()} | {e}")
            raise
        self.amqpc.log.debug(f"{datetime.datetime.now()} | Move focus done")
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
                self.amqpc.log.debug(
                    f"{datetime.datetime.now()} | Move focus to {value}"
                )
                self._foc.moveAbsolute(value, unit="STEPS")
            else:
                temp_value = temp_vs_focus(temperature=temperature)
                self.amqpc.log.debug(
                    f"{datetime.datetime.now()} | Move focus to {value} (estimated)"
                )
                self._foc.moveAbsolute(temp_value, unit="STEPS")

        except Exception as e:
            self.amqpc.log.error(f"{datetime.datetime.now()} | {e}")
            raise

        self.amqpc.log.debug(f"{datetime.datetime.now()} | Move focus done")

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
            self.amqpc.log.error(f"{datetime.datetime.now()} | {e}")
            raise

        self.amqpc.log.info(
            f"{datetime.datetime.now()} | Current focus position: {position}"
        )
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
            self.amqpc.log.error(f"{datetime.datetime.now()} | {e}")
            raise

    async def cal_traj(self, command):
        pass

    def derotate(self, pa=None):
        """
        Derotate the field to correct the given position angle.

        Parameters
        ----------
        pa
            Target position angle to be corrected
        """

        try:
            self.amqpc.log.debug(f"{datetime.datetime.now()} | Move Kmirror to {pa}")
            self._km.moveAbsolute(pa, unit="DEG")

        except Exception as e:
            self.amqpc.log.error(f"{datetime.datetime.now()} | {e}")
            raise
        self.amqpc.log.debug(f"{datetime.datetime.now()} | Move Kmirror done")


class LVMFiberselector:
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
            self.amqpc.log.error(f"{datetime.datetime.now()} | {e}")
            raise


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
            self.amqpc.log.error(f"{datetime.datetime.now()} | {e}")
            raise

    def goto_park(self):
        """
        Move telescope to safe park position.

        ======
        Comments and desired actions:
        - Check dome safety interlock:
            - if interlock is engaged, do not move the telescope. Return error message
            (assume people are inside dome)
        - run status (LVMI_interface) to check instrument status
            - if not idle (i.e. carrying out any observations or calibrations),
            abort observation (halt in LVMI_interface) and park telescope
            (in this case, we assume user wants to park due to an emergency)
        """
        pass

    def goto_zenith(self):
        """
        Point telescope to zenith

        ======
        Comments and desired actions:
        - Check dome safety interlock:
            - if interlock is engaged, do not move the telescope.
            Return error message (assume people are inside dome)
        - run status (LVMI_interface) to check instrument status
            - if not idle (i.e. carrying out any observations or calibrations),
            repeat status command regularly until it returns idle,
              then move telescope. Regularly give updates
              (i.e. "waiting for instrument to become idle before moving telescope")
        """

    def slew_radec2000(self, target_ra_h, target_dec_d):
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
            self.amqpc.log.debug(
                f"{datetime.datetime.now()} | Start to slew telescope to RA {target_ra_h}, Dec {target_dec_d}."  # noqa: E501
            )
            self._pwi.gotoRaDecJ2000(ra_h=target_ra_h, deg_d=target_dec_d)
        except Exception as e:
            self.amqpc.log.debug(f"{datetime.datetime.now()} | {e}")
            raise
        self.amqpc.log.debug(f"{datetime.datetime.now()} | Slew completed.")

    def slew_altaz(self, target_alt_d, target_az_d):
        """
        Slew the telescope to given horizontal coordinates.

        Parameters
        ----------
        target_alt_d
            Target altitude in degree
        target_az_d
            Target azimuth in degree
        """
        try:
            self.amqpc.log.debug(
                f"{datetime.datetime.now()} | Start to slew telescope to Alt {target_alt_d}, Az {target_az_d}."  # noqa: E501
            )
            self._pwi.gotoRaDecJ2000(alt_d=target_alt_d, az_d=target_az_d)
        except Exception as e:
            self.amqpc.log.debug(f"{datetime.datetime.now()} | {e}")
            raise
        self.amqpc.log.debug(f"{datetime.datetime.now()} | Slew completed.")

    def reset_offset_radec(self):
        """
        Reset the offset of both axes to zero.
        """
        try:
            self.amqpc.log.debug(
                f"{datetime.datetime.now()} | Set telescope offsets to zero."
            )
            self._pwi.offset(ra_reset=0, dec_reset=0)
        except Exception as e:
            self.amqpc.log.debug(f"{datetime.datetime.now()} | {e}")
            raise
        self.amqpc.log.debug(
            f"{datetime.datetime.now()} | Zero offset setting completed."
        )

    def offset_radec(self, ra_arcsec, dec_arcsec):
        """
        Give some offset to the mount

        Parameters
        ----------
        ra_arcsec
            Distance to move along right ascension axis in arcseconds
        dec_arcsec
            Distance to move along declination axis in arcseconds
        """

        try:
            self.amqpc.log.debug(
                f"{datetime.datetime.now()} | Set telescope offsets ra={ra_arcsec}, dec={dec_arcsec}"  # noqa: E501
            )
            self._pwi.offset(ra_add_arcsec=ra_arcsec, dec_add_arcsec=dec_arcsec)
        except Exception as e:
            self.amqpc.log.debug(f"{datetime.datetime.now()} | {e}")
            raise
        self.amqpc.log.debug(f"{datetime.datetime.now()} | Set offset done")

    def get_dec2000_deg(self):
        """
        Return the declination (J2000) of current position in degrees
        """
        try:
            status = self._pwi.status()
        except Exception as e:
            self.amqpc.log.debug(f"{datetime.datetime.now()} | {e}")
            raise

        return status["dec_j2000_degs"]


class LVMCamera:
    """
    Class for the FLIR guide cameras
    """

    def __init__(self):
        self.lvmcam = "lvmcam"  # actor name
        self.camname = ""  # cam name
        self.lvmcampath = ""

        self.amqpc = None
        self._cam = None

    def single_exposure(self, exptime):
        """
        Take a single exposure

        Parameters
        ----------
        exptime
            Exposure time
        """
        self.amqpc.log.debug(
            f"{datetime.datetime.now()} | Guider {self.camname} exposure started"
        )

        try:
            path = self._cam.expose(exptime=exptime, num=1, camname=self.camname)[
                "PATH"
            ]
        except Exception as e:
            self.amqpc.log.error(f"{datetime.datetime.now()} | {e}")
            raise

        self.amqpc.log.debug(
            f"{datetime.datetime.now()} | Guider {self.camname} exposure done"
        )

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
        self.amqpc.log.debug(
            f"{datetime.datetime.now()} | Guider {self.camname} exposure started"
        )

        try:
            path = self._cam.expose(
                exptime=exptime, num=1, camname=self.camname, testshot=True
            )["PATH"]
        except Exception as e:
            self.amqpc.log.error(f"{datetime.datetime.now()} | {e}")
            raise

        self.amqpc.log.debug(
            f"{datetime.datetime.now()} | Guider {self.camname} exposure done"
        )

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
        try:
            path = self._cam.expose(exptime=0, num=repeat, camname=self.camname)["PATH"]
        except Exception as e:
            self.amqpc.log.error(f"{datetime.datetime.now()} | {e}")
            raise

        self.amqpc.log.debug(
            f"{datetime.datetime.now()} | Guider {self.camname} exposure done"
        )

        return path.values()


class LVMEastCamera(LVMCamera):
    """
    Class for the FLIR guide cameras installed in east side

    Parameters
    ----------
    tel
        Telescope to which the camera belongs
    """

    def __init__(self, tel, amqpc):
        super().__init__()
        self.amqpc = amqpc
        self.lvmcam = "lvm." + tel + ".age"
        self.camname = tel + ".age"

        try:
            self._cam = Proxy(self.amqpc, self.lvmcam)
            self._cam.start()
        except Exception as e:
            self.amqpc.log.error(f"{datetime.datetime.now()} | {e}")
            raise


class LVMWestCamera(LVMCamera):
    """
    Class for the FLIR guide cameras installed in west side

    Parameters
    ----------
    tel
        Telescope to which the camera belongs
    """

    def __init__(self, tel, amqpc):
        super().__init__()
        self.amqpc = amqpc
        self.lvmcam = "lvm." + tel + ".agw"
        self.camname = tel + ".agw"

        try:
            self._cam = Proxy(self.amqpc, self.lvmcam)
            self._cam.start()
        except Exception as e:
            self.amqpc.log.error(f"{datetime.datetime.now()} | {e}")
            raise


class LVMTelescopeUnit(
    LVMTelescope, LVMFocuser, LVMWestCamera, LVMEastCamera, LVMFiberselector, LVMKMirror
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
        self.log = get_logger(f"sdss-lvmagp-{tel}")
        self.log.sh.setLevel(logging.DEBUG)
        self.amqpc = AMQPClient(
            name=f"{sys.argv[0]}.proxy-{uuid.uuid4().hex[:8]}",
            log_dir="/home/hojae/Desktop/lvmagp/logs",
            log=self.log,
        )
        # log_dir => How to fix??
        self.__connect_actors(
            enable_pwi, enable_foc, enable_agw, enable_age, enable_fibsel, enable_km
        )
        self.__read_parameters()

    def __connect_actors(
        self, enable_pwi, enable_foc, enable_agw, enable_age, enable_fibsel, enable_km
    ):
        try:
            if enable_pwi is True:
                LVMTelescope.__init__(self, self.name, self.amqpc)

            if enable_foc is True:
                LVMFocuser.__init__(self, self.name, self.amqpc)

            if enable_agw is True:
                self.agw = LVMWestCamera(self.name, self.amqpc)

            if enable_age is True:
                self.age = LVMEastCamera(self.name, self.amqpc)

            if enable_fibsel is True:
                LVMFiberselector.__init__(self, self.name, self.amqpc)

            if enable_km is True:
                LVMKMirror.__init__(self, self.name, self.amqpc)
        except Exception:
            raise LvmagpActorMissing

        self.amqpc.log.debug(
            f"{datetime.datetime.now()} | All instrument actors are connected."
        )

    def __read_parameters(self):
        # should be predefined somewhere...
        self.offset_x = -999
        self.offset_y = -999
        self.pixelscale = -999
        self.rotationangle = -999

        self.screen_alt_d = -999
        self.screen_az_d = -999

    ######## Autofocus functions #############
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

        self.amqpc.log.info(
            f"{datetime.datetime.now()} | (lvmagp) Fine autofocus start"
        )

        # get current pos of focus stage
        currentposition = self.getfocusposition(unit="STEPS")

        # Move focus
        targetposition = currentposition - (incremental * (repeat - 1)) / 2.0
        self.focus(value=targetposition)

        currentposition = targetposition
        position.append(currentposition)

        # Take picture & picture analysis
        FWHM_tmp = self.__get_fwhm()
        self.amqpc.log.info(
            f"{datetime.datetime.now()} | Focus at {currentposition}: {FWHM_tmp}"
        )
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
        self.amqpc.log.info(
            f"{datetime.datetime.now()} | (lvmagp) Fine autofocus done: pos={bestposition}, focus={bestfocus}"  # noqa: E501
        )

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
            self.amqpc.log.error(f"{datetime.datetime.now()} | {e}")
            raise

        guideimg_w = GuideImage(imgcmd_w["PATH"]["0"])
        guideimg_w.findstars()
        guideimg_e = GuideImage(imgcmd_e["PATH"]["0"])
        guideimg_e.findstars()
        FWHM = 0.5 * (guideimg_w.FWHM + guideimg_e.FWHM)

        return FWHM

    ############# Slew functions #########################

    def goto_eq(
        self,
        target_ra_h,
        target_dec_d,
        target_pa_d=0,
        target="optical_axis",
        ra_d=False,
    ):
        """
        Point telescope to position using RA and dec (J2000).

        Comments and desired actions:
        - Check dome safety interlock:
            - if interlock is engaged, do not move the telescope.
            Return error message (assume people are inside dome)
        - run status (LVMI_interface) to check instrument status
            - if not idle (i.e. carrying out any observations or calibrations),
            repeat status command regularly until it returns idle,
              then move telescope. Regularly give updates
              (i.e. "waiting for instrument to become idle before moving telescope")

        Parameters
        ----------
        target_ra_h
            The right ascension (J2000) of the target in hours
        target_dec_d
            The declination (J2000) of the target in degrees
        target_pa_d
            Desired position angle of the image
        target
            ???
        ra_d
            If ``True``, the RA of target should be given in degrees.
        """
        if self.check_safety_interlock():
            self.amqpc.log.debug(
                f"{datetime.datetime.now()} | (lvmagp) safety interlock engaged"
            )
            raise LvmagpInterlockEngaged

        # Check status to confirm the system is in idle state?

        # Check the target is in reachable area
        long_d = self.latitude
        lat_d = self.latitude

        if not check_target(target_ra_h, target_dec_d, long_d, lat_d):
            self.amqpc.log.debug(
                f"{datetime.datetime.now()} | (lvmagp) Target is over the limit"
            )
            raise LvmagpTargetOverTheLimit

        self.reset_offset_radec()

        # Calculate position angle and rotate K-mirror  :: should be changed to traj method.
        target_pa_d0 = cal_pa(target_ra_h, target_dec_d, long_d, lat_d)

        invoke(
            self.derotate(target_pa_d0 + target_pa_d),
            self.slew_radec2000(target_ra_h=target_ra_h, target_dec_d=target_dec_d),
        )

        self.amqpc.log.debug(
            f"{datetime.datetime.now()} | (lvmagp) Initial slew completed"
        )

        for iter in range(usrpars.aqu_max_iter + 1):

            # take an image for astrometry
            guideimgpath = invoke(
                self.agw.test_exposure(usrpars.aqu_exptime),
                self.age.test_exposure(usrpars.aqu_exptime),
            )

            westguideimg = GuideImage(guideimgpath[0])
            eastguideimg = GuideImage(guideimgpath[1])

            # astrometry
            manager = Manager()
            posinfo1 = manager.dict()
            posinfo2 = manager.dict()

            processes = []
            processes.append(
                Process(
                    target=westguideimg.astrometry,
                    args=(target_ra_h, target_dec_d, posinfo1),
                )
            )
            processes.append(
                Process(
                    target=eastguideimg.astrometry,
                    args=(target_ra_h, target_dec_d, posinfo2),
                )
            )

            for p in processes:
                p.start()

            for p in processes:
                p.join()

            westguideimg.ra2000 = posinfo1["ra"]
            westguideimg.dec2000 = posinfo1["dec"]
            westguideimg.pa = posinfo1["pa"]
            eastguideimg.ra2000 = posinfo1["ra"]
            eastguideimg.dec2000 = posinfo1["dec"]
            eastguideimg.pa = posinfo1["pa"]

            ra2000_d = 0.5 * (eastguideimg.ra2000 + westguideimg.ra2000)
            dec2000_d = 0.5 * (eastguideimg.dec2000 + westguideimg.dec2000)
            pa_d = 0.5 * (eastguideimg.pa + westguideimg.pa)
            # LVMWestCamera.rotationangle = westguideimg.pa   should be defined to which place?
            # LVMEastCamera.rotationangle = eastguideimg.pa   should be defined to which place?

            ra2000 = Angle(ra2000_d, u.degree)
            dec2000 = Angle(dec2000_d, u.degree)

            target_ra = Angle(target_ra_h, u.hour)
            target_dec = Angle(target_dec_d, u.degree)

            comp_ra_arcsec = (target_ra - ra2000).arcsecond
            comp_dec_arcsec = (target_dec - dec2000).arcsecond

            self.amqpc.log.info(
                f"{datetime.datetime.now()} | (lvmagp) Astrometry result"
                f"Img_ra2000={ra2000.to_string(unit=u.hour)}"
                f"Img_dec2000={dec2000.to_string(unit=u.degree)}"
                f"Img_pa={pa_d:%.3f} deg"
                f"offset_ra={comp_ra_arcsec:%.3f} arcsec"
                f"offset_dec={comp_dec_arcsec:%.3f} arcsec"
            )

            # Compensation  // Compensation for K-mirror based on astrometry result?
            # may be by offset method..
            if (
                np.sqrt(comp_ra_arcsec ** 2 + comp_dec_arcsec ** 2) >
                usrpars.aqu_tolerance_arcsec
            ):
                if iter >= usrpars.aqu_max_iter:
                    self.amqpc.log.debug(
                        f"{datetime.datetime.now()} | (lvmagp) Acquisition compensation failed"
                    )
                    raise LvmagpAcquisitionFailed
                else:
                    self.amqpc.log.debug(
                        f"{datetime.datetime.now()} | (lvmagp) Compensate offset: #{iter}"
                    )
                    invoke(
                        self.derotate(target_pa_d - pa_d),
                        self.offset_radec(
                            ra_arcsec=comp_ra_arcsec, dec_arcsec=comp_dec_arcsec
                        ),
                    )
            else:
                break

    def goto_aa(
        self, target_alt_d, target_az_d, target_pa_d=0, target="optical_axis", deg=True
    ):
        """
        Point telescope to position using alt/az (i.e. point to screen or manually park)
        It does not run additional compensation based on astrometry.

        ======
        Comments and desired actions:
        - Check dome safety interlock:
            - if interlock is engaged, do not move the telescope.
            Return error message (assume people are inside dome)
        - run status (LVMI_interface) to check instrument status
            - if not idle (i.e. carrying out any observations or calibrations),
            repeat status command regularly until it returns idle,
              then move telescope. Regularly give updates
              (i.e. "waiting for instrument to become idle before moving telescope")

        Parameters
        ----------
        target_alt_d
            Target altitude in degree
        target_az_d
            Target azimuth in degree
        target_pa_d
            Target position angle in degree
        target
            ???
        deg
            ???
        """

        if self.check_safety_interlock():
            self.amqpc.log.debug(
                f"{datetime.datetime.now()} | (lvmagp) safety interlock engaged"
            )
            raise LvmagpInterlockEngaged

        # Check status to confirm the system is in idle state?

        # Check the target is in reachable area
        alt_low, alt_high = define_visb_limit(target_az_d)
        if not (alt_low < target_alt_d) or not (target_alt_d < alt_high):
            self.amqpc.log.debug(
                f"{datetime.datetime.now()} | (lvmagp) Target is over the limit"
            )
            raise LvmagpTargetOverTheLimit

        self.reset_offset_radec()

        # Calculate position angle and rotate K-mirror  :: should be changed to traj method.
        target_pa_d0 = (
            0  # I dont know ... # cal_pa(target_ra_h, target_dec_d, long_d, lat_d)
        )

        invoke(
            self.derotate(target_pa_d0 + target_pa_d),
            self.slew_altaz(target_alt_d=target_alt_d, target_az_d=target_az_d),
        )

        self.amqpc.log.debug(
            f"{datetime.datetime.now()} | (lvmagp) Initial slew completed"
        )

    def goto_screen(self):
        """
        Point telescope to screen for dome flats

        ======
        Comments and desired actions:
        - Check dome safety interlock:
            - if interlock is engaged, do not move the telescope.
            Return error message (assume people are inside dome)
        - run status (LVMI_interface) to check instrument status
            - if not idle (i.e. carrying out any observations or calibrations),
            repeat status command regularly until it returns idle,
              then move telescope. Regularly give updates
              (i.e. "waiting for instrument to become idle before moving telescope")
        """

        self.goto_aa(target_alt_d=self.screen_alt_d, target_az_d=self.screen_az_d)

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

    def check_safety_interlock(self):
        pass
