import os
from dotenv import load_dotenv

load_dotenv()

class FindStudent:
    @staticmethod
    def find_by_school_number(school_number):
        student_image_path = os.getenv("IMAGE_FOLDER_PATH")
        if not student_image_path:
            raise ValueError("STUDENT_IMAGE_PATH is not set in the environment variables.")
        
        for root, dirs, files in os.walk(student_image_path):
            for file in files:
                if school_number in file:
                    return os.path.join(root, file)
        return None

