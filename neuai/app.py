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
from werkzeug.utils import secure_filename
import base64
import json
import pandas as pd
import io

load_dotenv()

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_face_similarity(frame, reference_img_path):
    """Yüz benzerliği analizi yapar"""
    try:
        reference_image = cv.imread(reference_img_path)
        if (reference_image is None):
            return {"error": "Referans görüntü yüklenemedi"}

        reference_vector = convert_to_vector(reference_image)
        if (reference_vector is None):
            return {"error": "Referans vektör oluşturulamadı"}

        normalized_reference_vector = normalize_vector(reference_vector)
        
        faces = detect_face(frame)
        if (not isinstance(faces, np.ndarray) or faces.size == 0):
            return {"error": "Yüz tespit edilemedi"}

        face = max(faces, key=lambda rect: rect[2] * rect[3])
        x, y, w, h = map(int, face)
        face_crop = frame[y:y+h, x:x+w]
        
        detected_face_vector = convert_to_vector(face_crop)
        if (detected_face_vector is None):
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
        
        if (not results):
            return {"error": "Belgede metin tespit edilemedi"}
            
        texts = [result[1] for result in results]
        boxes = [result[0] for result in results]
        info = extract_info(texts, boxes)
        
        if (not any(info.values())):
            return {"error": "Belge bilgileri okunamadı"}
            
        info['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return info
        
    except Exception as e:
        logging.error(f"Belge analiz hatası: {str(e)}")
        return {"error": str(e)}

def generate_frames():
    camera_session = get_camera_session()
    if (camera_session is None):
        print("Kamera başlatılamadı")
        return

    try:
        face_tracker = FaceTracker()
        frame_count = 0
        last_frame_time = time.time()
        
        while True:
            success, frame = camera_session.read_frame()
            if (not success):
                print("Kamera görüntüsü alınamadı")
                time.sleep(0.1)  # Kısa bekle ve tekrar dene
                continue
                
            # FPS loglama
            frame_count += 1
            current_time = time.time()
            if (current_time - last_frame_time >= 1.0):
                fps = frame_count / (current_time - last_frame_time)
                logging.debug(f"Video feed FPS: {fps:.2f}")
                frame_count = 0
                last_frame_time = current_time
            
            frame = cv.flip(frame, 1)

            # Nesne tespiti yap
            obj_type, confidence, obj_data = detect_object_type(frame)

            if (obj_type == "face" and isinstance(obj_data, np.ndarray) and len(obj_data) > 0):
                tracked_box = face_tracker.update(frame, obj_data)
                
                if (tracked_box is not None):
                    x, y, w, h = tracked_box
                    cv.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                            
            elif (obj_type == "document" and obj_data is not None):
                cv.drawContours(frame, [obj_data], -1, (0, 255, 0), 2)
                face_tracker = FaceTracker()

            try:
                ret, buffer = cv.imencode('.jpg', frame, [cv.IMWRITE_JPEG_QUALITY, 85])
                if (not ret):
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
def intro():
    return render_template('intro.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    stream = generate_frames()
    if (stream):
        return Response(stream, 
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    return "Kamera başlatılamadı", 500

@app.route('/detect_object')
def detect_object():
    camera_session = get_camera_session()
    if (camera_session is None):
        return jsonify({"error": "Could not access camera"})

    try:
        success, frame = camera_session.read_frame()
        if (not success):
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
    school_number = request.headers.get("X-School-Number")
    if (not school_number):
        return jsonify({"error": "School number is required"})

    camera_session = get_camera_session()
    if (camera_session is None):
        return jsonify({"error": "Could not access camera"})

    try:
        # Önce öğrenci fotoğrafını bul
        student_image_path = FindStudent.find_by_school_number(school_number)
        if (not student_image_path):
            return jsonify({"error": f"No image found for student number {school_number}"})

        # Kameradan frame al
        success, frame = camera_session.read_frame()
        if (not success):
            return jsonify({"error": "Could not read frame"})
            
        result = analyze_face_similarity(frame, student_image_path)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Analiz hatası: {str(e)}")
        return jsonify({"error": str(e)})
    finally:
        camera_session.release()

@app.route('/document_analysis')
def document_analysis():
    camera_session = get_camera_session()
    if (camera_session is None):
        return jsonify({"error": "Could not access camera"})

    try:
        success, frame = camera_session.read_frame()
        if (not success):
            return jsonify({"error": "Could not read frame"})
            
        result = analyze_document_frame(frame)
        
        if ("error" not in result):
            logging.info(f"Belge analiz sonucu: {result}")
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Belge analiz endpoint hatası: {str(e)}")
        return jsonify({"error": str(e)})
    finally:
        camera_session.release()

@app.route('/upload_document', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file and allowed_file(file.filename):
        try:
            file_bytes = file.read()
            nparr = np.frombuffer(file_bytes, np.uint8)
            frame = cv.imdecode(nparr, cv.IMREAD_COLOR)
            
            if frame is None:
                return jsonify({"error": "Could not process image"}), 400
            
            _, buffer = cv.imencode('.jpg', frame)
            img_str = base64.b64encode(buffer).decode('utf-8')
            
            result = analyze_document_frame(frame)
            result['image_preview'] = f"data:image/jpeg;base64,{img_str}"
            
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"Document upload analysis error: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Invalid file type"}), 400

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

@app.route('/save_attendance', methods=['POST'])
def save_attendance():
    try:
        data = request.json
        
        if not data or 'schoolNumber' not in data or 'courses' not in data:
            return jsonify({"error": "Invalid data format"})
        
        # Add timestamp using local time instead of UTC
        current_time = datetime.now()
        data['timestamp'] = current_time.isoformat()
            
        # Ensure the attendance directory exists
        attendance_dir = os.path.join(app.static_folder, 'attendance')
        os.makedirs(attendance_dir, exist_ok=True)
        
        # Create a filename based on date only
        date_str = current_time.strftime('%Y%m%d')
        filename = f"{date_str}.json"
        filepath = os.path.join(attendance_dir, filename)
        
        # Check if file exists and append to it
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    attendance_data = json.load(f)
                    
                # Check if it's a list of records (new format)
                if not isinstance(attendance_data, list):
                    attendance_data = [attendance_data]  # Convert old format to new format
                
                # Check if student already exists for this day
                student_exists = False
                for i, student in enumerate(attendance_data):
                    if student.get('schoolNumber') == data['schoolNumber']:
                        # Update existing student record
                        attendance_data[i] = data
                        student_exists = True
                        break
                
                if not student_exists:
                    # Add new student record
                    attendance_data.append(data)
            except json.JSONDecodeError:
                # File exists but is not valid JSON, create new
                attendance_data = [data]
        else:
            # Create new file with a list of student records
            attendance_data = [data]
        
        # Save the data to a JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(attendance_data, f, ensure_ascii=False, indent=4)
            
        return jsonify({"success": True, "message": "Attendance saved successfully"})
        
    except Exception as e:
        return jsonify({"error": f"Failed to save attendance: {str(e)}"})

@app.route('/export-to-excel', methods=['POST'])
def export_to_excel():
    try:
        # Get selected exams from request
        data = request.get_json()
        selected_exams = data.get('exams', [])
        
        if not selected_exams:
            return jsonify({"error": "No exams selected"}), 400
            
        # Create the attendance directory path
        attendance_dir = os.path.join(app.static_folder, 'attendance')
        
        # Check if directory exists
        if not os.path.exists(attendance_dir):
            return jsonify({"error": "No attendance records found"}), 404
        
        # Get current date for filename
        current_date = datetime.now().strftime('%Y%m%d')
        current_day_file = f"{current_date}.json"
        file_path = os.path.join(attendance_dir, current_day_file)
        
        # Check if current day's attendance file exists
        if not os.path.exists(file_path):
            return jsonify({"error": f"No attendance records found for today ({current_date})"}), 404
        
        # Debug: Print full path
        print(f"Looking for attendance file at: {file_path}")    
            
        # Dictionary to store student records by school number
        student_records = {}
        
        # Process current day's file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
                print(f"File content length: {len(file_content)}")
                file_data = json.loads(file_content)
                
            # Debug information
            print(f"Loaded JSON data, type: {type(file_data)}")
            if isinstance(file_data, list):
                print(f"Number of students in file: {len(file_data)}")
                for i, student in enumerate(file_data):
                    print(f"Student {i+1}: {student.get('schoolNumber', 'No school number')}")
                
            # Make sure file_data is a list
            if not isinstance(file_data, list):
                print("Converting file_data to list")
                file_data = [file_data]
                
            # Process each student record
            for student in file_data:
                # Get student's school number
                school_number = student.get('schoolNumber', '')
                if not school_number:
                    print("Skipping student with no school number")
                    continue
                    
                print(f"Processing student: {school_number}")
                
                # Get student's courses
                student_courses = student.get('courses', [])
                print(f"Student courses: {student_courses}")
                
                # No longer filtering by matching courses - include all students
                # Format student courses as comma-separated string
                courses_str = ', '.join(student_courses)
                
                # Extract timestamp info 
                timestamp = student.get('timestamp', '')
                date = ''
                time = ''
                
                # Parse timestamp using local time format
                if timestamp:
                    try:
                        # Handle different timestamp formats
                        if '.' in timestamp:
                            # Remove timezone if present
                            if '+' in timestamp:
                                timestamp = timestamp.split('+')[0]
                            dt = datetime.fromisoformat(timestamp)
                        else:
                            dt = datetime.fromisoformat(timestamp)
                        
                        date = dt.strftime('%Y-%m-%d')
                        time = dt.strftime('%H:%M:%S')
                    except Exception as e:
                        print(f"Error parsing timestamp {timestamp}: {e}")
                        # Fallback - try to extract date and time portions
                        if 'T' in timestamp:
                            date_part = timestamp.split('T')[0]
                            time_part = timestamp.split('T')[1].split('.')[0] if '.' in timestamp else timestamp.split('T')[1]
                            date = date_part
                            time = time_part
                    
                # Extract student info from documentInfo if available
                document_info = student.get('documentInfo', {})
                name = document_info.get('nameSurname', '')
                department = document_info.get('department', '')
                student_class = document_info.get('class', '')
                
                # Create or update student record
                if school_number in student_records:
                    # Update existing record's courses
                    current_courses = student_records[school_number]['Exams']
                    # Merge and deduplicate courses
                    all_courses = set(current_courses.split(', ') if current_courses else [])
                    all_courses.update(student_courses)
                    student_records[school_number]['Exams'] = ', '.join(sorted(all_courses))
                else:
                    # Create new record for this student
                    student_records[school_number] = {
                        'Date': date,
                        'Time': time,
                        'School Number': school_number,
                        'Name': name,
                        'Department': department,
                        'Class': student_class,
                        'Exams': courses_str,
                        'Attendance': 'Present' if student.get('attendance', False) else 'Absent'
                    }
                    
                    # Add similarity score if available
                    face_analysis = student.get('faceAnalysis', {})
                    if face_analysis and 'similarity_score' in face_analysis:
                        student_records[school_number]['Similarity Score'] = f"{face_analysis['similarity_score']:.2f}%"
                        student_records[school_number]['Result'] = face_analysis.get('interpretation', '')
                    
            # Print debug info about the records being processed
            print(f"Total student records to export: {len(student_records)}")
            for record in student_records.values():
                print(f"Student: {record.get('School Number')} - Exams: {record.get('Exams')}")
                
        except Exception as e:
            import traceback
            print(f"Error processing file {current_day_file}: {e}")
            traceback.print_exc()
            return jsonify({"error": f"Failed to process attendance data: {str(e)}"}), 500
        
        # Convert dictionary to list of records
        all_records = list(student_records.values())
        
        if not all_records:
            return jsonify({"error": "No records found for today"}), 404
        
        # Convert records to DataFrame
        df = pd.DataFrame(all_records)
        
        # Sort by time and school number
        if 'Time' in df.columns:
            df = df.sort_values(by=['Time', 'School Number'])
        else:
            df = df.sort_values(by=['School Number'])
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Today\'s Attendance', index=False)
            
            # Auto-adjust columns' width
            worksheet = writer.sheets['Today\'s Attendance']
            for i, col in enumerate(df.columns):
                column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, column_width)
        
        output.seek(0)
        
        # Return Excel file
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'attendance_export_{current_date}.xlsx'
        )
            
    except Exception as e:
        import traceback
        print(f"Export error: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Export failed: {str(e)}"}), 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


def main():
    """Flask sunucusunu başlatmak için bir giriş noktası."""
    app.run(debug=True)

if __name__ == '__main__':
    main()