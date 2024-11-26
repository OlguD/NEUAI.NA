import cv2 as cv
import logging
import platform
from contextlib import contextmanager
from typing import Optional, Generator, Tuple
import numpy as np
import threading
import queue
import time

class CameraManagerSingleton:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
                    cls._instance._resource_lock = threading.Lock()  # Instance için ayrı lock
        return cls._instance
    
    def __init__(self):
        if getattr(self, '_initialized', False):
            return
            
        self.camera = None
        self.device_id = 0
        self.frame_queue = queue.Queue(maxsize=2)
        self.running = False
        self.capture_thread = None
        self.last_frame_time = time.time()
        self.frame_count = 0
        self.users = 0
        self._initialized = True
        
    def __init__camera(self):
        try:
            logging.info("Initializing camera with DirectShow")
            cap = cv.VideoCapture(self.device_id, cv.CAP_DSHOW)
            
            if cap is None or not cap.isOpened():
                logging.error("DirectShow camera initialization failed")
                return None
                
            # Kamera ayarları
            cap.set(cv.CAP_PROP_SETTINGS, 0)
            cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv.CAP_PROP_FPS, 30)
            cap.set(cv.CAP_PROP_BUFFERSIZE, 1)
            
            # Test frame ve warmup
            warmup_success = False
            for i in range(10):
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0:
                    logging.info(f"Camera warmup frame {i+1} successful")
                    warmup_success = True
                    break
                time.sleep(0.1)
            
            if not warmup_success:
                logging.error("Camera warmup failed")
                return None
                
            logging.info("Camera initialization successful")
            return cap
            
        except Exception as e:
            logging.error(f"Camera initialization error: {str(e)}")
            return None
    
    def start(self):
        """Kamera başlatma"""
        with self._resource_lock:  # Instance lock kullan
            try:
                if not self.running:
                    logging.info("Initializing new camera session")
                    self.camera = self.__init__camera()
                    
                    if self.camera is None:
                        logging.error("Could not initialize camera")
                        return False
                    
                    # Queue'yu temizle
                    while not self.frame_queue.empty():
                        try:
                            self.frame_queue.get_nowait()
                        except:
                            pass
                    
                    self.running = True
                    self.capture_thread = threading.Thread(target=self._capture_frames, daemon=True)
                    self.capture_thread.start()
                    time.sleep(0.5)  # Kameranın başlaması için bekle
                
                self.users += 1
                logging.info(f"Camera session started (users: {self.users})")
                return True
                
            except Exception as e:
                logging.error(f"Camera start error: {str(e)}")
                self.release()
                return False
    
    def release(self):
        """Kamera kaynaklarını temizle"""
        with self._resource_lock:  # Instance lock kullan
            self.users -= 1
            logging.info(f"Release called (remaining users: {self.users})")
            
            if self.users <= 0:
                self.users = 0
                self.running = False
                
                if self.capture_thread and self.capture_thread.is_alive():
                    try:
                        logging.info("Stopping capture thread")
                        self.capture_thread.join(timeout=1.0)
                    except Exception as e:
                        logging.error(f"Error stopping capture thread: {str(e)}")
                
                try:
                    logging.info("Clearing frame queue")
                    while not self.frame_queue.empty():
                        try:
                            self.frame_queue.get_nowait()
                        except:
                            pass
                except Exception as e:
                    logging.error(f"Error clearing frame queue: {str(e)}")
                    
                try:
                    if self.camera is not None:
                        logging.info("Releasing camera")
                        self.camera.release()
                except Exception as e:
                    logging.error(f"Camera release error: {str(e)}")
                finally:
                    self.camera = None
                    self.frame_count = 0
                    self.last_frame_time = time.time()
                    logging.info("Camera resources cleaned up")

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Frame okuma"""
        if not self.running or self.camera is None:
            logging.error("Camera not running or None")
            return False, None
            
        try:
            frame = self.frame_queue.get(timeout=1.0)  # Daha uzun timeout
            if frame is None or frame.size == 0:
                logging.error("Invalid frame received")
                return False, None
                
            return True, frame.copy()  # Frame'in kopyasını döndür
            
        except queue.Empty:
            logging.warning("Frame queue empty")
            return False, None
        except Exception as e:
            logging.error(f"Frame reading error: {str(e)}")
            return False, None

    def _capture_frames(self):
        """Frame yakalama thread'i"""
        logging.info("Starting frame capture thread")
        last_frame_time = time.time()
        frame_count = 0
        
        while self.running:
            if self.camera is None or not self.camera.isOpened():
                logging.error("Camera disconnected")
                break
                
            try:
                ret, frame = self.camera.read()
                
                if not ret or frame is None or frame.size == 0:
                    logging.warning("Invalid frame captured")
                    time.sleep(0.001)
                    continue
                
                # FPS hesaplama ve loglama
                frame_count += 1
                current_time = time.time()
                if current_time - last_frame_time >= 1.0:
                    fps = frame_count / (current_time - last_frame_time)
                    logging.debug(f"Capture FPS: {fps:.2f}")
                    frame_count = 0
                    last_frame_time = current_time
                
                # Queue management with timeout
                try:
                    if self.frame_queue.full():
                        try:
                            self.frame_queue.get_nowait()
                        except queue.Empty:
                            pass
                        
                    self.frame_queue.put(frame, timeout=0.1)
                except queue.Full:
                    continue
                    
            except Exception as e:
                logging.error(f"Frame capture error: {str(e)}")
                continue
                
            time.sleep(0.001)  # CPU kullanımını azalt
            
        logging.info("Frame capture thread stopped")



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
                self.camera = cv.VideoCapture(self.device_id, cv.CAP_MSMF)
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

class CameraSession:
    def __init__(self):
        self.manager = CameraManagerSingleton()

    def __enter__(self):
        if self.manager.start():
            return self.manager
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manager.stop()

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

def get_camera_session():
    """Platform bağımsız kamera yöneticisi oluşturur"""
    is_windows = platform.system().lower() == "windows"
    
    logging.info(f"Platform: {platform.system()}")
    
    if is_windows:
        logging.info("Using Windows-specific camera session")
        manager = CameraManagerSingleton()
        if not manager.start():  # Kamerayı başlat
            logging.error("Failed to start Windows camera")
            return None
        return manager
    else:
        camera = CameraManager()
        if camera.initialize():
            return camera
        logging.error("Failed to initialize camera")
        return None

__all__ = ['get_camera_session', 'CameraManager', 'CameraManagerSingleton', 'CameraSession']            