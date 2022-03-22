import time
import signal

import multiprocessing

class LVMTelescopeUnit():
    def __init__(self, tel):
        self.tel = tel
        # self.ag_task = None
        self.ag_break = False
        self.proc = None

    def handler(self, signum, frame):
        self.guide_off()

    def autoguide_supervisor(self, msg):
        while True:
            self.autoguiding(msg)
            if self.ag_break: break

    def autoguiding(self, msg):
        time.sleep(1)
        print(msg)

    def guide_on(self, timeout=None):
        # self.ag_task = True
        print(f"{self.tel} | Autoguide Start")

        try:
            signal.signal(signal.SIGINT, self.handler)
            if timeout is not None:
                signal.signal(signal.SIGALRM, self.handler)
                signal.alarm(timeout)
            self.proc = multiprocessing.Process(target=self.autoguide_supervisor, args=(f"{self.tel} | Autoguiding...", ))
            self.proc.start()
        except:
            raise Exception
        # finally:
        #     self.ag_task = None 
        
        # if not self.proc.is_alive():
        #     return print(f"{self.tel} | Autoguide Done")

    def guide_off(self, proc=None):

        if self.proc is not None:
            try:
                self.proc.terminate()
            except:
                raise Exception
        
        # if self.ag_task is not None:
        #     self.ag_break = True
        # else:
        #     raise Exception

    def expose(self, exptime):
        print(f"{self.tel} | Expose Start")
        time.sleep(exptime)
        print(f"{self.tel} | Expose Done")
        self.guide_off()


if  __name__ == '__main__' :
    start = time.perf_counter()

    sci = LVMTelescopeUnit("sci")
    # aaa = LVMTelescopeUnit("aaa")

    # p = multiprocessing.Process(target=sci.guide_on)
    # p = multiprocessing.Process(target=sci.guide_on, args=(5,))
    # p.start()
   
    # aaa.expose(1)
    # p.join()
    sci.guide_on()
    sci.expose(5)

    
    finish = time.perf_counter()
    print(f'Finished in {round(finish-start, 2)} second(s)')