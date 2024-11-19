from flask import Flask, render_template, Response, jsonify
import cv2 as cv
import numpy as np
import logging
from face_new_similarity import (FaceTracker, REFERENCE_IMAGE_PATH, 
    convert_to_vector, normalize_vector, detect_face, cosine_similarity, euclidean_distance,
    interpret_similarity)
import easyocr
from document_detection import preprocess_image, extract_info
from face_detection import detect_face, capture_video, get_frame
from detect_object import detect_object_type, detect_document_features
from datetime import datetime

app = Flask(__name__)

# Configuration
CASCADE_PATH = "/Users/olgudegirmenci/Desktop/NEUAI.NA/core/haarcascade_frontalface_default.xml"
VIDEO_SOURCE = 0

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def analyze_face_similarity(frame, reference_img_path):
    """Yüz benzerliği analizi yapar"""
    try:
        reference_image = cv.imread(reference_img_path)
        if reference_image is None:
            return {"error": "Referans görüntü yüklenemedi"}

        reference_vector = convert_to_vector(reference_image)
        if reference_vector is None:
            return {"error": "Referans vektör oluşturulamadı"}

        normalized_reference_vector = normalize_vector(reference_vector)
        
        faces = detect_face(frame)
        # NumPy array kontrolünü düzelt
        if not isinstance(faces, np.ndarray) or faces.size == 0:
            return {"error": "Yüz tespit edilemedi"}

        # En büyük yüzü seç
        face = max(faces, key=lambda rect: rect[2] * rect[3])
        x, y, w, h = map(int, face)
        face_crop = frame[y:y+h, x:x+w]
        
        detected_face_vector = convert_to_vector(face_crop)
        if detected_face_vector is None:
            return {"error": "Yüz vektörü oluşturulamadı"}

        normalized_detected_vector = normalize_vector(detected_face_vector)
        
        cos_sim = cosine_similarity(normalized_reference_vector, normalized_detected_vector)
        euc_dist = euclidean_distance(normalized_reference_vector, normalized_detected_vector)
        
        result = interpret_similarity(cos_sim, euc_dist)
        logging.info(f"Analiz sonucu: {result}")
        return result

    except Exception as e:
        logging.error(f"Yüz analizi hatası: {str(e)}")
        return {"error": str(e)}

def analyze_document_frame(frame):
    """Belge analizi yapar"""
    try:
        processed = preprocess_image(frame)
        reader = easyocr.Reader(['tr', 'en'])
        results = reader.readtext(processed)
        
        if not results:
            return {"error": "Belgede metin tespit edilemedi"}
            
        texts = [result[1] for result in results]
        boxes = [result[0] for result in results]
        info = extract_info(texts, boxes)
        
        if not any(info.values()):
            return {"error": "Belge bilgileri okunamadı"}
            
        info['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return info
        
    except Exception as e:
        logging.error(f"Belge analiz hatası: {str(e)}")
        return {"error": str(e)}

def generate_frames():
    capture = capture_video(VIDEO_SOURCE)
    face_tracker = FaceTracker()
    object_detected = False  # Nesne tespit durumunu kontrol eden bayrak

    try:
        while True:
            frame = get_frame(capture)
            if frame is None:
                break

            # İlk çerçevede nesne tespiti yap
            if not object_detected:
                obj_type, confidence, obj_data = detect_object_type(frame)
                object_detected = True  # Nesne tespitini yalnızca bir kez yap
            else:
                obj_type, confidence, obj_data = "unknown", 0.0, None  # Tespiti durdur

            # Tespit edilen nesneye göre çizim yap
            if obj_type == "face" and isinstance(obj_data, np.ndarray) and len(obj_data) > 0:
                for (x, y, w, h) in obj_data:
                    cv.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv.putText(frame, "Face", (x, y-10),
                               cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            elif obj_type == "document" and obj_data is not None:
                cv.drawContours(frame, [obj_data], -1, (0, 255, 0), 2)
                cv.putText(frame, "Document", (10, 30),
                           cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # Frame'i gönder
            ret, buffer = cv.imencode('.jpg', frame, [cv.IMWRITE_JPEG_QUALITY, 85])
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    except Exception as e:
        logging.error(f"Frame üretme hatası: {e}")
    finally:
        capture.release()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/detect_object')
def detect_object():
    try:
        capture = capture_video(VIDEO_SOURCE)
        frame = get_frame(capture)
        if frame is not None:
            object_type, confidence, _ = detect_object_type(frame)
            capture.release()
            
            response = {
                "type": object_type,
                "confidence": float(confidence)
            }
            logging.info(f"Tespit sonucu: {response}")  # Log ekle
            return jsonify(response)
            
        capture.release()
        return jsonify({"error": "Frame alınamadı"})
    except Exception as e:
        logging.error(f"Tespit hatası: {str(e)}")
        return jsonify({"error": str(e)})

@app.route('/analyze_face')
def analyze_face():
    try:
        capture = capture_video(VIDEO_SOURCE)
        frame = get_frame(capture)
        if frame is not None:
            result = analyze_face_similarity(frame, REFERENCE_IMAGE_PATH)
            capture.release()
            return jsonify(result)
        capture.release()
        return jsonify({"error": "Frame alınamadı"})
    except Exception as e:
        logging.error(f"Analiz hatası: {str(e)}")
        return jsonify({"error": str(e)})

@app.route('/document_analysis')
def document_analysis():
    try:
        capture = capture_video(VIDEO_SOURCE)
        frame = get_frame(capture)
        
        if frame is None:
            return jsonify({"error": "Görüntü alınamadı"})
            
        result = analyze_document_frame(frame)
        
        if "error" not in result:
            logging.info(f"Belge analiz sonucu: {result}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"student_info_{timestamp}.txt"
            
            # try:
            #     with open(filename, 'w', encoding='utf-8') as f:
            #         f.write("=== STUDENT INFORMATION ===\n")
            #         for key, value in result.items():
            #             if value:
            #                 f.write(f"{key}: {value}\n")
            # except Exception as e:
            #     logging.error(f"Dosya kayıt hatası: {str(e)}")
        
        capture.release()
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Belge analiz endpoint hatası: {str(e)}")
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)