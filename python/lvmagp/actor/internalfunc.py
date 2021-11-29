import asyncio
import warnings
from datetime import datetime

import numpy as np
# import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.modeling import fitting, models
from astropy.stats import sigma_clipped_stats
from astropy.time import Time
from photutils.detection import DAOStarFinder
from scipy.spatial import KDTree


class GuideImage:
    def __init__(self, filepath):
        self.filepath = filepath
        self.nstar = 3
        self.initFWHM = 3
        self.FWHM = -999
        self.hdu = fits.open(self.filepath)
        self.data, self.hdr = self.hdu[0].data, self.hdu[0].header
        self.mean, self.median, self.std = sigma_clipped_stats(self.data, sigma=3.0)
        self.guidestarposition = []
        self.ra2000 = -999
        self.dec2000 = -999
        self.pa = -999
        self.fov = -999
        self.pixelscale = -999

    def findstars(self, nstar=3):
        daofind = DAOStarFinder(
            fwhm=self.initFWHM, threshold=3.0 * self.std, peakmax=60000 - self.median
        )  # 1sigma = FWHM/(2*sqrt(2ln2)); FWHM = sigma * (2*sqrt(2ln2))
        sources = daofind(self.data[10:-10, 10:-10] - self.median)
        posnflux = np.array(
            [sources["xcentroid"], sources["ycentroid"], sources["flux"]]
        )  # xcoord, ycoord, flux
        sortidx = np.argsort(-posnflux[2])
        posnflux = np.array(
            [posnflux[0, sortidx], posnflux[1, sortidx], posnflux[2, sortidx]]
        )

        positions = np.transpose((posnflux[0], posnflux[1]))

        self.liststarpass = []
        for i in range(len(positions[:, 0])):
            positions_del = np.delete(positions, i, 0)
            kdtree = KDTree(positions_del)
            dist, idx = kdtree.query(positions[i])
            if dist > 5.0 * self.initFWHM:
                self.liststarpass.append(i)
            if len(self.liststarpass) >= nstar:
                break

        self.guidestarposition = positions[self.liststarpass]

        if (
            len(self.liststarpass) != nstar
        ):  # if there does not exist sufficient stars, just use 1 star.
            self.guidestarposition = self.guidestarposition[0, :]
        self.nstar = len(self.guidestarposition)
        return self.guidestarposition  # list ; [[x1, y1], [x2, y2], [x3, y3]]

    def twoDgaussianfit(self):
        windowradius = 5  # only integer
        plist = []

        for i in range(len(self.guidestarposition[:, 0])):
            xcenter = int(self.guidestarposition[i, 0])
            ycenter = int(self.guidestarposition[i, 1])
            p_init = models.Gaussian2D(amplitude=10000, x_mean=xcenter, y_mean=ycenter)
            fit_p = fitting.LevMarLSQFitter()
            xrange = np.arange(xcenter - windowradius, xcenter + windowradius)
            yrange = np.arange(ycenter - windowradius, ycenter + windowradius)
            X, Y = np.meshgrid(xrange, yrange)
            X = np.ravel(X)
            Y = np.ravel(Y)
            Z = np.ravel(
                (self.data - self.median)[
                ycenter - windowradius: ycenter + windowradius,
                xcenter - windowradius: xcenter + windowradius,
                ]
            )

            with warnings.catch_warnings():
                # Ignore model linearity warning from the fitter
                warnings.simplefilter("ignore")
                p = fit_p(p_init, X, Y, Z)
                plist.append(p)
        return plist

    def calflux(self):
        if len(self.guidestarposition) == 0:
            pass

        starfluxlist = []
        plist = self.twoDgaussianfit()

        for p in plist:
            starfluxlist.append(p.amplitude)
        return starfluxlist


    def calfwhm(self):
        if len(self.guidestarposition) == 0:
            pass

        starsizelist = []
        plist = self.twoDgaussianfit()

        for p in plist:
            starsizelist.append((p.x_fwhm, p.y_fwhm))

        self.FWHM = np.median(np.array(starsizelist))  # float
        return self.FWHM

    async def astrometry(self, ra_h=-999, dec_d=-999):
        ospassword = "0000"
        resultpath = "/home/hojae/Desktop/lvmagp/testimg/astrometry_result/result.txt"
        timeout = 5
        scalelow = 0.9
        scalehigh = 1.1
        radius = 1

        if ra_h == -999:
            cmd = (
                "echo %s | sudo -S /usr/local/astrometry/bin/solve-field %s --cpulimit %f --overwrite \
            --downsample 2 --no-plots > %s"
                % (ospassword, self.filepath, timeout, resultpath)
            )

        else:
            cmd = "echo %s | sudo -S /usr/local/astrometry/bin/solve-field %s --cpulimit %f --overwrite \
            --downsample 2 --scale-units arcsecperpix --scale-low %f --scale-high %f --ra %f --dec %f \
            --radius %f --no-plots > %s" % (  # noqa: E501
                ospassword,
                self.filepath,
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

        with open(resultpath, "r") as f:
            result = f.readlines()

        for line in result[::-1]:
            if "Field center: (RA,Dec)" in line:
                startidx = line.find("(", 25)
                mididx = line.find(",", 25)
                endidx = line.find(")", 25)

                self.ra2000 = float(line[startidx + 1: mididx])
                self.dec2000 = float(line[mididx + 1: endidx])

            elif "Field rotation angle" in line:
                startidx = line.find("is")
                endidx = line.find("degrees")

                if line[endidx + 8] == "E":
                    self.pa = float(line[startidx + 3: endidx - 1])
                elif line[endidx + 8] == "W":
                    self.pa = 360 - float(line[startidx + 3: endidx - 1])

            elif "Total CPU time limit reached!" in line:
                raise Exception("Astrometry timeout")

        return True


def findfocus(positions, FWHMs):  # both are lists or np.array
    t_init = models.Polynomial1D(degree=2)
    fit_t = fitting.LinearLSQFitter()
    t = fit_t(t_init, positions, FWHMs)
    bestposition = -t.c1 / (2 * t.c2)
    bestfocus = t(bestposition)
    return (bestposition, bestfocus)


def cal_pa(ra_h, dec_d, long_d, lat_d):
    dec = np.deg2rad(dec_d)
    lat = np.deg2rad(lat_d)

    t = Time(datetime.utcnow(), scale="utc", location=(long_d, lat_d))
    LST = t.sidereal_time("apparent").value * 15
    HA = np.mod(LST - ra_h * 15, 360)
    pa = np.arctan(
        -np.sin(np.deg2rad(HA)) / (np.cos(dec) * np.tan(lat) - np.sin(dec) * np.cos(np.deg2rad((HA))))
    )

    return np.rad2deg(pa)


def star_altaz(ra_h, dec_d, long_d, lat_d):
    dec = np.deg2rad(dec_d)
    lat = np.deg2rad(lat_d)

    # CALC. the hour angle
    t = Time(datetime.utcnow(), scale="utc", location=(long_d, lat_d))
    LST = t.sidereal_time("apparent").value * 15
    HA = np.mod(LST - ra_h * 15, 360)
    # CALC. the altitude and azimuth
    sin_ALT = np.sin(dec) * np.sin(lat) + np.cos(dec) * np.cos(lat) * np.cos(
        np.deg2rad(HA)
    )
    ALT = np.rad2deg(np.arcsin(sin_ALT))
    cos_AZI = (np.sin(dec) - np.sin(np.deg2rad(ALT)) * np.sin(lat)) / (
        np.cos(np.deg2rad(ALT)) * np.cos(lat)
    )
    AZI = np.mod(np.rad2deg(np.arccos(cos_AZI)), 360)
    # CORR. the azimuth value for HA
    if HA < 180:
        AZI = 360 - AZI

    return ALT, AZI


def define_visb_limit(Az):  # or Hour angle..?
    # input any condition ..
    alt_low = 30
    alt_high = 90
    return alt_low, alt_high


def check_target(ra_h, dec_d, long_d, lat_d):
    alt, az = star_altaz(ra_h, dec_d, long_d, lat_d)
    alt_low, alt_high = define_visb_limit(az)
    if (alt_low < alt) and (alt < alt_high):
        return True
    else:
        return False


async def send_message(command, actor, command_to_send, returnval=False, body=""):
    cmd = await command.actor.send_command(actor, command_to_send)
    cmdwait = await cmd

    if cmdwait.status.did_fail:
        return False

    if returnval:
        return cmdwait.replies[-1].body[body]

    return True


"""
if __name__ == "__main__":
    guideimglist = [
        "/home/hojae/Desktop/lvmagp/testimg/focus_series/
        synthetic_image_median_field_5s_seeing_02.5.fits", #
        "/home/hojae/Desktop/lvmagp/testimg/focus_series/
        synthetic_image_median_field_5s_seeing_03.0.fits",
        "/home/hojae/Desktop/lvmagp/testimg/focus_series/
        synthetic_image_median_field_5s_seeing_06.0.fits",
    ]
    guideimgidx = [1, 0, 1, 2]

    guideimg = GuideImage(guideimglist[2])
    FWHM = guideimg.calfwhm(findstar=True)
    print(FWHM)


    position = range(29000,31100,100)
    focus = [40.5,36.2,31.4,28.6,23.1,21.2,16.6,13.7,6.21,4.21,3.98,4.01,4.85,11.1,15.3,22.1,21.9,27.4,32.1,36.5,39.7]  # noqa: E501
    pos, foc = findfocus(position, focus)
    print (pos,foc)
"""