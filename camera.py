# -- coding: utf-8 --
import cv2
import numpy as np
import sys
import copy
import os
import termios
import time
from ctypes import *

sys.path.append("/opt/MVS/Samples/64/Python/MvImport")

from MvCameraControl_class import *

libc = CDLL("libc.so.6")



class HK_Camera:
    def __init__(self,):
        self.init_cam()

    def start(self):
        # ch:开始取流 | en:Start grab image
        ret = self.cam.MV_CC_StartGrabbing()

    # def psp(self):
    #     self.start()

    #     for i in range(10):
    #         st = time.time()
    #         self.capture_one(name=str(i))
    #         print("st:", time.time()-st)

    #     self.exit()   

    def init_cam(self,):
        deviceList = MV_CC_DEVICE_INFO_LIST()
        tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE
        ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
        nConnectionNum = 0
        # ch:创建相机实例 | en:Creat Camera Object
        self.cam = MvCamera()
        # ch:选择设备并创建句柄 | en:Select device and create handle
        stDeviceList = cast(deviceList.pDeviceInfo[int(nConnectionNum)], 
                            POINTER(MV_CC_DEVICE_INFO)).contents
        ret = self.cam.MV_CC_CreateHandle(stDeviceList)        
        # ch:打开设备 | en:Open device
        ret = self.cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
        # ch:设置触发模式为off | en:Set trigger mode as off
        # ret = self.cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)  

        ret = self.cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_ON) 
        ret = self.cam.MV_CC_SetEnumValue("TriggerSource", MV_TRIGGER_SOURCE_SOFTWARE)     

        # ch:获取数据包大小 | en:Get payload size
        stParam = MVCC_INTVALUE()
        memset(byref(stParam), 0, sizeof(MVCC_INTVALUE))

        ret = self.cam.MV_CC_GetIntValue("PayloadSize", stParam)
        
        self.nPayloadSize = stParam.nCurValue    

    def capture_one(self, name="test"):
        stDeviceList = MV_FRAME_OUT_INFO_EX()
        memset(byref(stDeviceList), 0, sizeof(stDeviceList))
        self.data_buf = (c_ubyte * self.nPayloadSize)()
        
        # self.cam.MV_CC_SetCommandValue("TriggerSoftware")
        # ret = self.cam.MV_CC_GetOneFrameTimeout(byref(self.data_buf), self.nPayloadSize, stDeviceList, 1000)
        self.cam.MV_CC_SetCommandValue("TriggerSoftware")
        ret = self.cam.MV_CC_GetOneFrameTimeout(byref(self.data_buf), self.nPayloadSize, stDeviceList, 1000)

        if ret == 0:
            # print ("get one frame: Width[%d], Height[%d], nFrameNum[%d]" % (stDeviceList.nWidth, stDeviceList.nHeight, stDeviceList.nFrameNum))
            nRGBSize = stDeviceList.nWidth * stDeviceList.nHeight * 3
            stConvertParam = MV_SAVE_IMAGE_PARAM_EX()
            stConvertParam.nWidth = stDeviceList.nWidth
            stConvertParam.nHeight = stDeviceList.nHeight
            stConvertParam.pData = self.data_buf
            stConvertParam.nDataLen = stDeviceList.nFrameLen
            stConvertParam.enPixelType = stDeviceList.enPixelType
            stConvertParam.nImageLen = stConvertParam.nDataLen
            stConvertParam.nJpgQuality = 70
            # stConvertParam.enImageType = MV_Image_Jpeg
            stConvertParam.enImageType = MV_Image_Bmp

            stConvertParam.pImageBuffer = (c_ubyte * nRGBSize)()
            stConvertParam.nBufferSize = nRGBSize
            ret = self.cam.MV_CC_ConvertPixelType(stConvertParam)
            # print(stConvertParam.nImageLen)
            ret = self.cam.MV_CC_SaveImageEx2(stConvertParam)
            if ret != 0:
                print ("convert pixel fail ! ret[0x%x]" % ret)
                del self.data_buf
                sys.exit()
            file_path = name
            file_open = open(file_path.encode('ascii'), 'wb+')
            img_buff = (c_ubyte * stConvertParam.nImageLen)()
            # cdll.msvcrt.memcpy(byref(img_buff), stConvertParam.pImageBuffer, stConvertParam.nImageLen)
            memcpy = libc.memcpy(byref(img_buff), stConvertParam.pImageBuffer, stConvertParam.nImageLen)

            file_open.write(img_buff)
            # print(f"img write_{name}", time.time())
        # print ("Save Image succeed!")

    def exit(self,):
        # ch:停止取流 | en:Stop grab image
        ret = self.cam.MV_CC_StopGrabbing()
        if ret != 0:
            print ("stop grabbing fail! ret[0x%x]" % ret)
            del self.data_buf
            sys.exit()
        # ch:关闭设备 | Close device
        ret = self.cam.MV_CC_CloseDevice()
        if ret != 0:
            print ("close deivce fail! ret[0x%x]" % ret)
            del self.data_buf
            sys.exit()

        # ch:销毁句柄 | Destroy handle
        ret = self.cam.MV_CC_DestroyHandle()
        if ret != 0:
            print ("destroy handle fail! ret[0x%x]" % ret)
            del self.data_buf
            sys.exit()

        del self.data_buf
    
def test():
    hkc = HK_Camera()
    # hhv.psp()
    hkc.start()

    for i in range(10):
        st = time.time()
        hkc.capture_one(name='r_' + str(i)+".bmp")
        print("st:", time.time()-st)

    hkc.exit()   



if __name__ == "__main__":
    test()
    
