from lvmagp.actor.commfunc import LVMTelescopeUnit

import time
def my_exposure(exptime):
    print("my_exposure Start")
    time.sleep(exptime)
    print("my_exposure Done")
    return True 

sci = LVMTelescopeUnit("sci")

# autofocus
sci.fine_autofocus()

# slew
sci.goto_eq(11, -25)

# autoguide
sci.guide_on()

# kill autoguide loop
res = my_exposure(10)
if (res): 
    sci.guide_off()