import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class FindStudent:
    @staticmethod
    def find_by_school_number(school_number):
        relative_path = os.getenv("IMAGE_FOLDER_PATH")
        if not relative_path:
            raise ValueError("IMAGE_FOLDER_PATH is not set in the environment variables.")
        
        # Convert relative path to absolute path
        absolute_path = Path(relative_path).resolve()
        
        for root, dirs, files in os.walk(absolute_path):
            for file in files:
                if school_number in file:
                    return os.path.join(root, file)
        return None

