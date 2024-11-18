import cv2 as cv
import numpy as np
from deepface import DeepFace
import logging
from face_detection import detect_face, capture_video, get_frame
from collections import deque

# Temel ayarlar
COSINE_THRESHOLD = 0.4
EUCLIDEAN_THRESHOLD = 15.0
STABILITY_QUEUE_SIZE = 5
MIN_DETECTION_CONFIDENCE = 0.7
REFERENCE_IMAGE_PATH = "/Users/olgudegirmenci/Desktop/NEUAI.NA/core/olgu.jpg"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class FaceTracker:
    def __init__(self):
        self.prev_boxes = deque(maxlen=STABILITY_QUEUE_SIZE)
        self.current_box = None
        self.detection_count = 0
        self.lost_count = 0
        self.is_tracking = False
        
    def smooth_box(self, new_box):
        if not self.prev_boxes:
            self.prev_boxes.append(new_box)
            return new_box
        
        new_box = np.array(new_box)
        prev_boxes_array = np.array(list(self.prev_boxes))
        avg_box = np.mean(prev_boxes_array, axis=0)
        
        alpha = 0.7
        smoothed_box = tuple(map(int, alpha * new_box + (1 - alpha) * avg_box))
        
        self.prev_boxes.append(smoothed_box)
        return smoothed_box
    
    def is_valid_detection(self, new_box, frame_shape):
        try:
            if isinstance(new_box, np.ndarray):
                new_box = tuple(new_box)
            
            if new_box is None or len(new_box) != 4:
                return False
                
            x, y, w, h = map(int, new_box)
            frame_h, frame_w = frame_shape[:2]
            
            if x < 0 or y < 0 or x + w > frame_w or y + h > frame_h:
                return False
                
            area_ratio = (w * h) / (frame_w * frame_h)
            if area_ratio > 0.8 or area_ratio < 0.01:
                return False
                
            aspect_ratio = w / float(h)
            if aspect_ratio < 0.5 or aspect_ratio > 2.0:
                return False
                
            return True
            
        except Exception as e:
            logging.error(f"Geçerlilik kontrolünde hata: {str(e)}")
            return False

    def update(self, frame, faces):
        frame_shape = frame.shape
        
        if faces is None:
            faces = []
        elif isinstance(faces, np.ndarray):
            faces = faces.tolist()
        
        valid_faces = []
        for face in faces:
            if self.is_valid_detection(face, frame_shape):
                valid_faces.append(face)
        
        if not valid_faces:
            self.lost_count += 1
            if self.lost_count > 10:
                self.is_tracking = False
                self.prev_boxes.clear()
            return None
            
        self.lost_count = 0
        
        center_x = frame_shape[1] / 2
        center_y = frame_shape[0] / 2
        
        def distance_to_center(box):
            x, y, w, h = map(int, box)
            box_center_x = x + w/2
            box_center_y = y + h/2
            return ((box_center_x - center_x)**2 + (box_center_y - center_y)**2)
        
        best_face = min(valid_faces, key=distance_to_center)
        
        if not self.is_tracking:
            self.current_box = tuple(map(int, best_face))
            self.is_tracking = True
        else:
            self.current_box = self.smooth_box(best_face)
            
        self.detection_count += 1
        return self.current_box

def convert_to_vector(image):
    try:
        image_rgb = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        embeddings = DeepFace.represent(image_rgb, model_name="VGG-Face", 
                                      enforce_detection=False)
        return embeddings[0]['embedding']
    except Exception as e:
        logging.error(f"Vektör dönüşümünde hata: {str(e)}")
        return None

def normalize_vector(vector):
    """Vektör normalizasyonu"""
    try:
        if vector is None or not isinstance(vector, (np.ndarray, list)):
            return None
            
        vector = np.array(vector, dtype=np.float32).flatten()
        norm = np.linalg.norm(vector)
        
        if norm == 0:
            return vector
            
        return vector / norm
    except Exception as e:
        logging.error(f"Normalize etme hatası: {str(e)}")
        return None

def cosine_similarity(embedding1, embedding2):
    """Cosine benzerliği hesaplama"""
    try:
        # Vektörleri düzleştir ve numpy array'e çevir
        embedding1 = np.array(embedding1, dtype=np.float32).flatten()
        embedding2 = np.array(embedding2, dtype=np.float32).flatten()
        
        # Boyut kontrolü
        if embedding1.shape != embedding2.shape:
            raise ValueError("Vektör boyutları eşleşmiyor")
        
        # Sıfır vektör kontrolü
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0
        
        # Cosine similarity hesapla
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        
        return float(similarity)  # Skaler değer döndür
        
    except Exception as e:
        logging.error(f"Cosine similarity hesaplama hatası: {str(e)}")
        return 0

def euclidean_distance(embedding1, embedding2):
    """Euclidean mesafe hesaplama"""
    try:
        # Vektörleri düzleştir ve numpy array'e çevir
        embedding1 = np.array(embedding1, dtype=np.float32).flatten()
        embedding2 = np.array(embedding2, dtype=np.float32).flatten()
        
        # Boyut kontrolü
        if embedding1.shape != embedding2.shape:
            raise ValueError("Vektör boyutları eşleşmiyor")
        
        # Mesafeyi hesapla
        distance = np.linalg.norm(embedding1 - embedding2)
        
        return float(distance)  # Skaler değer döndür
        
    except Exception as e:
        logging.error(f"Euclidean mesafe hesaplama hatası: {str(e)}")
        return float('inf')  # Hata durumunda sonsuz mesafe döndür

def interpret_similarity(cos_sim, euc_dist):
    """Benzerlik skorunu yorumla"""
    try:
        # Cosine similarity'yi 0-1 arasına normalize et
        weighted_cos = float(cos_sim + 1) / 2
        
        # Euclidean distance'ı normalize et
        weighted_euc = max(0, 1 - float(euc_dist) / EUCLIDEAN_THRESHOLD)
        
        # Toplam skoru hesapla
        similarity_score = (weighted_cos * 0.8) + (weighted_euc * 0.2)
        
        # Yorumla
        if similarity_score >= 0.95:
            interpretation = "Aynı kişi (Çok yüksek benzerlik)"
        elif similarity_score >= 0.85:
            interpretation = "Büyük olasılıkla aynı kişi"
        elif similarity_score >= 0.75:
            interpretation = "Benzer özellikler mevcut"
        else:
            interpretation = "Farklı kişiler"

        return {
            "similarity_score": float(similarity_score * 100),
            "cosine_similarity": float(weighted_cos),
            "euclidean_distance": float(euc_dist),
            "interpretation": interpretation
        }
        
    except Exception as e:
        logging.error(f"Benzerlik yorumlama hatası: {str(e)}")
        return {
            "similarity_score": 0,
            "cosine_similarity": 0,
            "euclidean_distance": float('inf'),
            "interpretation": "Hesaplama hatası"
        }