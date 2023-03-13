# 2 choices

# 1. with simulator on nicelab, user lvm
#   RMQ_HOST=$(minikube ip) ipython3
#   paste the code

# 2. local with image eg from nicelab:
#   /data/lvm/sci/agcam/east/20220927/lvm.sci.agcam.east_00003730.fits
#    python > 3.8
#    pip3 install sdss-lvmagp astrometry
#    ipython3

from logging import DEBUG

import astropy.wcs

from sdsstools import get_logger
from sdsstools.logger import StreamFormatter

from lvmagp.images import Image
from lvmagp.images.processors.detection import SepSourceDetection


log = get_logger("astro")
log.sh.setLevel(DEBUG)
log.sh.formatter = StreamFormatter(
    fmt="%(asctime)s %(name)s %(levelname)s %(filename)s:%(lineno)d: \033[1m%(message)s\033[21m"
)
log.debug("test")

import astrometry


solver = astrometry.Solver(
    astrometry.series_5200.index_files(
        cache_directory="/data/astrometrynet",
        scales={6},
    )
)

# source_detection = DaophotSourceDetection()
source_detection = SepSourceDetection()

# only first iteration
logodds_callback = astrometry.Action.STOP
# full
# logodds_callback = astrometry.Action.CONTINUE

#  choice 1.
log.debug("Expose")

tssn = "sci"
exptime = 3.0

telsubsys = await lvm.from_string(tssn).start()
rc = await telsubsys.agc.expose(exptime)
images = [Image.from_file(v["filename"]) for k, v in rc.items()]


# choice 2.
log.debug("Load")
filename = "/data/lvm/sci/agcam/east/20220927/lvm.sci.agcam.east_00003730.fits"

images = [Image.from_file(filename)]

log.debug("Detect")
source_count = 17

image = source_detection(images[0])
arcsec_per_pixel = 1 / image.header["PIXELSC"] * image.header["BINX"]

if image.catalog is None:
    log.warning("No catalog found in image.")

log.debug("Sort")
sources = image.catalog
sources.sort("peak")
sources.reverse()
sources = sources[:source_count]

log.debug("Solve start")
solution = solver.solve(
    stars_xs=sources["x"],
    stars_ys=sources["y"],
    size_hint=astrometry.SizeHint(
        lower_arcsec_per_pixel=arcsec_per_pixel - 0.1,
        upper_arcsec_per_pixel=arcsec_per_pixel + 0.1,
    ),
    position_hint=astrometry.PositionHint(
        ra_deg=image.header["RA"],
        dec_deg=image.header["DEC"],
        radius_deg=1,
    ),
    solve_id=None,
    tune_up_logodds_threshold=14.0,  # None disables tune-up (SIP distortion)
    output_logodds_threshold=21.0,
    logodds_callback=lambda logodds_list: logodds_callback,
)
log.debug("Solve done")

if solution.has_match():
    print(f"{solution.best_match().center_ra_deg=}")
    print(f"{solution.best_match().center_dec_deg=}")
    print(f"{solution.best_match().scale_arcsec_per_pixel=}")
    wcs = astropy.wcs.WCS(solution.best_match().wcs_fields)
    pixels = wcs.all_world2pix(
        [[star.ra_deg, star.dec_deg] for star in solution.best_match().stars],
        0,
    )
    print(f"{wcs}")
