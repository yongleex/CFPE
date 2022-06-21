import numpy as np 
import cv2
from pathlib import Path


# synthetic fringe images
class Fringes():
    def __init__(self, config):
        self._c = config

    def generate_bg(self):
        W, H = self._c.pattern_size
        img = np.zeros([H, W])
        return img+self._c.light_value

    def generate_one(self, zeta, T, A, B):
        W, H = self._c.pattern_size
        img = np.zeros([H, W])
        x = np.linspace(0,W-1,W) if self._c.hv == "h" else np.linspace(0,H-1,H).reshape(-1,1) 
        y = A+B*np.cos(2*np.pi*x/T+zeta) 
        return img+y
    
    def generate_steps(self, T, A, B, step):
        assert step >= 3

        zeta_s = np.linspace(0, step-1, step)*2*np.pi/step
        images = list()
        for zeta in zeta_s:
            images.append(self.generate_one(zeta, T, A, B))
        return images
    
    def generate_all(self):
        images = list()
        for T, A, B, step in zip(self._c.Tp, self._c.A, self._c.B, self._c.steps):
            fringes = self.generate_steps(T, A, B, step)
            images.append(fringes)
        # images.append(self.generate_bg)
        return images

    def save_images(self):
        images = self.generate_all()
        root = self._c.pattern_path
        for f, fringes in enumerate(images):
            for s, fringe in enumerate(fringes):
                p = Path(root)/f"{f:0>2d}{s:0>2d}{self._c.hv}.bmp" 
                cv2.imwrite(str(p), fringe)
        img = self.generate_bg()
        p = Path(root)/f"bg.bmp" 
        cv2.imwrite(str(p), img)


    def generate_phase(self):
        W, H = self._c.pattern_size
        img = np.zeros([H, W])
        x = np.linspace(0,W-1,W)
        phase = img+2*np.pi*x/self._c.Tp[0]
        return phase
    
    
class Fringes_Seg(Fringes):
    def __init__(self, config):
        super().__init__(config)
        self.init_T123()
        
    def init_T123(self):
        mT = lambda T1, T2: T1*T2/(T2-T1)
        T12 = mT(self._c.Tp[0],self._c.Tp[1])
        T23 = mT(self._c.Tp[1],self._c.Tp[2])
        T123 = mT(T12, T23)
        T1 = self._c.Tp[0]
        
        # obtain the del index
        indT = np.round(np.arange(np.round(T1))-T1/2).astype(np.int32)
        seg = np.linspace(0, T123, self._c.steps[0]+1)
        ind = (indT.reshape(1,-1)+seg.reshape(-1,1)).flatten()
        ind = np.round(ind).astype(np.int32) 
        
        mask = (ind>-1)*(ind<self._c.pattern_size[0])
        self.ind = ind[mask]        
        
    def generate_one(self, zeta, T, A, B):
        self._c.pattern_size[0] +=200
        y = super().generate_one(zeta,T,A,B)
        self._c.pattern_size[0] -=200
        y = np.delete(y, self.ind, 1)
        y = y[:,0:(self._c.pattern_size[0])]
        return y
        
    
class Fringes_Gamma(Fringes):
    def __init__(self, config):
        super().__init__(config)
    def generate_one(self, zeta, T, A, B):
        y = super().generate_one(zeta,T,A,B)
        y = 255*np.power(y/255, self._c.gamma) 
        y = np.round(y)
        return y 
    
    
class Fringes_Harmonics(Fringes):
    def __init__(self, config):
        super().__init__(config)
    def generate_one(self, zeta, T, A, B):
        W, H = self._c.pattern_size
        img = np.zeros([H, W])
        # x = np.linspace(0,W-1,W)
        x = np.linspace(0,W-1,W) if self._c.hv == "h" else np.linspace(0,H-1,H).reshape(-1,1) 
        phi = 2*np.pi*x/T+zeta
        y = A+B*np.cos(phi)
        h = self._c.C*np.cos(2*phi)+self._c.D*np.cos(4*phi)
        return np.round(img+y+h)
 
def fringe_wrapper(cfg, method):
    assert method in ["fringe","gamma","harmonic", "seg"]
    d = {"fringe":Fringes,"gamma":Fringes_Gamma,"harmonic":Fringes_Harmonics,"seg":Fringes_Seg}
    return d[method](cfg)
    
    
def projection_fringes_save():
    from config import config
    cfg = config()  

    cfg.hv="h"
    Fringes(cfg).save_images() 
    cfg.hv="v"
    Fringes(cfg).save_images() 
    

if __name__ == '__main__':
    projection_fringes_save()
