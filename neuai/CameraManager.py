import cv2 as cv
import logging
import platform
from contextlib import contextmanager
from typing import Optional, Generator, Tuple
import numpy as np

class CameraManager:
    def __init__(self):
        self.camera = None
        self.device_id = self._get_default_device()
        
    def _get_default_device(self) -> int:
        if platform.system().lower() == "darwin":  # macOS
            # Sırasıyla 0, 1, 2'yi dene
            for device_id in range(3):
                test_cap = cv.VideoCapture(device_id)
                if test_cap.isOpened():
                    test_cap.release()
                    return device_id
        return 0  # Fallback to default
        
    def initialize(self) -> bool:
        """Initialize camera with error handling"""
        if self.camera is not None:
            self.release()
            
        try:
            self.camera = cv.VideoCapture(self.device_id)
            if not self.camera.isOpened():
                # Try alternate device
                alt_device = 1 if self.device_id == 0 else 0
                self.camera = cv.VideoCapture(alt_device)
                
            if not self.camera.isOpened():
                logging.error(f"Failed to open camera on devices {self.device_id} and {alt_device}")
                return False
                
            # Configure camera
            self.camera.set(cv.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv.CAP_PROP_FPS, 30)
            return True
            
        except Exception as e:
            logging.error(f"Camera initialization error: {str(e)}")
            self.camera = None
            return False
            
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read a frame with error handling"""
        if self.camera is None or not self.camera.isOpened():
            return False, None
            
        try:
            ret, frame = self.camera.read()
            if not ret:
                logging.error("Failed to read frame")
                return False, None
            return True, frame
        except Exception as e:
            logging.error(f"Frame reading error: {str(e)}")
            return False, None
            
    def release(self):
        """Safely release camera resources"""
        try:
            if self.camera is not None:
                self.camera.release()
        except Exception as e:
            logging.error(f"Camera release error: {str(e)}")
        finally:
            self.camera = None

@contextmanager
def camera_session() -> Generator[CameraManager, None, None]:
    """Context manager for safe camera handling"""
    camera = CameraManager()
    try:
        if camera.initialize():
            yield camera
        else:
            logging.error("Failed to initialize camera")
            yield None
    finally:
        camera.release()