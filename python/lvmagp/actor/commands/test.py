from lvmagp.actor.commfunc import LVMTelescopeUnit

sci = LVMTelescopeUnit("sci")

# sci.fine_autofocus()

sci.goto_aa(58, 315)
# sci.goto_eq(22.5, -10.5)

# print(sci.find_guide_stars())
# sci.guide_on()
# sci.calibration()

