import cv2 as cv
import numpy as np
import logging
from face_detection import detect_face

def check_face_detection(faces):
    try:
        if faces is None:
            return False, 0

        if not isinstance(faces, np.ndarray):
            return False, 0
        
        if len(faces) == 0:
            return False, 0

        max_area = 0
        for face in faces:
            try:
                width = int(face[2])  # Genişlik
                height = int(face[3])  # Yükseklik
                area = width * height
                if area > max_area:
                    max_area = area
            except (IndexError, TypeError):
                continue
        
        return bool(max_area > 0), float(max_area)

    except Exception as e:
        logging.error(f"Yüz kontrol hatası: {str(e)}")
        return False, 0.0

def detect_document_features(frame):
    """Belge özelliklerini tespit eder"""
    try:
        # Görüntüyü işle
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        blurred = cv.GaussianBlur(gray, (5, 5), 0)
        edges = cv.Canny(blurred, 50, 150)
        
        # Kenarları güçlendir
        kernel = np.ones((5,5), np.uint8)
        dilated = cv.dilate(edges, kernel, iterations=2)
        
        # Konturları bul
        contours, _ = cv.findContours(dilated, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        
        max_area = 0
        best_contour = None
        frame_area = float(frame.shape[0] * frame.shape[1])
        
        for contour in contours:
            perimeter = cv.arcLength(contour, True)
            approx = cv.approxPolyDP(contour, 0.02 * perimeter, True)
            
            if len(approx) == 4:  # Dörtgen şekil
                area = cv.contourArea(contour)
                if area > frame_area * 0.1:  # Frame'in en az %10'u kadar büyük olmalı
                    rect = cv.minAreaRect(contour)
                    width = rect[1][0]
                    height = rect[1][1]
                    
                    # En-boy oranı kontrolü
                    if width > 0 and height > 0:
                        aspect_ratio = max(width, height) / min(width, height)
                        if 1 < aspect_ratio < 2:  # Makul bir en-boy oranı
                            if area > max_area:
                                max_area = area
                                best_contour = approx

        is_document = max_area > frame_area * 0.1
        confidence = (max_area / frame_area) if is_document else 0
        
        return is_document, confidence, best_contour
        
    except Exception as e:
        logging.error(f"Belge özellik tespiti hatası: {str(e)}")
        return False, 0, None

def detect_object_type(frame):
    try:
        # Yüz tespiti
        faces = detect_face(frame)
        logging.info(f"Tespit edilen yüzler: {faces}")  # Debug için

        if faces is not None and len(faces) > 0:
            logging.info("Yüz tespit edildi!")
            # En büyük yüzü bul
            max_area = 0
            for face in faces:
                w = int(face[2])
                h = int(face[3])
                area = w * h
                if area > max_area:
                    max_area = area

            if max_area > 0:
                frame_area = frame.shape[0] * frame.shape[1]
                confidence = max_area / frame_area
                logging.info(f"Yüz alanı: {max_area}, Frame alanı: {frame_area}, Güven: {confidence}")
                return "face", float(confidence), faces

        # Yüz yoksa belge kontrolü yap
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        blurred = cv.GaussianBlur(gray, (5, 5), 0)
        edges = cv.Canny(blurred, 50, 150)
        contours, _ = cv.findContours(edges, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        max_area = 0
        is_document = False
        document_contour = None

        for contour in contours:
            area = cv.contourArea(contour)
            if area > max_area:
                perimeter = cv.arcLength(contour, True)
                approx = cv.approxPolyDP(contour, 0.02 * perimeter, True)
                if len(approx) == 4:  # Dörtgen şekil
                    max_area = area
                    document_contour = approx
                    is_document = True

        if is_document:
            frame_area = frame.shape[0] * frame.shape[1]
            confidence = max_area / frame_area
            logging.info(f"Belge tespit edildi. Alan: {max_area}, Güven: {confidence}")
            return "document", float(confidence), document_contour

        logging.info("Nesne tespit edilemedi")
        return "unknown", 0.0, None

    except Exception as e:
        logging.error(f"Nesne tespiti hatası: {str(e)}")
        return "unknown", 0.0, None