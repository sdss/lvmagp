class usrpars:
    # special positions
    screen_alt_d = -999
    screen_az_d = -999
    park_alt_d = -999
    park_az_d = -999

    # autofocus parameters
    af_incremental = 10000  # step size for each movement
    af_repeat = 5  # the number of steps
    af_exptime = 3  # in seconds

    # acquisition parameters
    aqu_exptime = 5  # exposure time for acquisition in seconds
    aqu_max_iter = 2  # maximum iteration of astrometry compensation
    aqu_tolerance_arcsec = 30.0  # maximum tolerable position error

    # autoguide parameters
    ag_exptime = 3  # exposure time for autoguide in seconds
    ag_halfboxsize = 15  # 1/2 of box in pixel
    # ag_minsnr = 6
    ag_min_offset = 0.3  # minimum offset to do correction in pixel
    ag_flux_tolerance = (
        0.3  # maximum variability of flux due to seeing to identify the guide star
    )

    ag_cal_offset_per_step = 5.0  # Step size for calibration in arcseconds
    ag_cal_num_step = 3  # number of steps of calibration per axis

    pixelscale = 1.01
    offset_x = 0.0
    offset_y = 0.0
    rotationangle = 140.0


def temp_vs_focus(temperature):
    """
    Returns estimation of focus position in steps unit for input temperature

    Parameters
    ----------
    temperature
        Target temperature in Celsius
    """
    pos = temperature  # here put a relation between temperature (Celsius) and focus position (step)  # noqa: E501
    return pos
