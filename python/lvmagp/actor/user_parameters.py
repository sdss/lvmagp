class usrpars():
    # location  -- it is in lvmagp.yml..
    #latitude = 0
    #longitude = 0


    # autofocus parameters


    # aquisition parameters
    aqu_exptime = 5  #in seconds
    aqu_max_iter = 2
    aqu_tolerance_arcsec = 30.0

    # autoguide paramters
    ag_exptime = 3
    ag_halfboxsize = 15  # 1/2 of box in pixel
    ag_minsnr = 6
    ag_min_offset = 0.3  # minimum offset to do correction in pixel
    ag_flux_tolerance = 0.2  # maximum variability of flux due to seeing to identify the guide star



