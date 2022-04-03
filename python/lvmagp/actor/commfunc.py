import sys, uuid, datetime, logging
from multiprocessing import Manager, Process
from threading import Thread
import numpy as np
import astropy.units as u
from astropy.coordinates import Angle, SkyCoord
from clu import AMQPClient
from cluplus.proxy import Proxy, invoke
from lvmtipo.site import Site
from lvmtipo.siderostat import Siderostat
from lvmtipo.target import Target
from sdsstools import get_logger
import yaml

from lvmagp.actor.internalfunc import (
    GuideImage,
    cal_pa,
    check_target,
    define_visb_limit,
    findfocus,
    print_debug,
    print_error,
    print_info,
)
from lvmagp.actor.user_parameters import temp_vs_focus, usrpars
from lvmagp.exceptions import (
    LvmagpAcquisitionFailed,
    LvmagpActorMissing,
    LvmagpInterlockEngaged,
    LvmagpTargetOverTheLimit,
)

# import time


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
            print_error(self.amqpc, e)
            raise

    def focusoffset(self, delta_f=None):
        """
        Apply a relative telescope focus offset.

        Parameters:
            delta_f (float): focus offset value in steps
        """

        try:
            print_debug(self.amqpc, f"Move focus by {delta_f}")
            self._foc.moveRelative(delta_f, "STEPS")

        except Exception as e:
            print_error(self.amqpc, e)
            raise
        print_debug(self.amqpc, "Move focus done")
        return True

    def focus(self, value=None, temperature=None):
        """
        Move focus to a particular value or a first guess from a given temperature

        Parameters:
            value (float): if provided, focus stage moves to this step value
            temperature (float): if 'value' is not provided or 'value=None',
            focus stage moves to best guess based on focus vs temperature model
        Returns:
            None
        """

        try:
            if value is not None:
                print_debug(self.amqpc, f"Move focus to {value}")
                self._foc.moveAbsolute(value, "STEPS")
            else:
                temp_value = temp_vs_focus(temperature=temperature)
                print_debug(self.amqpc, f"{datetime.datetime.now()} | Move focus to {value} (estimated)")
                self._foc.moveAbsolute(temp_value, "STEPS")

        except Exception as e:
            print_error(self.amqpc, e)
            raise

        print_debug(self.amqpc, "Move focus done")

    def getfocusposition(self, unit="STEPS"):
        """
        Get current position of device in given unit.

        Parameters
        ----------
        unit
            Unit of position
        """
        try:
            position = self._foc.getPosition(unit)["Position"]
        except Exception as e:
            print_error(self.amqpc, e)
            raise

        print_info(self.amqpc, f"Current focus position: {position}")
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
            print_error(self.amqpc, e)
            raise

    def derotate(self, pa):
        """
        Derotate the field to correct the given field angle.

        Parameters
        ----------
        pa
            Target field angle to be corrected.
            The direction where pa = field angle will head up after the derotation.
        """

        try:
            print_debug(self.amqpc, f"Rotate Kmirror to {pa}")
            self._km.moveAbsolute(pa, "DEG")

        except Exception as e:
            print_error(self.amqpc, e)
            raise
        print_debug(self.amqpc, "Rotating Kmirror done")


    def _kmoffset(self, delta_pa):
        """
        Rotate K-mirror by given offset angle in degree.

        Parameters
        ----------
        delta_pa
            Offset angle for K-mirror to be rotated.
        """
        try:
            print_debug(self.amqpc, f"Rotate Kmirror by {delta_pa}")
            self._km.moveRelative(delta_pa, "DEG")

        except Exception as e:
            print_error(self.amqpc, e)
            raise
        print_debug(self.amqpc, "Rotating Kmirror done")

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
            print_error(self.amqpc, e)
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

        try:
            self._pwi = Proxy(self.amqpc, self.lvmpwi)
            self._pwi.start()

        except Exception as e:
            print_error(self.amqpc, e)
            raise

    def _slew_radec2000(self, target_ra_h, target_dec_d):
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
            print_debug(self.amqpc, f"Start to slew telescope to RA {target_ra_h}, Dec {target_dec_d}.")  # noqa: E501
            self._pwi.gotoRaDecJ2000(target_ra_h, target_dec_d)
        except Exception as e:
            print_error(self.amqpc, e)
            raise
        print_debug(self.amqpc, "Slew completed.")


    def _slew_altaz(self, target_alt_d, target_az_d):
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
            print_debug(self.amqpc, f"Start to slew telescope to Alt {target_alt_d}, Az {target_az_d}.")  # noqa: E501
            self._pwi.gotoAltAzJ2000(target_alt_d, target_az_d)
        except Exception as e:
            print_error(self.amqpc, e)
            raise
        print_debug(self.amqpc, "Slew completed.")

    def _reset_offset_radec(self):
        """
        Reset the offset of both axes to zero.
        """
        try:
            print_debug(self.amqpc, "Set telescope offsets to zero.")
            self._pwi.offset(ra_reset=0, dec_reset=0)
        except Exception as e:
            print_error(self.amqpc, e)
            raise
        print_debug(self.amqpc, "Zero offset setting completed.")

    def _offset_radec(self, ra_arcsec, dec_arcsec):
        """
        Give some offset to the mount

        Parameters
        ----------
        ra_arcsec
            Distance to move along right ascension axis in arcseconds
        dec_arcsec
            Distance to move along declination axis in arcseconds
        """
        print_debug(self.amqpc, f"Set telescope offsets ra={ra_arcsec}, dec={dec_arcsec}")  # noqa: E501
        try:
            self._pwi.offset(ra_add_arcsec=ra_arcsec, dec_add_arcsec=dec_arcsec)
        except Exception as e:
            print_error(self.amqpc, e)
            raise
        print_debug(self.amqpc, "Set offset done")

    def _get_dec2000_deg(self):
        """
        Return the declination (J2000) of current position in degrees
        """
        try:
            status = self._pwi.status()
        except Exception as e:
            print_error(self.amqpc, e)
            raise

        return status["dec_j2000_degs"]

    def _set_tracking(self, enable):
        """
        Turn on or off the mount tracking

        Parameters
        ----------
        enable
            If enable is True, tracking will be started. Otherwise, the tracking will be stopped.
        """


        s = "ON" if enable else "OFF"
        print_debug(self.amqpc, f"Set tracking {s}")
        try:
            self._pwi.setTracking(enable)
        except Exception as e:
            print_error(self.amqpc, e)
            raise


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
        print_debug(self.amqpc, f"Guider {self.camname} exposure started")

        try:
            path = self._cam.expose(exptime, 1, self.camname)[
                "PATH"
            ]
        except Exception as e:
            print_error(self.amqpc, e)
            raise

        print_debug(self.amqpc, f"Guider {self.camname} exposure done")

        return path['0']

    def test_exposure(self, exptime):
        """
        Take a test exposure using ``-t`` option of lvmcam.
        The image file (Temp.fits) will be overwritten whenever this command is executed.

        Parameters
        ----------
        exptime
            Exposure time
        """

        print_debug(self.amqpc, f"Guider {self.camname} exposure started")

        try:
             path = self._cam.expose(
                exptime, 1, self.camname, testshot=""
            )["PATH"]
        except Exception as e:
            print_error(self.amqpc, e)
            raise

        print_debug(self.amqpc, f"Guider {self.camname} exposure done")

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
        print_debug(self.amqpc, f"Guider {self.camname} exposure started")

        try:
            path = self._cam.expose(0, repeat, self.camname)["PATH"]
        except Exception as e:
            print_error(self.amqpc, e)
            raise

        print_debug(self.amqpc, f"Guider {self.camname} exposure done")

        return path.values()

    def status(self):
        '''
        Return status of autoguide camera (i.e. power status, exposing/reading out/idle ).
        '''

        try:
            status = self._cam.status()
        except Exception as e:
            print_error(self.amqpc, e)
            raise

        print_info(self.amqpc, status)

        return status

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
            try:
                self._cam.disconnect()
                self._cam.connect(name=self.camname)
            except Exception as e:
                self._cam.connect(name=self.camname)
        except Exception as e:
            print_error(self.amqpc, e)
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
            try:
                self._cam.disconnect()
                self._cam.connect(name=self.camname)
            except Exception as e:
                self._cam.connect(name=self.camname)
        except Exception as e:
            print_error(self.amqpc, e)
            raise


class LVMTelescopeUnit(
    LVMTelescope, LVMFocuser, LVMWestCamera, LVMEastCamera, LVMFiberselector, LVMKMirror
):
    def __init__(
        self,
        tel,
        sitename = "LCO",
        enable_pwi=True,
        enable_foc=True,
        enable_agw=True,
        enable_age=False,
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

        self.site = Site(name=sitename)
        self.latitude = self.site.lat
        self.longitude = self.site.long

        self.ag_task = None
        # self.ag_on = False
        self.ag_break = False

        self.siderostat = Siderostat()
        self.target = None

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
            else:
                self.age = self.agw

            if enable_fibsel is True:
                LVMFiberselector.__init__(self, self.name, self.amqpc)

            if enable_km is True:
                LVMKMirror.__init__(self, self.name, self.amqpc)
        except Exception:
            raise LvmagpActorMissing

        print_debug(self.amqpc, "All instrument actors are connected.")

    def __read_parameters(self):

        #with open('../etc/lvmagp.yml') as f:
        with open('../../etc/lvmagp.yml') as f:
            conf = yaml.load(f, Loader=yaml.FullLoader)
        data = conf[self.name]['agw']
        self.offset_x = data['offset_x']
        self.offset_y = data['offset_y']
        self.pixelscale = data['pixelscale']
        self.rotationangle = data['rotationangle']

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

        print_info(self.amqpc, "(lvmagp) Fine autofocus start")

        # get current pos of focus stage
        currentposition = self.getfocusposition(unit="STEPS")

        # Move focus
        targetposition = currentposition - (incremental * (repeat - 1)) / 2.0
        self.focus(value=targetposition)

        currentposition = targetposition
        position.append(currentposition)

        # Take picture & picture analysis
        FWHM_tmp = self.__get_fwhm()
        print_info(self.amqpc, f"Focus at {currentposition}: {FWHM_tmp}")
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
        print_info(self.amqpc, f"(lvmagp) Fine autofocus done: pos={bestposition}, focus={bestfocus}")  # noqa: E501

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
                    self.agw._cam.async_expose(usrpars.aqu_exptime, 1, self.agw.camname),
                    self.age._cam.async_expose(usrpars.aqu_exptime, 1, self.age.camname),
                )
                imgcmd_w, imgcmd_e = imgcmd_w["PATH"]["0"], imgcmd_e["PATH"]["0"]
            else:
                imgcmd_w = self.agw.single_exposure(exptime=exptime)
                imgcmd_e = imgcmd_w

        except Exception as e:
            print_error(self.amqpc, e)
            raise
        
        guideimg_w = GuideImage(imgcmd_w)
        guideimg_w.findstars()
        guideimg_e = GuideImage(imgcmd_e)
        guideimg_e.findstars()
        FWHM = 0.5 * (guideimg_w.FWHM + guideimg_e.FWHM)

        return FWHM

    ############# Slew functions #########################

    def goto_eq(
        self,
        target_ra_h,
        target_dec_d,
        target_pa_d=0,
        ra_d=False,
    ):
        """
        Point telescope to position using RA and dec (J2000).

        Comments and desired actions:
            Check dome safety interlock: if interlock is engaged, do not move the telescope.
            Return error message (assume people are inside dome)

            run status (LVMI_interface) to check instrument status: if not idle (i.e. carrying out any observations or calibrations),
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
        ra_d
            If ``True``, the RA of target should be given in degrees.
        """
        if self.check_safety_interlock():
            print_debug(self.amqpc, "(lvmagp) safety interlock engaged")
            raise LvmagpInterlockEngaged

        # Check status to confirm the system is in idle state?

        # Check the target is in reachable area
        long_d = self.longitude
        lat_d = self.latitude
        if ra_d:
            target_ra_h /= 15

        self.target = Target(SkyCoord(ra=target_ra_h*u.hourangle, dec=target_dec_d*u.degree))

        if not check_target(target_ra_h, target_dec_d, long_d, lat_d):
            print_debug(self.amqpc, "(lvmagp) Target is over the limit")
            raise LvmagpTargetOverTheLimit

        self._reset_offset_radec()

        # Calculate position angle and rotate K-mirror  :: should be changed to traj method.
        target_pa_d0 = cal_pa(target_ra_h, target_dec_d, long_d, lat_d)

        # self.derotate(target_pa_d0 + target_pa_d)
        # self._slew_radec2000(target_ra_h=target_ra_h, target_dec_d=target_dec_d),
        
        pa = target_pa_d0 + target_pa_d

        print_debug(self.amqpc, f"Rotate Kmirror to {pa}")
        print_debug(self.amqpc, f"Start to slew telescope to RA {target_ra_h}, Dec {target_dec_d}.")  # noqa: E501

        invoke(
            self._km.async_moveAbsolute(pa , "DEG"),
            self._pwi.async_gotoRaDecJ2000(target_ra_h, target_dec_d-30/60),
        )

        print_debug(self.amqpc, "Rotating Kmirror done")
        print_debug(self.amqpc, "Slew completed.")

        print_debug(self.amqpc, "(lvmagp) Initial slew completed")

        for iter in range(usrpars.aqu_max_iter + 1):

            # take an image for astrometry
            
            print_debug(self.amqpc, "(lvmagp) Astrometry...")

            print_debug(self.amqpc, f"{self.agw.camname} exposure started")
            print_debug(self.amqpc, f"{self.age.camname} exposure started")

            guideimgpath = invoke(
                self.agw._cam.async_expose(usrpars.aqu_exptime, 1, self.agw.camname, testshot=True),
                self.age._cam.async_expose(usrpars.aqu_exptime, 1, self.age.camname, testshot=True)
            )
        
            guideimgpath = [guideimgpath[0]["PATH"]["0"], guideimgpath[1]["PATH"]["0"]]

            print_debug(self.amqpc, f"{self.agw.camname} exposure done")
            print_debug(self.amqpc, f"{self.age.camname} exposure done")

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
            self.agw.rotationangle = westguideimg.pa  
            self.age.rotationangle = eastguideimg.pa 

            ra2000 = Angle(ra2000_d, u.degree)
            dec2000 = Angle(dec2000_d, u.degree)

            target_ra = Angle(target_ra_h, u.hour)
            target_dec = Angle(target_dec_d, u.degree)

            comp_ra_arcsec = (target_ra - ra2000).arcsecond
            comp_dec_arcsec = (target_dec - dec2000).arcsecond

            print_debug(self.amqpc, "(lvmagp) Astrometry result")
            print_info(self.amqpc, f"Img_ra2000={ra2000.to_string(unit=u.hour)}")
            print_info(self.amqpc, f"Img_dec2000={dec2000.to_string(unit=u.degree)}")
            print_info(self.amqpc, f"Img_pa={pa_d:.3f} deg")
            print_info(self.amqpc, f"offset_ra={comp_ra_arcsec:.3f} arcsec")
            print_info(self.amqpc, f"offset_dec={comp_dec_arcsec:.3f} arcsec")

            # Compensation  // Compensation for K-mirror based on astrometry result?
            # may be by offset method..
            if (
                np.sqrt(comp_ra_arcsec ** 2 + comp_dec_arcsec ** 2) >
                usrpars.aqu_tolerance_arcsec
            ):
                if iter >= usrpars.aqu_max_iter:
                    print_debug(self.amqpc, "(lvmagp) Acquisition compensation failed")
                    raise LvmagpAcquisitionFailed
                else:
                    print_debug(self.amqpc, f"(lvmagp) Compensate offset: #{iter}")
                    
                    pa = target_pa_d - pa_d

                    print_debug(self.amqpc, f"Rotate Kmirror to {pa}")
                    print_debug(self.amqpc, f"Set telescope offsets ra={comp_ra_arcsec}, dec={comp_dec_arcsec}")
                    
                    invoke(
                        self._km.async_moveAbsolute(pa, "DEG"),
                        self._pwi.async_offset(ra_add_arcsec=comp_ra_arcsec, dec_add_arcsec=comp_dec_arcsec)
                    )

                    print_debug(self.amqpc, "Rotating Kmirror done")
                    print_debug(self.amqpc, "Set offset done")

                    # # invoke(
                    # self.derotate(target_pa_d - pa_d)
                    # self._offset_radec(ra_arcsec=comp_ra_arcsec, dec_arcsec=comp_dec_arcsec)
                    # # )
            else:
                break

    def goto_aa(
        self, target_alt_d, target_az_d, target_pa_d=0, target="optical_axis", deg=True
    ):
        """
        Point telescope to position using alt/az (i.e. point to screen or manually park)
        It does not run additional compensation based on astrometry.

        Comments and desired actions:
            Check dome safety interlock: if interlock is engaged, do not move the telescope.
            Return error message (assume people are inside dome)
            
            run status (LVMI_interface) to check instrument status: if not idle (i.e. carrying out any observations or calibrations),
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
            print_debug(self.amqpc, "(lvmagp) safety interlock engaged")
            raise LvmagpInterlockEngaged

        # Check status to confirm the system is in idle state?

        # Check the target is in reachable area
        alt_low, alt_high = define_visb_limit(target_az_d)
        if not (alt_low < target_alt_d) or not (target_alt_d < alt_high):
            print_debug(self.amqpc, "(lvmagp) Target is over the limit")
            raise LvmagpTargetOverTheLimit

        self._reset_offset_radec()

        # Calculate position angle and rotate K-mirror  :: should be changed to traj method.
        target_pa_d0 = (
            0  # I dont know ... # cal_pa(target_ra_h, target_dec_d, long_d, lat_d)
        )

        # invoke(
        self.derotate(target_pa_d0 + target_pa_d)
        self._slew_altaz(target_alt_d=target_alt_d, target_az_d=target_az_d),
        # )

        print_debug(self.amqpc, "(lvmagp) Initial slew completed")

    def goto_screen(self):
        """
        Point telescope to screen for dome flats

        Comments and desired actions:
            Check dome safety interlock: if interlock is engaged, do not move the telescope.
            Return error message (assume people are inside dome)

            run status (LVMI_interface) to check instrument status: if not idle (i.e. carrying out any observations or calibrations),
            repeat status command regularly until it returns idle,
            then move telescope. Regularly give updates
            (i.e. "waiting for instrument to become idle before moving telescope")

        """

        self.goto_aa(target_alt_d=usrpars.screen_alt_d, target_az_d=usrpars.screen_az_d)

    def goto_park(self):
        """
        Move telescope to safe park position.

        Comments and desired actions:
            Check dome safety interlock: if interlock is engaged, do not move the telescope. Return error message
            (assume people are inside dome)

            run status (LVMI_interface) to check instrument status: if not idle (i.e. carrying out any observations or calibrations),
            abort observation (halt in LVMI_interface) and park telescope
            (in this case, we assume user wants to park due to an emergency)

        """
        self.goto_aa(target_alt_d=usrpars.park_alt_d, target_az_d=usrpars.park_az_d)

    def goto_zenith(self):
        """
        Point telescope to zenith

        Comments and desired actions:
            Check dome safety interlock: if interlock is engaged, do not move the telescope.
            Return error message (assume people are inside dome)
            
            run status (LVMI_interface) to check instrument status: if not idle (i.e. carrying out any observations or calibrations),
            repeat status command regularly until it returns idle,
            then move telescope. Regularly give updates
            (i.e. "waiting for instrument to become idle before moving telescope")

        """
        self.goto_aa(target_alt_d=89.9999, target_az_d=180.)

    def track_on(self, derotator=True):
        '''
        Turn on tracking, optionally track in rotation, optionally
        supply non-sidereal track rates.

        Parameters
        ----------
        derotator
            If True, derotator will work to compensate the field rotation.
        '''
        self._set_tracking(enable=True)
        if derotator:
            pass  # do something to derotate the field

    def track_off(self):
        '''
        Turn off mount tracking and field derotating.
        '''

        self._set_tracking(enable=False)
        # do something to stop the derotator

    ############# Autoguide functions #########################
    def offset(
        self, delta_ra=None, delta_dec=None, delta_x=None, delta_y=None, delta_pa=None
    ):
        """
        Normal offset (for guiding): do NOT change track rates
        It returns applied offset values.

        Parameters
        ----------
        delta_ra
            Offset in ra direction in arcsecond (+/- = E/W)
        delta_dec
            Offset in dec direction in arcsecond(+/- = N/S)
        delta_x
            Offset in x direction in guide frame in pixel(+/- = R/L)
        delta_y
            Offset in y direction in guide frame in pixel (+/- = U/D)
        delta_pa
            Offset in position angle in degree (+/- = CW/CCW)
        """

        if (delta_ra is not None) or (delta_dec is not None):
            self._offset_radec(ra_arcsec=delta_ra, dec_arcsec=delta_dec)
            returnval = ['radec', delta_ra, delta_dec]

        if (delta_x is not None) or (delta_y is not None):
            P = np.array([1, -1])  # inversion matrix
            # (x-axis by right-hand coordinate to left-hand, y-axis by siderostat mirror)
            offset_xy = np.array([delta_x, delta_y])

            if self.name == 'sci':  # 20220401 'phot':
                #20220401
                theta = -self.siderostat.fieldAngle(self.site, self.target, ambi=None)
                print_debug(self.amqpc, f"field angle={np.rad2deg(theta)}")
   
                # theta = np.deg2rad(self.rotationangle)

                c, s = np.cos(theta), np.sin(theta)
                R = np.array([[c, -s], [s, c]])  # rotation matrix
            else:
                R = np.array([[1,0],[0,1]])

            offset_radec = np.dot(R, offset_xy) * self.pixelscale

            decj2000_deg = self._get_dec2000_deg()
            offset_radec[0] /= np.cos(np.deg2rad(decj2000_deg))
            offset_radec *= P

            self._offset_radec(ra_arcsec=offset_radec[0], dec_arcsec=offset_radec[1])
            returnval = ['radec', offset_radec[0], offset_radec[1]]

        if (delta_pa is not None):
            self._kmoffset(delta_pa)
            returnval = ['pa', delta_pa]

        return returnval


    def dither(self, delta_x=None, delta_y=None, delta_pa=None):
        """
        move the guider set points (guide boxes) by specified amount; used to move accurate
        offsets by letting the guider do the work. used, e.g., for dithering.

        Parameters
        ----------
        delta_x
            Offset in x direction in guide frame in pixel(+/- = R/L)
        delta_y
            Offset in y direction in guide frame in pixel (+/- = U/D)
        delta_pa
            Offset in position angle in degree (+/- = CW/CCW)
        """

        pass

    def guide_on(self, guide_parameters=None, ra_h=None, dec_d=None):
        '''
        Start guiding, or modify parameters of running guide loop.  <--- modify????
        guide_parameters is a dictionary containing additional parameters for
        the guiders, e.g. exposure times, cadence, PID parameters, readout or window modes, ...

        Parameters
        ----------
        useteldata
            If ``useteldata`` is flagged, the sequence will use the pixel scale and
            rotation angle from LVMTelescope.
            Otherwise, the sequence will get pixel scale from LVMCamera, and
            it assumes that the camera is north-oriented.
        guide_parameters
            exposure times, cadence, PID parameters, readout or window modes, ... ???
        '''
        if ra_h is not None and dec_d is not None:
            self.target = Target(SkyCoord(ra=ra_h*u.hourangle, dec=dec_d*u.degree))
        # if self.ag_on:
        #     pass #raise lvmagpguidealreadyrunning ?????

        self.ag_task = True
        print_debug(self.amqpc, "(lvmagp) Autoguide Start")

        try:
            t = Thread(target=self.autoguide_supervisor)
            # t.setDaemon(True)
            t.start()

        except Exception as e:
            print_error(self.amqpc, e)
            raise

        # finally:
        #         self.ag_task = None

        # return  self.amqpc.log.debug(f"{datetime.datetime.now()} | Guide stopped")


    def guide_off(self):
        '''
        Turn off guiding, revert to tracking (track_on).
        '''
        if self.ag_task is not None:
            self.ag_break = True
            self.ag_task = None
            return
        else:
            return print_error(self.amqpc, f"There is no autoguiding loop for telescope {self.name}")

    '''
    def calibration(self):
        """
        Run calibration sequence to calculate the transformation
        from the equatorial coordinates to the xy coordinates of the image.
        """

        offset_per_step = usrpars.ag_cal_offset_per_step
        num_step = usrpars.ag_cal_num_step

        decj2000_deg = self._get_dec2000_deg()

        xpositions, ypositions = [], []

        initposition, initflux = self.find_guide_stars()
        xpositions.append(initposition[:, 0])
        ypositions.append(initposition[:, 1])

        time.sleep(3)

        # dec axis calibration
        for step in range(1, num_step + 1):
            self._offset_radec(0, offset_per_step)
            position, flux = self.find_guide_stars(positionguess=initposition)
            xpositions.append(position[:, 0])
            ypositions.append(position[:, 1])

        self._offset_radec(0, -num_step * offset_per_step)

        xoffsets = np.array(xpositions) - xpositions[0]
        yoffsets = np.array(ypositions) - ypositions[0]

        print(xpositions)
        print(xoffsets)
        print(ypositions)
        print(yoffsets)

        xscale_dec = (
                np.average(xoffsets[1:] / np.array([[i] * 3 for i in range(1, num_step + 1)])) /
                offset_per_step
        )  # displacement along x-axis by ra offset in pixel per arcsec. exclude the first index (0,0)
        yscale_dec = (
                np.average(yoffsets[1:] / np.array([[i] * 3 for i in range(1, num_step + 1)])) /
                offset_per_step
        )  # exclude the first index (0,0)

        # ra axis calibration
        xpositions = [initposition[:, 0]]
        ypositions = [initposition[:, 1]]

        for step in range(1, num_step + 1):
            self._offset_radec(
                offset_per_step / np.cos(np.deg2rad(decj2000_deg)), 0
            )
            position, flux = self.find_guide_stars(positionguess=initposition)
            xpositions.append(position[:, 0])
            ypositions.append(position[:, 1])

        self._offset_radec(
            -num_step * offset_per_step / np.cos(np.deg2rad(decj2000_deg)), 0
        )

        xoffsets = np.array(xpositions) - xpositions[0]
        yoffsets = np.array(ypositions) - ypositions[0]

        print(xpositions)
        print(xoffsets)
        print(ypositions)
        print(yoffsets)

        xscale_ra = (
                np.sum(xoffsets[1:] / np.array([[i] * 3 for i in range(1, num_step + 1)]))
                / offset_per_step
        )  # exclude the first index (0,0)
        yscale_ra = (
                np.sum(yoffsets[1:] / np.array([[i] * 3 for i in range(1, num_step + 1)]))
                / offset_per_step
        )  # exclude the first index (0,0)

        self.scale_matrix = np.linalg.inv(
            np.array([[xscale_ra, xscale_dec], [yscale_ra, yscale_dec]])
        )  # inverse matrix.. linear system of equations..

        return self.amqpc.log.debug(
            f"{datetime.datetime.now()} |"+
            f'xscale_ra={xscale_ra} pixel/arcsec'+
            f'yscale_ra={yscale_ra} pixel/arcsec'+
            f'xscale_dec={xscale_dec} pixel/arcsec'+
            f'yscale_dec={yscale_dec} pixel/arcsec'
        )
    '''

    def autoguide_supervisor(self):
        """
        Manage the autoguide sequence.
        It starts real autoguide loop and keeps it until the break signal comes.

        Parameters
        ----------
        tel
            Telescope to autoguide
        """
        initposition, initflux = self.find_guide_stars()

        while 1:
            print_debug(self.amqpc, "autoguiding loop Start")
            
            self.autoguiding(
                initposition,
                initflux
            )
            
            print_debug(self.amqpc, "autoguiding loop Done")

            if self.ag_break:
                self.ag_break = False
                break

        return True

    def find_guide_stars(self, positionguess=None):
        """
        Expose an image, and find three guide stars from the image.
        Also calculate the center coordinates and fluxes of found stars.

        Parameters
        ----------
        positionguess
            Initial guess of guidestar position.
            It should be given in np.ndarray as [[x1, y1], [x2, y2], ...]
            If ``positionguess`` is not None, ``find_guide_stars`` only conduct center finding
            based on ``positionguess`` without finding new stars.
        """

        # take an image for astrometry
        print_debug(self.amqpc, "Taking image...")

        try:
            # guideimgpath = [
            #    self.agw.single_exposure(usrpars.ag_exptime),
            #    self.age.single_exposure(usrpars.ag_exptime)
            # ]

            print_debug(self.amqpc, f"{self.agw.camname} exposure started")
            print_debug(self.amqpc, f"{self.age.camname} exposure started")

            guideimgpath = invoke(
                self.agw._cam.async_expose(usrpars.aqu_exptime, 1, self.agw.camname),
                self.age._cam.async_expose(usrpars.aqu_exptime, 1, self.age.camname)
            )
            guideimgpath = [guideimgpath[0]["PATH"]["0"], guideimgpath[1]["PATH"]["0"]]

            print_debug(self.amqpc, f"{self.agw.camname} exposure done")
            print_debug(self.amqpc, f"{self.age.camname} exposure done")

        except Exception as e:
            print_error(self.amqpc, e)
            raise

        westguideimg = GuideImage(guideimgpath[0])
        eastguideimg = GuideImage(guideimgpath[1])

        if positionguess is None:
            starposition = westguideimg.findstars()
        else:
            westguideimg.guidestarposition = positionguess
            westguideimg.update_guidestar_properties()
            starposition = westguideimg.guidestarposition
        starflux = westguideimg.guidestarflux

        return starposition, starflux

    def autoguiding(self, initposition,
            initflux,
    ):
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
        """

        #self._pwi.offset(ra_add_arcsec=3, dec_add_arcsec=-2)
        
        #time.sleep(1)

        starposition, starflux = self.find_guide_stars(
            positionguess=initposition,
        )

        print_debug(self.amqpc, f'initposition = {initposition} | initflux = {initflux}')
        print_debug(self.amqpc, f'starposition = {starposition} | starflux = {starflux}')


        if (
                np.abs(
                    np.average(starflux / initflux - 1, weights=2.5 * np.log10(initflux * 10))
                )
                > usrpars.ag_flux_tolerance
        ):
            return print_error(self.amqpc, 
                "Star flux variation %.3f is too large."
                % np.abs(
                    np.average(
                        starflux / initflux - 1, weights=2.5 * np.log10(initflux * 10)
                    )
                )
            )

        offset = np.mean(starposition - initposition, axis=0)  # in x,y [pixel]

        if (np.sqrt(offset[0] ** 2 + offset[1] ** 2)) > usrpars.ag_min_offset:
            correction = self.offset(delta_x=-offset[0], delta_y=-offset[1])

            print_debug(self.amqpc, 
                "compensate signal: ra %.2f arcsec dec %.2f arcsec   x %.2f pixel y %.2f pixel"
                % (correction[1], correction[2], -offset[0], -offset[1])
            )

            return correction[1:3]

        else:
            return [0.0, 0.0]

    def zero_coordinates(self):
        '''
        Zero-out mount model once pointing is verified.
        '''
        pass  #what is this?

    def check_safety_interlock(self):
        pass
