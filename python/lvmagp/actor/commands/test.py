from lvmagp.actor.commfunc import LVMTelescopeUnit

sci = LVMTelescopeUnit("sci")

sci.fine_autofocus()
sci.goto_eq(8, -38)
sci.guide_on()

import time
def my_exposure(exptime):
    print("my_exposure Start")
    time.sleep(exptime)
    print("my_exposure Done")
    return True 

res = my_exposure(60)

if (res): 
    sci.guide_off()