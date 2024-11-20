# This project was done by Olgu Değirmenci and Atakan Uzun as a graduation project in Software Engineering. 

import cv2 as cv
from threading import Thread
import time
import logging
import sys
import numpy as np  
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
CASCADE_PATH = os.getenv("CASCADE_PATH")
VIDEO_SOURCE = int(os.getenv("VIDEO_SOURCE", 0))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def capture_video(source=0):
    """Kamera bağlantısını başlatır"""
    try:
        # DirectShow backend'i kullan
        capture = cv.VideoCapture(VIDEO_SOURCE)
        if not capture.isOpened():
            logging.error(f"Kamera açılamadı: {VIDEO_SOURCE}")
        else:
            logging.info("Kamera başarıyla açıldı.")
            
        # Kamera ayarları
        capture.set(cv.CAP_PROP_FRAME_WIDTH, 640)
        capture.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
        capture.set(cv.CAP_PROP_FPS, 30)
        
        return capture
        
    except Exception as e:
        logging.error(f"Kamera başlatma hatası: {e}")
        return None

def get_frame(capture):
    """Kameradan frame alır"""
    try:
        success, frame = capture.read()
        if not success:
            logging.warning("Failed to capture frame")
            return None
            
        # Frame'i yatay çevir
        return cv.flip(frame, 1)
        
    except Exception as e:
        logging.error(f"Frame alma hatası: {e}")
        return None

def show_frame(frame):
    frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    flipped_frame = cv.flip(frame, 1)
    cv.imshow('NEUAI.NA', flipped_frame)
    if cv.waitKey(1) & 0xFF == ord('q'):
        return False
    return True

def detect_face(frame):
    """Görüntüde yüz tespiti yapar"""
    try:
        # Cascade sınıflandırıcıyı yükle
        face_cascade = cv.CascadeClassifier(cv.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Gri tonlamaya çevir
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        
        # Yüz tespiti yap
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv.CASCADE_SCALE_IMAGE
        )
        
        # Sonuçları logla
        logging.info(f"Tespit edilen yüz sayısı: {len(faces) if isinstance(faces, np.ndarray) else 0}")
        
        return faces
        
    except Exception as e:
        logging.error(f"Yüz tespiti hatası: {str(e)}")
        return None
    
# def main():
#     # Video kaynağını başlat
#     logging.info("Video kaynağı başlatılıyor...")
#     capture = capture_video(VIDEO_SOURCE)
    
#     logging.info("Video kaynağı başarıyla başlatıldı. Çıkmak için 'q' tuşuna basın.")
    
#     try:
#         while True:
#             # Kareyi al
#             frame = get_frame(capture)
#             if frame is None:
#                 break
            
#             # Yüz tespiti yap
#             faces = detect_face(frame)
            
#             # Yüz tespit edilen alanları çerçeve ile işaretle
#             if faces is not None:
#                 for (x, y, w, h) in faces:
#                     cv.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
#             # Kareyi ekranda göster
#             if not show_frame(frame):
#                 break
#     except KeyboardInterrupt:
#         logging.info("Klavye kesintisi algılandı. Uygulama sonlandırılıyor...")
#     except Exception as e:
#         logging.error(f"Bir hata oluştu: {str(e)}")
#     finally:
#         # Kaynakları serbest bırak
#         logging.info("Kaynaklar serbest bırakılıyor...")
#         capture.release()
#         cv.destroyAllWindows()
#         logging.info("Uygulama kapatıldı.")

# if __name__ == "__main__":
#     main()