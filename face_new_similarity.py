import cv2 as cv
import numpy as np
from deepface import DeepFace
import logging
from face_detection import detect_face, capture_video, get_frame
from collections import deque

# Temel ayarlar
COSINE_THRESHOLD = 0.4
EUCLIDEAN_THRESHOLD = 20.0
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
        
        # Convert to numpy array for calculations
        new_box = np.array(new_box)
        prev_boxes_array = np.array(list(self.prev_boxes))
        avg_box = np.mean(prev_boxes_array, axis=0)
        
        alpha = 0.7
        smoothed_box = tuple(map(int, alpha * new_box + (1 - alpha) * avg_box))
        
        self.prev_boxes.append(smoothed_box)
        return smoothed_box
    
    def is_valid_detection(self, new_box, frame_shape):
        """Tespit edilen yüzün geçerli olup olmadığını kontrol eder"""
        try:
            # NumPy array'i tuple'a çevir
            if isinstance(new_box, np.ndarray):
                new_box = tuple(new_box)
            
            # Boş kontrol
            if new_box is None or len(new_box) != 4:
                return False
                
            x, y, w, h = map(int, new_box)  # Değerleri integer'a çevir
            frame_h, frame_w = frame_shape[:2]
            
            # Geçerlilik kontrolleri
            if x < 0 or y < 0 or x + w > frame_w or y + h > frame_h:
                return False
                
            # Boyut kontrolleri
            area_ratio = (w * h) / (frame_w * frame_h)
            if area_ratio > 0.8 or area_ratio < 0.01:
                return False
                
            # En-boy oranı kontrolü
            aspect_ratio = w / float(h)
            if aspect_ratio < 0.5 or aspect_ratio > 2.0:
                return False
                
            return True
            
        except (TypeError, ValueError, ZeroDivisionError) as e:
            logging.error(f"Geçerlilik kontrolünde hata: {str(e)}")
            return False

    def update(self, frame, faces):
        """Yüz konumunu günceller ve stabilize eder"""
        frame_shape = frame.shape
        
        # faces'in liste olduğundan emin ol
        if faces is None:
            faces = []
        elif isinstance(faces, np.ndarray):
            faces = faces.tolist()
        
        # Geçerli yüzleri filtrele
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
        
        # Merkeze en yakın yüzü seç
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
    if vector is None:
        return None
    norm = np.linalg.norm(vector)
    return vector / norm if norm != 0 else vector

def cosine_similarity(embedding1, embedding2):
    """Cosine benzerliği hesaplama, daha hassas"""
    embedding1 = np.array(embedding1)
    embedding2 = np.array(embedding2)
    dot_product = np.dot(embedding1, embedding2)
    norm1 = np.linalg.norm(embedding1)
    norm2 = np.linalg.norm(embedding2)
    similarity = dot_product / (norm1 * norm2)
    # Normalize etme yöntemini değiştiriyoruz
    return similarity

def euclidean_distance(embedding1, embedding2):
    return np.linalg.norm(np.array(embedding1) - np.array(embedding2))

def interpret_similarity(cos_sim, euc_dist):
    """Daha sıkı benzerlik yorumlama kriterleri"""
    # Cosine similarity -1 ile 1 arasında olacak
    # Euclidean distance için daha hassas eşik
    EUCLIDEAN_THRESHOLD = 15.0  # Eşik değerini düşürdük
    
    # Yeni ağırlıklar ve hesaplama yöntemi
    weighted_cos = (cos_sim + 1) / 2  # Normalize 0-1 arasına
    weighted_euc = max(0, 1 - (euc_dist / EUCLIDEAN_THRESHOLD))
    
    # Cosine similarity'ye daha fazla ağırlık veriyoruz
    similarity_score = (weighted_cos * 0.8) + (weighted_euc * 0.2)
    
    # Daha sıkı eşik değerleri
    if similarity_score >= 0.95:
        interpretation = "Same person (Very high similarity)"
    elif similarity_score >= 0.85:
        interpretation = "Most likely the same person"
    elif similarity_score >= 0.75:
        interpretation = "Similar features present"
    else:
        interpretation = "Different persons"

    return {
        "similarity_score": float(similarity_score * 100),
        "cosine_similarity": float(weighted_cos),
        "euclidean_distance": float(euc_dist),
        "interpretation": interpretation
    }

def main():
    logging.info("Starting camera...")
    video_capture = capture_video(0)
    if video_capture is None or not video_capture.isOpened():
        logging.error("Error: Kamera başlatılamadı.")
        return
    
    reference_image_path = REFERENCE_IMAGE_PATH
    reference_image = cv.imread(reference_image_path)
    if reference_image is None:
        logging.error("Error: Referans görüntü yüklenemedi.")
        return

    reference_vector = convert_to_vector(reference_image)
    if reference_vector is None:
        logging.error("Error: Referans vektör oluşturulamadı.")
        return

    normalized_reference_vector = normalize_vector(reference_vector)
    face_tracker = FaceTracker()
    frame_counter = 0
    detected_face_vector = None

    while True:
        ret, frame = video_capture.read()
        if not ret:
            logging.error("Error: Frame alınamadı.")
            break
        
        frame = cv.flip(frame, 1)
        faces = detect_face(frame)
        frame_counter += 1
        
        tracked_face = face_tracker.update(frame, faces)
        
        if tracked_face is not None:
            x, y, w, h = map(int, tracked_face)  # Integer'a çevir
            
            if frame_counter % 5 == 0:
                try:
                    face_crop = frame[y:y+h, x:x+w]
                    detected_face_vector = convert_to_vector(face_crop)
                    
                    if detected_face_vector is not None:
                        normalized_detected_vector = normalize_vector(detected_face_vector)
                        
                        if normalized_detected_vector is not None:
                            cos_sim = cosine_similarity(normalized_reference_vector, 
                                                      normalized_detected_vector)
                            euc_dist = euclidean_distance(normalized_reference_vector, 
                                                        normalized_detected_vector)
                            result = interpret_similarity(cos_sim, euc_dist)
                            
                            cv.putText(frame, f"Benzerlik: {result}", (10, 30),
                                     cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                            cv.putText(frame, f"Cosine: {cos_sim:.3f}", (10, 60),
                                     cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                            cv.putText(frame, f"Euclidean: {euc_dist:.3f}", (10, 90),
                                     cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                except Exception as e:
                    logging.error(f"Yüz işleme hatası: {str(e)}")
            
            cv.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        cv.imshow('Video', frame)
        
        if cv.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv.destroyAllWindows()

# if __name__ == '__main__':
#     main()