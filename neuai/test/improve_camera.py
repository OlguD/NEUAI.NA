import cv2 as cv
import time
from neuai.CameraManager import camera_session
from neuai.face_new_similarity import FaceTracker
from neuai.detect_object import detect_object_type

def main():
    with camera_session() as cam:
        if cam is None:
            print("Could not access camera")
            return

        faceTracker = FaceTracker()

        try:
            # Add a delay to ensure the camera feed window is displayed properly
            time.sleep(2)
            while True:
                success, frame = cam.read_frame()
                if not success:
                    print("Could not read frame")
                    break

                frame = cv.flip(frame, 1) 
                # Resize the frame to reduce the window size
                frame = cv.resize(frame, (640, 480))
                obj_type, confidence, obj_data = detect_object_type(frame)
                if obj_type == "face":
                    tracked_box = faceTracker.update(frame, obj_data)
                    if tracked_box is not None:
                        x, y, w, h = tracked_box
                        # Yumuşatılmış çerçeveyi çiz
                        cv.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

                # Display the frame
                cv.imshow('Camera Feed', frame)

                # Break the loop if 'q' is pressed
                if cv.waitKey(1) & 0xFF == ord('q'):
                    break

        except Exception as e:
            print(f"Frame üretme hatası: {e}")

        finally:
            # Release the camera and close all OpenCV windows
            cam.release()
            cv.destroyAllWindows()

if __name__ == "__main__":
    main()