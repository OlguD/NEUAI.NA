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

def extract_info(texts, boxes, image=None):
    """Metinlerden öğrenci numarasını çıkarır"""
    info = {
        'student_no': None
    }
    
    # Check each text for student number pattern
    for text in texts:
        # Clean the text and check for student number pattern (20xxxxxx)
        cleaned_text = ''.join(filter(str.isdigit, text.strip()))
        if re.match(r'^20\d{6}$', cleaned_text):
            info['student_no'] = cleaned_text
            break
    
    return info