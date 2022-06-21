import os
import time
from pathlib import Path 
import numpy as np
import cv2

from config import config
from projector import Projector
from camera import HK_Camera


class Capture():
    def __init__(self, config):
        self._c = config
        self.prj = Projector(config)
        self.hkc = HK_Camera()
        self.hkc.start()

    def capture_one(self, path, hv="h"):
            i = 0
            prj_flag = True
            while prj_flag:
                prj_flag = self.prj.update(hv)
                time.sleep(8/24)
                self.prj.black()
                self.hkc.capture_one(name=path + f"{i:0>2d}{hv}.bmp")
                i+=1

    def calibra_capture(self):
        count = 0
        root = Path(self._c.calibra_path)
        root.mkdir(parents=True, exist_ok=True)
        while self.prj.wait_to_begin():
            self.capture_one(str(root)+ f"/{count:0>2d}_", hv="h")
            self.capture_one(str(root)+ f"/{count:0>2d}_", hv="v")
            count +=1


    def measure_capture(self):
        count = 0
        root = Path(self._c.measure_path)
        root.mkdir(parents=True, exist_ok=True)
        while self.prj.wait_to_begin():
            self.capture_one(str(root)+ f"/{count:0>2d}", hv="h")
            count +=1


    def exit(self):
        self.prj.exit()
        self.hkc.exit()

from config import config
cfg = config()  

cap = Capture(cfg)
# cap.calibra_capture()
cap.measure_capture()

cap.exit()



