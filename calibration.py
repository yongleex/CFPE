import numpy as np
import cv2 
import pathlib
import matplotlib.pyplot as plt

from phase import PE


def reshape34(l):
    x =[[e for e in seg] for seg in [l[0:4],l[4:8],l[8:12]]]
    return x


def draw_chess(gray, points):
    board_size = (9, 6)  # 也就是boardSize
    vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    cv2.drawChessboardCorners(vis, board_size, points.reshape(-1,1,2), True)
    plt.figure()
    plt.imshow(vis)


class Calibrator():
    def __init__(self, config):
        self._c = config
        self._c.steps=[4, 4, 4]
        self.psp = PE(self._c)
        
    def find_gray_corners(self, gray, show=False):
        board_size = (9, 6)  # 也就是boardSize
        square_Size = 10     # The distance betdraw_chessween two neighbor points in mm
        
        points_w = np.zeros((np.prod(board_size), 3), np.float32)
        points_w[:, :2] = np.indices(board_size).T.reshape(-1, 2)
        points_w *= square_Size
        
        # 粗查找角点
        found, corners = cv2.findChessboardCorners(gray, board_size)
        if not found:
            print("ERROR(no corners):")
            return None
        
        # 精细化查找
        term = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 30, 0.01)
        corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), term)  # 精定位角点
        points_c = corners.reshape(-1, 2)
        return points_w, points_c
    
    def calibrate(self):
        root = pathlib.Path(self._c.calibra_path)

        points_ws, points_cs, points_ps = [],[],[]
        for i in range(22):
            # read gray image and find the corners
            name_gray = root/f"{i:0>2d}_{12:0>2d}h.bmp"
            image_gray = cv2.imread(name_gray.as_posix(), 0)
            points_w, points_c = self.find_gray_corners(image_gray, self._c.debug)
            
            # read the fringe images and obtain the phases
            images_ph = [root/f"{i:0>2d}_{j:0>2d}h.bmp" for j in range(12)]
            images_pv = [root/f"{i:0>2d}_{j:0>2d}v.bmp" for j in range(12)]
            images_h = [cv2.imread(p.as_posix(), 0) for p in images_ph]
            images_v = [cv2.imread(p.as_posix(), 0) for p in images_pv]
            images_h = reshape34(images_h)
            images_v = reshape34(images_v)

            phase_h, T_h = self.psp.phase_extract(images_h)
            phase_v, T_v = self.psp.phase_extract(images_v)
            phase_h, phase_v = cv2.blur(phase_h,(15,15)), cv2.blur(phase_v,(15,15))# due to a plane

            # phase to projector points
            coord_h = phase_h*self._c.Tc[0]/(2*np.pi)
            coord_v = phase_v*self._c.Tc[0]/(2*np.pi)+60
            
            coord_h = cv2.remap(coord_h, points_c[:,0], points_c[:,1], cv2.INTER_CUBIC)
            coord_v = cv2.remap(coord_v, points_c[:,0], points_c[:,1], cv2.INTER_CUBIC)
            points_p = np.concatenate((coord_h, coord_v), axis=1).astype(np.float32)
            
            points_ws.append(points_w)
            points_cs.append(points_c.reshape(-1,2))
            points_ps.append(points_p.reshape(-1,2))
            
            if self._c.debug:
                plt.figure()
                plt.subplot(1,2,1)
                plt.imshow(phase_h)
                plt.colorbar()
                plt.subplot(1,2,2)
                plt.plot(phase_h[100,:])
                draw_chess(image_gray, points_p.reshape(-1,2))
        

            
        # step 2, perform standard calibration with opencv func
        print("Calibrating the camera and projector system ...")
        h_c, w_c = 480, 640
        h_p, w_p = 480, 640
        
        projet_retval, projet_matrix, projetDistCoeffs, _, _ = cv2.calibrateCamera(points_ws, points_ps, (w_p, h_p), None, None, flags=cv2.CALIB_FIX_S1_S2_S3_S4)
        camera_retval, camera_matrix, cameraDistCoeffs, _, _ = cv2.calibrateCamera(points_ws, points_cs, (w_c, h_c), None, None, flags=cv2.CALIB_FIX_S1_S2_S3_S4)

        term = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 100, 1e-5)
        retval,  cameraMatrix, cameraDistCoeffs, projetMatrix, projetDistCoeffs, R, T, E, F = \
                cv2.stereoCalibrate(points_ws, points_cs, points_ps, camera_matrix, cameraDistCoeffs,  
                        projet_matrix, projetDistCoeffs, (w_p, h_p),
                        flags=cv2.CALIB_FIX_ASPECT_RATIO | cv2.CALIB_ZERO_TANGENT_DIST | cv2.CALIB_FIX_INTRINSIC|
                        # flags=cv2.CALIB_FIX_ASPECT_RATIO | cv2.CALIB_ZERO_TANGENT_DIST | cv2.CALIB_USE_INTRINSIC_GUESS |
                              cv2.CALIB_USE_INTRINSIC_GUESS |cv2.CALIB_RATIONAL_MODEL | cv2.CALIB_FIX_K3 | cv2.CALIB_FIX_K4 | cv2.CALIB_FIX_K5, criteria=term)
        print("The return value of cal:", camera_retval, projet_retval, retval)

        # step 3, perform stereo rectify with calibrated results
        R1, R2, P1, P2, Q, validPixROI1, validPixROI2 = \
                cv2.stereoRectify(cameraMatrix, cameraDistCoeffs, projetMatrix, projetDistCoeffs, (w_c, h_c), R, T, flags=0, alpha=0.70)
        map_c1, map_c2 = cv2.initUndistortRectifyMap(cameraMatrix, cameraDistCoeffs, R1, P1, (w_c, h_c), cv2.CV_16SC2)
        map_p1, map_p2 = cv2.initUndistortRectifyMap(projetMatrix, projetDistCoeffs, R2, P2, (w_c, h_c), cv2.CV_16SC2)
        print("The valid ROIs:",validPixROI1, validPixROI2)
        
        if self._c.debug:
            image_rgb = cv2.cvtColor(image_gray, cv2.COLOR_GRAY2BGR)
            image_rgb = cv2.drawChessboardCorners(image_rgb, (9,6), points_c.reshape(-1,1,2), True)
            proj_rgb = cv2.cvtColor(image_gray*0, cv2.COLOR_GRAY2BGR)
            proj_rgb = cv2.drawChessboardCorners(proj_rgb, (9,6), points_p.reshape(-1,1,2), True)
        
            result1 = cv2.remap(image_rgb, map_c1, map_c2, cv2.INTER_CUBIC)
            result2 = cv2.remap(proj_rgb, map_p1, map_p2, cv2.INTER_CUBIC)
            result = np.concatenate((result1, result2), axis=1)
            plt.figure()
            plt.imshow(result)
                
        x = np.linspace(0,w_p-1,w_p)+np.zeros([h_p, w_p])
        phase = 2*np.pi*x/self._c.Tc[0]
        phase_rectified = cv2.remap(phase, map_p1, map_p2, cv2.INTER_LINEAR)
        
        # save the results for measurement
        np.savez(root/"calibration_result",  map_c1=map_c1,  map_c2=map_c2,  Q=Q,  phase_rectified=phase_rectified) 
        if self._c.debug:
            plt.show()
        
    def load(self):
        root = pathlib.Path(self._c.calibra_path)
        cal_data = np.load(root/"calibration_result.npz")
        map_c1 = cal_data['map_c1']
        map_c2 = cal_data['map_c2']
        phase_rectified = cal_data['phase_rectified']
        Q = cal_data['Q']
        return map_c1, map_c2, phase_rectified, Q

        
if __name__=="__main__":
    from config import config
    cfg = config()
    cfg.debug = True

    cal = Calibrator(cfg)
    cal.calibrate()
