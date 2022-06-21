"""
The phase extraction methods in this work
- standard phase extraction (PE) method
- the baseline method (LLS) 
- our cross-frequency phase extraction (CFPE)
- one multifrequency phase extraction (MPE) method --- ablation method of our CFPE
"""
import numpy as np
import cv2


# standard phase extractor (PE)
class PE():
    def __init__(self, config):
        self._c = config
        
    def psi_extract(self, images):
        """The wrapped phase: psi"""
        steps = len(images)
        den, num = 0,0
        for step in range(steps):
            num += np.sin(2*np.pi*step/steps)*images[step]
            den += np.cos(2*np.pi*step/steps)*images[step]
        psi = np.mod(-np.arctan2(num, den), 2*np.pi)
        return psi

    def phase_unwarping2(self, psi1, psi2, T1, T2):
        assert T2>T1, "please change the order of input"
        phase12 = psi1-psi2
        phase12 = np.mod(phase12, 2*np.pi)
        
        T = T1*T2/(T2-T1)
        R = T/T1
        n = np.round((phase12*R-psi1)/(2*np.pi))
        
        phase1 = (psi1 + 2*n*np.pi)/R
        return phase1, T # remove further optimization
    
    # def phase_unwarping2(self, psi1, psi2, T1, T2):
    #     assert T2>T1, "please change the order of input"
    #     phase12 = psi1-psi2
    #     mask = phase12 < 0
    #     phase12[mask] = phase12[mask] + 2*np.pi
    #     T = T1*T2/(T2-T1)

    #     N1, N2 = T2/(T2-T1), T1/(T2-T1)
    #     N1, N2 = self.integer_N(N1), self.integer_N(N2)

    #     n1 = np.round((phase12*N1-psi1)/(2*np.pi))
    #     phase1 = (psi1 + 2*n1*np.pi)/N1

    #     return phase1, T # remove further optimization
    
    # def phase_unwarping3(self, psi1, psi2, psi3, T1, T2, T3):
    #     """ for three frequencies
    #     """
    #     phase12, T12 = self.phase_unwarping2(psi1, psi2, T1, T2)
    #     phase23, T23 = self.phase_unwarping2(psi2, psi3, T2, T3)
    #     phase123, T123 = self.phase_unwarping2(phase12, phase23, T12, T23)
    #     return phase123, T123
    def phase_unwarping3(self, psi1, psi2, psi3, T1, T2, T3):
        """ for three frequencies
        """
        phase12, T12 = self.phase_unwarping2(psi1, psi2, T1, T2)
        phase23, T23 = self.phase_unwarping2(psi2, psi3, T2, T3)
        
        assert T23>T12, "please change the order of input"
        phase123 = phase12-phase23
        phase123 = np.mod(phase123, 2*np.pi)
        
        T123 = T12*T23/(T23-T12)
        R = T123/T1

        n = np.round((phase123*R-psi1)/(2*np.pi))
        phase123 = (psi1 + 2*n*np.pi)/R
        return phase123, T123
    
    def basic_extract(self, images):
        # extract psi
        psi = list()
        for pattens in images:
            psi.append(self.psi_extract(pattens))
        assert len(psi)==3
        phi1, T1 = self.phase_unwarping3(psi[0],psi[1],psi[2],self._c.Tc[0],self._c.Tc[1],self._c.Tc[2])
        phi1 = phi1*T1/self._c.Tc[0]
        phi1 = phi1.astype(np.float32)
        return phi1, T1
    
    def phase_extract(self, images):
        """The interface for other high-order method"""
        return self.basic_extract(images)


# LLS method
class LLS(PE):
    def __init__(self, config):
        super(LLS, self).__init__(config)

        self.b0, self.b1 = 0, 0
        self.bN, self.phi1 = 0, 0
        
    def phase_extract(self, images):
        self.phi1, T1 = self.basic_extract(images)
        self.phi1 = cv2.medianBlur(self.phi1, 5)      

        self.images = images
        self._init_param()
        
        # update via LSM 
        for it in range(self._c.MaxIter):
            Omega, Delta = list(), list()
            for j, patterns in enumerate(images):
                step = len(patterns)
                deltas = 2*np.pi*np.linspace(0, step-1, step)/step
                alpha = self._c.alpha[j]
                for s, img in enumerate(patterns):
                    img_fit = self._func(alpha, deltas[s], step-1)
                    grad_theta = self._grad_func(alpha, deltas[s], step-1)
                    grad_theta = np.stack(grad_theta, axis=-1)
                    Delta.append(img-img_fit)
                    Omega.append(grad_theta)
                    
            Delta = np.stack(Delta, axis=-1)
            Delta = np.expand_dims(Delta, axis=-1)
            Omega = np.stack(Omega, axis=-2)
            Omega_t = np.swapaxes(Omega,-1,-2)
            
            A = np.matmul(Omega_t, Omega)
            # AI = np.linalg.inv(A)
#             A = np.matmul(Omega_t, Omega)+1e-8*np.expand_dims(np.diag(np.ones(4)), axis=(0,1))
            AI = np.linalg.pinv(A, hermitian=True)
            B = np.matmul(Omega_t, Delta)
            d_theta = np.matmul(AI, B)
        
            self.b0 += d_theta[:,:,0,0]
            self.b1 += d_theta[:,:,1,0]
            self.bN += d_theta[:,:,2,0]
            self.phi1 += d_theta[:,:,3,0]
            if self._c.debug:
                print(f"\t\t The mean increasing amount of phi:{np.mean(np.abs(d_theta[:,:,3,0])):3g}")
        return self.phi1, T1
    
    def _func(self, alpha, delta, N):
        img1 = self.b0+self.b1*np.cos(alpha*self.phi1+delta)
        img2 = self.bN*np.cos(N*(alpha*self.phi1+delta))
        return img1+img2

    def _grad_func(self, alpha, delta, N):
        grad_phi1_p1 = -alpha*self.b1*np.sin(alpha*self.phi1+delta)
        grad_phi1_p2 = - N*alpha*self.bN*np.sin(N*(alpha*self.phi1+delta))
        grad_phi1 = grad_phi1_p1+grad_phi1_p2
        
        grad_b0 = np.ones_like(self.b0)
        grad_b1 = np.cos(alpha*self.phi1+delta)
        grad_bN = np.cos(N*(alpha*self.phi1+delta))
        return grad_b0, grad_b1, grad_bN, grad_phi1
    
    def _init_param(self):
        parttens = np.array(self.images)
        self.b0 = np.mean(parttens, axis=(0,1)).astype(np.float32)
        self.bN = np.zeros_like(self.b0)
        
        # self.b1
        step = len(self.images[0])
        deltas = 2*np.pi*np.linspace(0, step-1, step)/step
        part1, part2 = 0, 0
        for s, img in enumerate(self.images[0]):
            part1 += img*np.sin(deltas[s])
            part2 += img*np.cos(deltas[s])
        self.b1 = np.sqrt(part1*part1+part2*part2)*2/step


# our CFPE method
class CFPE(PE):
    def __init__(self, config):
        super(CFPE, self).__init__(config)
        
    def phase_extract(self, images):
        self.phi1, T1 = self.basic_extract(images)
        self.phi1 = cv2.medianBlur(self.phi1, 5)      
        
        for iter in range(self._c.MaxIter):
            # if iter<self._c.MaxIter/2:
                # self.phi1 = cv2.blur(self.phi1, (7,7))
            c1, c2, c3, c4 = 0., 0., 0., 0.
            Is, Ic, Ih = 0., 0., 0.
            for f, imgs in enumerate(images):
                steps = len(imgs)
                alpha_f = self._c.alpha[f]
                
                for s, img in enumerate(imgs):
                    zeta_s_f = alpha_f*self.phi1+2*np.pi*s/steps
                    
                    sin_zeta = np.sin(zeta_s_f)
                    cos_zeta = np.cos(zeta_s_f)
                    cos_zeta_h = np.cos((steps-1)*zeta_s_f)
                    
                    Is += sin_zeta*img
                    Ic += cos_zeta*img
                    Ih += cos_zeta_h*img
                    
                    c1 += sin_zeta**2
                    c2 += sin_zeta*cos_zeta_h
                    c3 += cos_zeta*cos_zeta_h
                    c4 += cos_zeta_h**2

            eps = 1e-6 # add eps to deal with pitfall points 
            num = (c1*c4-c3*c3+eps)*Is + c2*c3*Ic -c1*c2*Ih
            den = c2*c3*Is + (c1*c4-c2*c2+eps)*Ic -c1*c3*Ih
            num[np.abs(num)<1e1] = 0.0
            delta_phase = -np.arctan2(num, den)
            self.phi1 += delta_phase 
            if self._c.debug:
                print(f"\t\t The mean increasing amount of phi:{np.mean(np.abs(delta_phase)):3g}")
        return self.phi1, T1


# multifrequency phase extraction (MPE) method 
# an ablation method of our CFPE
class MPE(PE):
    def __init__(self, config):
        super(MPE, self).__init__(config)
        
    def phase_extract(self, images):
        self.phi1, T1 = self.basic_extract(images)  
        self.phi1 = cv2.medianBlur(self.phi1, 5)  
            
        for it in range(self._c.MaxIter):
            Is, Ic = 0, 0
            for f, imgs in enumerate(images):
                steps = len(imgs)
                alpha_f = self._c.alpha[f]
                for s, img in enumerate(imgs):
                    zeta_s_f = alpha_f*self.phi1+2*np.pi*s/steps
                    Is += np.sin(zeta_s_f)*img
                    Ic += np.cos(zeta_s_f)*img

            delta_phase = -np.arctan2(Is, Ic)
            self.phi1 += delta_phase 
            if self._c.debug:
                print(f"\t\t The mean increasing amount of phi:{np.mean(np.abs(delta_phase)):3g}")
        return self.phi1, T1

def phase_wrapper(cfg, method):
    assert method in ["PE","LLS","CFPE","MPE"]
    return eval(method)(cfg)
