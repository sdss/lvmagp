from lvmagp.actor.commfunc import LVMTelescopeUnit

import time
def my_exposure(exptime):
    print("my_exposure Start")
    time.sleep(exptime)
    print("my_exposure Done")
    return True 

sci = LVMTelescopeUnit("sci", sitename="KHU")

# autofocus
#sci.fine_autofocus()

# slew
sci.goto_eq(12.7897, 23.945)

# autoguide
sci.guide_on(ra_h=12.7897, dec_d=23.945)

# kill autoguide loop
res = my_exposure(90)
if (res):
    sci.guide_off()
