from flask import Flask, render_template, Response, jsonify, request, send_file
import cv2 as cv
import numpy as np
import logging
from datetime import datetime
from neuai.face_similarity import (FaceTracker, convert_to_vector, 
    normalize_vector, detect_face, cosine_similarity,
    euclidean_distance, interpret_similarity)
import easyocr
from neuai.document_detection import preprocess_image, extract_info
from neuai.detect_object import detect_object_type
from neuai.CameraManager import get_camera_session, CameraSession, CameraManagerSingleton
from neuai.FindStudent import FindStudent
from dotenv import load_dotenv
import os
import time

load_dotenv()

app = Flask(__name__)

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
        if not isinstance(faces, np.ndarray) or faces.size == 0:
            return {"error": "Yüz tespit edilemedi"}

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
    camera_session = get_camera_session()
    if camera_session is None:
        print("Kamera başlatılamadı")
        return

    try:
        face_tracker = FaceTracker()
        frame_count = 0
        last_frame_time = time.time()
        
        while True:
            success, frame = camera_session.read_frame()
            if not success:
                print("Kamera görüntüsü alınamadı")
                time.sleep(0.1)  # Kısa bekle ve tekrar dene
                continue
                
            # FPS loglama
            frame_count += 1
            current_time = time.time()
            if current_time - last_frame_time >= 1.0:
                fps = frame_count / (current_time - last_frame_time)
                logging.debug(f"Video feed FPS: {fps:.2f}")
                frame_count = 0
                last_frame_time = current_time
            
            frame = cv.flip(frame, 1)

            # Nesne tespiti yap
            obj_type, confidence, obj_data = detect_object_type(frame)

            if obj_type == "face" and isinstance(obj_data, np.ndarray) and len(obj_data) > 0:
                tracked_box = face_tracker.update(frame, obj_data)
                
                if tracked_box is not None:
                    x, y, w, h = tracked_box
                    cv.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                            
            elif obj_type == "document" and obj_data is not None:
                cv.drawContours(frame, [obj_data], -1, (0, 255, 0), 2)
                face_tracker = FaceTracker()

            try:
                ret, buffer = cv.imencode('.jpg', frame, [cv.IMWRITE_JPEG_QUALITY, 85])
                if not ret:
                    print("Çerçeve kodlanamadı")
                    continue

                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            except Exception as e:
                logging.error(f"Frame encoding error: {str(e)}")
                continue

    except Exception as e:
        print(f"Hata oluştu: {e}")
        logging.error(f"Frame üretme hatası: {e}")
    finally:
        camera_session.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    stream = generate_frames()
    if stream:
        return Response(stream, 
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    return "Kamera başlatılamadı", 500

@app.route('/detect_object')
def detect_object():
    camera_session = get_camera_session()
    if camera_session is None:
        return jsonify({"error": "Could not access camera"})

    try:
        success, frame = camera_session.read_frame()
        if not success:
            return jsonify({"error": "Could not read frame"})
            
        object_type, confidence, _ = detect_object_type(frame)
        return jsonify({
            "type": object_type,
            "confidence": float(confidence)
        })
    finally:
        camera_session.release()

@app.route('/analyze_face')
def analyze_face():
    camera_session = get_camera_session()
    if camera_session is None:
        return jsonify({"error": "Could not access camera"})

    try:
        success, frame = camera_session.read_frame()
        if not success:
            return jsonify({"error": "Could not read frame"})
            
        result = analyze_face_similarity(frame, os.getenv("IMAGE2_PATH"))
        return jsonify(result)
    except Exception as e:
        logging.error(f"Analiz hatası: {str(e)}")
        return jsonify({"error": str(e)})
    finally:
        camera_session.release()

@app.route('/document_analysis')
def document_analysis():
    camera_session = get_camera_session()
    if camera_session is None:
        return jsonify({"error": "Could not access camera"})

    try:
        success, frame = camera_session.read_frame()
        if not success:
            return jsonify({"error": "Could not read frame"})
            
        result = analyze_document_frame(frame)
        
        if "error" not in result:
            logging.info(f"Belge analiz sonucu: {result}")
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Belge analiz endpoint hatası: {str(e)}")
        return jsonify({"error": str(e)})
    finally:
        camera_session.release()
# app.py
@app.route('/find_student')
def find_student():
    school_number = request.headers.get("X-School-Number")
    try:
        image_path = FindStudent.find_by_school_number(school_number)
        return jsonify({"image_path": image_path})

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/get_student_image/<school_number>')
def get_student_image(school_number):
    try:
        image_path = FindStudent.find_by_school_number(school_number)
        return send_file(image_path, mimetype='image/jpeg')
    except Exception as e:
        return jsonify({"error": str(e)})

def main():
    """Flask sunucusunu başlatmak için bir giriş noktası."""
    app.run(debug=True)

if __name__ == '__main__':
    main()