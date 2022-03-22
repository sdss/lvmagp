import time
import signal

import threading

class LVMTelescopeUnit():
    def __init__(self, tel):
        self.tel = tel
        self.ag_break = False
        # self.proc = None

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
        print(f"{self.tel} | Autoguide Start")

        try:
            signal.signal(signal.SIGINT, self.handler)
            if timeout is not None:
                signal.signal(signal.SIGALRM, self.handler)
                signal.alarm(timeout)
            t = threading.Thread(target=self.autoguide_supervisor, args=(f"{self.tel} | Autoguiding...", ))
            t.setDaemon(True)
            t.start()
        except:
            raise Exception


    def guide_off(self, proc=None):
        self.ag_break = True
        # if self.proc is not None:
        #     try:
        #         self.proc.terminate()
        #     except:
        #         raise Exception
    

    def expose(self, exptime):
        print(f"{self.tel} | Expose Start")
        time.sleep(exptime)
        print(f"{self.tel} | Expose Done")
        self.guide_off()


if  __name__ == '__main__' :
    start = time.perf_counter()

    sci = LVMTelescopeUnit("sci")

    sci.guide_on()
    sci.expose(5)

    
    finish = time.perf_counter()
    print(f'Finished in {round(finish-start, 2)} second(s)')