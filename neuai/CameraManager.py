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
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.camera = None
        self.device_id = self._get_default_device()
        self.frame_queue = queue.Queue(maxsize=2)
        self.running = False
        self.capture_thread = None
        self.last_frame_time = time.time()
        self.frame_count = 0
        self.users = 0
        self._initialized = True
        self.is_macos = platform.system().lower() == 'darwin'
        
    def _get_default_device(self) -> int:
        """Platform'a göre varsayılan kamera ID'sini belirle"""
        if platform.system().lower() == 'darwin':
            # macOS için kamera test et
            for device_id in [0, 1]:  # Dahili ve harici kamera için kontrol
                try:
                    cap = cv.VideoCapture(device_id)
                    if cap is not None and cap.isOpened():
                        cap.release()
                        return device_id
                except:
                    continue
        return 0
    
    def _init_camera(self):
        """Platform'a göre kamera başlatma"""
        try:
            if self.is_macos:
                # macOS için özel başlatma
                cap = cv.VideoCapture(self.device_id)
                if cap is None or not cap.isOpened():
                    return None
            else:
                # Windows için DirectShow
                cap = cv.VideoCapture(self.device_id, cv.CAP_DSHOW)
                if cap is None or not cap.isOpened():
                    return None
            
            # Platform bağımsız ayarlar
            cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv.CAP_PROP_FPS, 30)
            
            # Windows-specific ayarlar
            if not self.is_macos:
                cap.set(cv.CAP_PROP_SETTINGS, 0)
                cap.set(cv.CAP_PROP_BUFFERSIZE, 1)
            
            # Test frame
            for _ in range(3):  # macOS için daha az deneme
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0:
                    return cap
                time.sleep(0.1)
                
            return None
            
        except Exception as e:
            logging.error(f"Camera initialization error: {str(e)}")
            return None
    
    def _capture_frames(self):
        """Frame yakalama thread'i"""
        warmup_frames = 0
        warmup_limit = 5 if self.is_macos else 10
        
        while self.running and warmup_frames < warmup_limit:
            if self.camera is None or not self.camera.isOpened():
                break
                
            ret, frame = self.camera.read()
            if ret and frame is not None and frame.size > 0:
                warmup_frames += 1
            time.sleep(0.01)
            
        while self.running:
            if self.camera is None or not self.camera.isOpened():
                break
                
            try:
                ret, frame = self.camera.read()
                
                if not ret or frame is None or frame.size == 0:
                    time.sleep(0.001)
                    continue
                    
                # FPS hesaplama
                self.frame_count += 1
                current_time = time.time()
                if current_time - self.last_frame_time >= 1.0:
                    fps = self.frame_count / (current_time - self.last_frame_time)
                    logging.debug(f"Camera FPS: {fps:.2f}")
                    self.frame_count = 0
                    self.last_frame_time = current_time
                
                # Queue yönetimi
                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()
                    except queue.Empty:
                        pass
                        
                self.frame_queue.put_nowait(frame)
                
            except Exception as e:
                logging.warning(f"Frame capture error: {str(e)}")
                time.sleep(0.001)
                continue
                
            time.sleep(0.001)
    
    def start(self):
        """Kamera başlatma"""
        with self._lock:
            self.users += 1
            if self.running:
                return True
                
            try:
                self.camera = self._init_camera()
                
                if self.camera is None:
                    logging.error("Could not initialize camera")
                    return False
                
                self.running = True
                self.capture_thread = threading.Thread(target=self._capture_frames, daemon=True)
                self.capture_thread.start()
                
                time.sleep(0.2 if self.is_macos else 0.5)  # macOS için daha kısa bekleme
                
                logging.info("Camera initialized successfully")
                return True
                
            except Exception as e:
                logging.error(f"Camera initialization error: {str(e)}")
                self.stop()
                return False
    
    def stop(self):
        """Kamera durdurma"""
        with self._lock:
            self.users -= 1
            if self.users <= 0:
                self.users = 0
                self.running = False
                
                if self.capture_thread and self.capture_thread.is_alive():
                    try:
                        self.capture_thread.join(timeout=1.0)
                    except:
                        pass
                
                try:
                    while not self.frame_queue.empty():
                        try:
                            self.frame_queue.get_nowait()
                        except:
                            pass
                except:
                    pass
                    
                try:
                    if self.camera is not None:
                        self.camera.release()
                except Exception as e:
                    logging.error(f"Camera release error: {str(e)}")
                finally:
                    self.camera = None
                    self.frame_count = 0
                    self.last_frame_time = time.time()
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Frame okuma"""
        if not self.running or self.camera is None:
            return False, None
            
        try:
            frame = self.frame_queue.get(timeout=0.1)
            if frame is None or frame.size == 0:
                return False, None
            return True, frame
        except queue.Empty:
            return False, None
        except Exception as e:
            logging.error(f"Frame reading error: {str(e)}")
            return False, None

class CameraSession:
    def __init__(self):
        self.manager = CameraManagerSingleton()
    
    def __enter__(self):
        if self.manager.start():
            return self.manager
        return None
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manager.stop()

def get_camera_session() -> Generator[Optional[CameraManagerSingleton], None, None]:
    """Kamera oturumu oluşturur"""
    with CameraSession() as camera:
        yield camera