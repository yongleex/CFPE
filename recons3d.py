import numpy as np
import cv2
from pathlib import Path
import matplotlib.pyplot as plt

from phase import *
from calibration import Calibrator


ply_header = '''ply
format ascii 1.0
element vertex %(vert_num)d
property float x
property float y
property float z
end_header
'''


class Recons3D():
    def __init__(self, cfg):
        self._c = cfg
        self.calibrator = Calibrator(self._c)
        self.map_c1, self.map_c2, self.phase_rectified, self.Q = self.calibrator.load()

        self.pe = eval(self._c.pe_method)(self._c)
        
        self.shape = self.phase_rectified.shape

        
    def measure(self, images, gray):
        phase, _ = self.pe.phase_extract(images)
        phase = cv2.remap(phase, self.map_c1, self.map_c2, cv2.INTER_LINEAR)
        
        gray = cv2.remap(gray, self.map_c1, self.map_c2, cv2.INTER_CUBIC)
        gray_mask = gray<35
        
        s_x, s_y = np.meshgrid(np.arange(self.shape[1]), np.arange(self.shape[0]))
        s_x, s_y = s_x.astype(np.float32), s_y.astype(np.float32)
        x = np.zeros_like(self.phase_rectified).astype(np.float32)
        
        alpha = 0.9
        for i in range(10):
            alpha *= 0.9
            wp = cv2.remap(self.phase_rectified, s_x-x, s_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            diff = wp-phase
            if i<5:
                diff = cv2.blur(diff, (3,3))
            x = x + alpha*diff.astype(np.float32)
        disp = x
          
        mask = disp< -50
        disp[mask]= np.nan
        mask = disp> 350
        disp[mask]= np.nan
        disp[gray_mask]= np.nan
            
        self.points = cv2.reprojectImageTo3D(disp.astype(np.float32), self.Q)
        # self.points = self.points[45:-35, 40:-5,:]
        
        if self._c.debug:
            plt.figure(figsize=(16,6))
            plt.subplot(1,2,1)
            plt.imshow(phase)
            plt.colorbar()
            plt.title("phase measured")
            plt.subplot(1,2,2)
            plt.imshow(self.phase_rectified)
            plt.colorbar()
            plt.title("phase rectified")

            plt.figure(figsize=(16,6))
            plt.imshow(disp)
            plt.colorbar()
            plt.title("disparity")
        return phase, self.points

    def remap(self, img):
        return cv2.remap(img, self.map_c1, self.map_c2, cv2.INTER_CUBIC)

    def save_points(self, fn, points=None):
        # if points is not None
            # verts = points 
        # else: 
        verts = self.points if points is None else points
        # verts = self.points.reshape(-1, 3)
        verts  = verts.reshape(-1,3)
        mask = ~np.isnan(np.sum(verts, axis=-1))
        verts = verts[mask]
        # verts[np.isnan(verts)] = 0.00
        with open(fn, 'wb') as f:
            f.write((ply_header % dict(vert_num=len(verts))).encode('utf-8'))
            np.savetxt(f, verts, fmt='%f %f %f')