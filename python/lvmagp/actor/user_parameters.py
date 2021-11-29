class usrpars():
    def __init__(self):
        # location  -- it is in lvmagp.yml..
        #self.latitude = 0
        #self.longitude = 0


        # autofocus parameters


        # aquisition parameters
        self.aqu_exptime = 5  #in seconds
        self.aqu_max_iter = 1
        self.aqu_tolerance_arcsec = 30.0

        # autoguide paramters
        self.ag_exptime = 3
        self.ag_halfboxsize = 15  # 1/2 of box in pixel
        self.ag_minsnr = 6
        self.ag_min_offset = 0.3  # minimum offset to do correction in pixel
        self.ag_flux_tolerance = 0.2  # maximum variability of flux due to seeing to identify the guide star



