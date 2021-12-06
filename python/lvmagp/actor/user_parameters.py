class usrpars():
    # location  -- it is in lvmagp.yml..
    #latitude = 0
    #longitude = 0


    # autofocus parameters


    # acquisition parameters
    aqu_exptime = 5  # exposure time for acquisition in seconds
    aqu_max_iter = 2  # maximum iteration of astrometry compensation
    aqu_tolerance_arcsec = 30.0  # maximum tolerable angular distance between target coordinates and aquisited coordinates

    # autoguide parameters
    ag_exptime = 3  # exposure time for autoguide in seconds
    ag_halfboxsize = 15  # 1/2 of box in pixel
    #ag_minsnr = 6
    ag_min_offset = 0.3  # minimum offset to do correction in pixel
    ag_flux_tolerance = 0.3  # maximum variability of flux due to seeing to identify the guide star

    ag_cal_offset_per_step = 3.0  # Step size for calibration in arcseconds
    ag_cal_num_step = 3  # number of steps of calibration per axis



