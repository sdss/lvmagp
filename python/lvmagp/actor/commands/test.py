from lvmagp.actor.commfunc import LVMTelescopeUnit

sci = LVMTelescopeUnit("sci")

# sci.fine_autofocus()

# sci.goto_aa(58, 315)
sci.goto_eq(12.2, -17.5)

# print(sci.find_guide_stars())
# sci.track_off()
# sci.track_on()
sci.guide_on()
# sci.calibration()

