from flask import Flask, render_template, Response, jsonify
import cv2 as cv
import logging
from face_similarity import calculate_face_similarity
import easyocr
from document_detection import capture_image, preprocess_image, extract_info
from face_detection import detect_face, capture_video, get_frame

app = Flask(__name__)

# Configuration
CASCADE_PATH = "/Users/olgudegirmenci/Desktop/NEUAI.NA/core/haarcascade_frontalface_default.xml"
IMAGE2_PATH = '/Users/olgudegirmenci/Desktop/NEUAI.NA/core/IMG_1546.jpg'
VIDEO_SOURCE = 0  # or your video source

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(asctime)s - %(message)s')

def generate_frames():
    capture = capture_video(VIDEO_SOURCE)
    try:
        while True:
            frame = get_frame(capture)
            if frame is not None:
                frame = detect_face(frame)
                frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)  # Convert BGR to RGB
                ret, buffer = cv.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                break
    except Exception as e:
        logging.error(f"Error generating frames: {e}")
    finally:
        capture.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/analyze_image')
def analyze_image():
    capture = capture_video(VIDEO_SOURCE)
    frame = get_frame(capture)
    if frame is not None:
        detected_faces = detect_face(frame)
        similarity = calculate_face_similarity(frame, IMAGE2_PATH)
        capture.release()
        return jsonify(similarity)
    capture.release()
    return jsonify({"error": "No frame captured"})

@app.route('/document_analysis')
def document_analysis():
    try:
        image = capture_image()
        if image is not None:
            processed = preprocess_image(image)
            reader = easyocr.Reader(['tr', 'en'])
            results = reader.readtext(processed)
            texts = [result[1] for result in results]
            boxes = [result[0] for result in results]
            info = extract_info(texts, boxes)
            return jsonify(info)
        return jsonify({"error": "No image captured"})
    except Exception as e:
        logging.error(f"Error analyzing document: {e}")
        return jsonify({"error": "An error occurred"})

if __name__ == '__main__':
    app.run(debug=True)