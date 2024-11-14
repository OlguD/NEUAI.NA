import cv2
import easyocr
import re
import numpy as np
from datetime import datetime

def capture_image():
    cap = cv2.VideoCapture(0)
    cv2.waitKey(1000)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Camera image could not be obtained")
            break
            
        cv2.imshow('Point to the document and press SPACE (Exit: Q)', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            return None
        elif key == ord(' '):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    return frame

def preprocess_image(image):
    """NEU DOCUMENT"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    denoised = cv2.fastNlMeansDenoising(enhanced)
    return denoised

def is_valid_name(text):
    if re.search(r'\d{2}\.\d{2}\.\d{4}', text):
        return False
    
    if '(' in text or ')' in text:
        return False
    
    if not all(c.isalpha() or c.isspace() for c in text.replace('İ', 'I').replace('Ğ', 'G').replace('Ü', 'U').replace('Ş', 'S').replace('Ö', 'O').replace('Ç', 'C')):
        return False
    
    words = text.split()
    if len(words) < 2:
        return False
    
    if any(len(word) < 2 for word in words):
        return False
    
    return True

def extract_info(texts, boxes):
    info = {
        'student_no': None,
        'name_surname': None,
        'department': None,
        'class': None
    }
    
    text_with_pos = [(text.strip(), box[0][1]) for text, box in zip(texts, boxes)]
    text_with_pos.sort(key=lambda x: x[1])
    
    for text, y_pos in text_with_pos:
        # Student Number
        if re.match(r'\b20\d{6}\b', text):
            info['student_no'] = text
            
        # Name Surname
        elif is_valid_name(text) and text.isupper():
            info['name_surname'] = text
            
        # Department
        elif ('ENGINEERING' in text.upper()) and len(text) > 10:
            info['department'] = text
            
        # Class
        elif text.isdigit() and len(text) == 1 and 1 <= int(text) <= 4:
            info['class'] = text

    return info

def main():
    reader = easyocr.Reader(['tr', 'en'])
    
    while True:
        print("\nNEU Student Document Reader")
        print("1. Capture new photo")
        print("2. Exit")
        
        choice = input("Your choice (1-2): ")
        
        if choice == '2':
            break
        elif choice == '1':
            print("\nPoint the document to the camera and press SPACE...") 
            image = capture_image()
            
            if image is None:
                continue
            
            processed = preprocess_image(image)
            
            print("\nDocument is being read...")
            results = reader.readtext(processed)
            
            texts = [result[1] for result in results]
            boxes = [result[0] for result in results]
            
            info = extract_info(texts, boxes)
            
            print("\n=== RESULTS ===")
            print(f"Student No: {info['student_no'] or 'Not found'}")
            print(f"Name & Surname: {info['name_surname'] or 'Not found'}")
            print(f"Department: {info['department'] or 'Not found'}")
            print(f"Class: {info['class'] or 'Not found'}")
            print("==============")
            
            if info['student_no']:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"student_info_{timestamp}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=== STUDENT INFORMATION ===\n")
                    f.write(f"Student No: {info['student_no']}\n")
                    f.write(f"Name & Surname: {info['name_surname']}\n")
                    f.write(f"Department: {info['department']}\n")
                    f.write(f"Class: {info['class']}\n")
                print(f"\nInformation saved to '{filename}' file.")
            
            input("\nPress ENTER to continue...")
        else:
            print("Invalid selection!")

if __name__ == "__main__":
    main()
