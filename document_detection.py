import cv2
import easyocr
import re
import numpy as np
from datetime import datetime

def preprocess_image(image):
    """Belge görüntüsünü işler"""
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        denoised = cv2.fastNlMeansDenoising(enhanced)
        return denoised
    except Exception as e:
        print(f"Görüntü işleme hatası: {str(e)}")
        return None

def is_valid_name(text):
    """İsim kontrolü yapar"""
    # Tarih formatını kontrol et
    if re.search(r'\d{2}\.\d{2}\.\d{4}', text):
        return False
    
    # Parantez kontrolü
    if '(' in text or ')' in text:
        return False
    
    # Türkçe karakterleri değiştir ve alfanumerik kontrol yap
    normalized_text = text.replace('İ', 'I').replace('Ğ', 'G').replace('Ü', 'U')\
                         .replace('Ş', 'S').replace('Ö', 'O').replace('Ç', 'C')
    
    if not all(c.isalpha() or c.isspace() for c in normalized_text):
        return False
    
    # Kelime sayısı ve uzunluk kontrolü
    words = text.split()
    if len(words) < 2 or any(len(word) < 2 for word in words):
        return False
    
    return True

def extract_info(texts, boxes):
    """Metinlerden bilgileri çıkarır"""
    info = {
        'student_no': None,
        'name_surname': None,
        'department': None,
        'class': None
    }
    
    # Dikey pozisyona göre sırala
    text_with_pos = [(text.strip(), box[0][1]) for text, box in zip(texts, boxes)]
    text_with_pos.sort(key=lambda x: x[1])
    
    for text, _ in text_with_pos:
        # Öğrenci Numarası
        if re.match(r'\b20\d{6}\b', text):
            info['student_no'] = text
            continue
            
        # Ad Soyad
        if is_valid_name(text) and text.isupper():
            info['name_surname'] = text
            continue
            
        # Bölüm
        if 'ENGINEERING' in text.upper() and len(text) > 10:
            info['department'] = text
            continue
            
        # Sınıf
        if text.isdigit() and len(text) == 1 and 1 <= int(text) <= 4:
            info['class'] = text
            continue

    return info

def enhance_document_detection(frame):
    """Belge tespitini iyileştirir"""
    try:
        # Gri tonlamaya çevir
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Gürültü azaltma
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Kenar tespiti
        edges = cv2.Canny(blurred, 75, 200)
        
        # Kontur bulma
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        max_area = 0
        best_rect = None
        
        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
            
            if len(approx) == 4:  # Dörtgen şekil
                area = cv2.contourArea(contour)
                if area > max_area:
                    max_area = area
                    best_rect = approx
        
        if best_rect is not None:
            # Perspektif düzeltme
            pts = best_rect.reshape(4, 2)
            rect = np.zeros((4, 2), dtype="float32")
            
            s = pts.sum(axis=1)
            rect[0] = pts[np.argmin(s)]
            rect[2] = pts[np.argmax(s)]
            
            diff = np.diff(pts, axis=1)
            rect[1] = pts[np.argmin(diff)]
            rect[3] = pts[np.argmax(diff)]
            
            (tl, tr, br, bl) = rect
            
            # Maksimum genişlik ve yükseklik
            widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
            widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
            maxWidth = max(int(widthA), int(widthB))
            
            heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
            heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
            maxHeight = max(int(heightA), int(heightB))
            
            # Perspektif dönüşüm matrisi
            dst = np.array([
                [0, 0],
                [maxWidth - 1, 0],
                [maxWidth - 1, maxHeight - 1],
                [0, maxHeight - 1]], dtype="float32")
            
            M = cv2.getPerspectiveTransform(rect, dst)
            warped = cv2.warpPerspective(frame, M, (maxWidth, maxHeight))
            
            return warped
            
    except Exception as e:
        print(f"Belge geliştirme hatası: {str(e)}")
    
    return frame