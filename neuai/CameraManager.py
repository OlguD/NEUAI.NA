import cv2 as cv
import logging
import platform
from contextlib import contextmanager
from typing import Optional, Generator, Tuple
import numpy as np
import time

class CameraManager:
    def __init__(self):
        self.camera = None
        self.device_id = self._get_default_device()
        self.is_windows = platform.system().lower() == "windows"
        
    def _get_default_device(self) -> int:
        if platform.system().lower() == "darwin":
            for device_id in range(3):
                test_cap = cv.VideoCapture(device_id)
                if test_cap.isOpened():
                    test_cap.release()
                    return device_id
        return 0
        
    def initialize(self) -> bool:
        if self.camera is not None:
            self.release()
            
        try:
            if self.is_windows:
                self.camera = cv.VideoCapture(self.device_id, cv.CAP_DSHOW)
                if self.camera.isOpened():
                    self.camera.set(cv.CAP_PROP_BUFFERSIZE, 1)
                    self.camera.set(cv.CAP_PROP_FRAME_WIDTH, 640)
                    self.camera.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
                    self.camera.set(cv.CAP_PROP_FPS, 30)
                    
                    # Windows warmup
                    for _ in range(10):
                        ret, _ = self.camera.read()
                        if not ret:
                            break
                        time.sleep(0.1)
                    return True
                logging.error("Windows camera initialization failed")
            else:
                self.camera = cv.VideoCapture(self.device_id)
                if not self.camera.isOpened():
                    alt_device = 1 if self.device_id == 0 else 0
                    self.camera = cv.VideoCapture(alt_device)
                    
                if not self.camera.isOpened():
                    logging.error(f"Failed to open camera on devices {self.device_id} and {alt_device}")
                    return False
                    
                return True
                
            return False
            
        except Exception as e:
            logging.error(f"Camera initialization error: {str(e)}")
            self.camera = None
            return False
            
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        if self.camera is None or not self.camera.isOpened():
            return False, None
            
        try:
            for _ in range(2 if self.is_windows else 1):  # Windows may need multiple reads
                ret, frame = self.camera.read()
                if ret and frame is not None:
                    return True, frame
            return False, None
        except Exception as e:
            logging.error(f"Frame reading error: {str(e)}")
            return False, None
            
    def release(self):
        try:
            if self.camera is not None:
                self.camera.release()
        except Exception as e:
            logging.error(f"Camera release error: {str(e)}")
        finally:
            self.camera = None

@contextmanager
def camera_session() -> Generator[CameraManager, None, None]:
    camera = CameraManager()
    try:
        if camera.initialize():
            yield camera
        else:
            logging.error("Failed to initialize camera")
            yield None
    finally:
        camera.release()