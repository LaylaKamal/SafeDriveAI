"""
Step 3-4: Face Mesh + landmark extraction
Face detection and returning landmarks for analysis
"""

import os
import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.framework.formats import landmark_pb2

try:
    drawing_utils = mp.solutions.drawing_utils
    drawing_styles = mp.solutions.drawing_styles
except Exception:
    drawing_utils = None
    drawing_styles = None


class FaceMeshDetector:
    """Face detection and landmark extraction engine"""

    def __init__(self):
        model_path = os.path.join(os.path.dirname(__file__), "face_landmarker.task")

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model file not found: {model_path}\n"
                "Make sure face_landmarker.task exists inside the vision folder."
            )

        base_options = python.BaseOptions(
            model_asset_path=model_path,
            delegate=python.BaseOptions.Delegate.CPU,
        )

        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1,
        )

        self._face_landmarker = vision.FaceLandmarker.create_from_options(options)
        self._frame_count = 0

    def process(self, frame):
        """
        Process frame and return result

        Args:
            frame: BGR image from OpenCV

        Returns:
            tuple: (face_detected: bool, landmarks: list or None)
        """
        if frame is None:
            return False, None

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        timestamp_ms = int(self._frame_count * 1000 / 30)
        self._frame_count += 1

        detection_result = self._face_landmarker.detect_for_video(mp_image, timestamp_ms)

        if not detection_result.face_landmarks:
            return False, None

        landmarks = detection_result.face_landmarks[0]
        return True, landmarks

    def draw_landmarks(self, frame, landmarks):
        """
        Draw landmarks on frame for testing

        Args:
            frame: OpenCV BGR image
            landmarks: list of normalized landmarks from MediaPipe Tasks
        """
        if (
            frame is None
            or landmarks is None
            or drawing_utils is None
            or drawing_styles is None
        ):
            return

        landmark_list = landmark_pb2.NormalizedLandmarkList()

        for lm in landmarks:
            landmark_list.landmark.add(x=lm.x, y=lm.y, z=lm.z)

        drawing_utils.draw_landmarks(
            image=frame,
            landmark_list=landmark_list,
            connections=mp.solutions.face_mesh.FACEMESH_TESSELATION,
            landmark_drawing_spec=None,
            connection_drawing_spec=drawing_styles.get_default_face_mesh_tesselation_style(),
        )

    def close(self):
        """Close engine"""
        if self._face_landmarker:
            self._face_landmarker.close()


def get_landmark_point(landmarks, index):
    """
    Extract point coordinates from landmarks

    Args:
        landmarks: landmark list
        index: landmark index

    Returns:
        tuple(x, y) or None
    """
    if landmarks is None or index >= len(landmarks):
        return None

    lm = landmarks[index]
    return (lm.x, lm.y)


def run_face_mesh_test():
    """Test run to verify Face Mesh works"""
    try:
        from .camera import open_camera, read_frame, release_camera
    except ImportError:
        from camera import open_camera, read_frame, release_camera

    cap = open_camera(0)

    if cap is None or not cap.isOpened():
        print("Error: Cannot open camera")
        return

    detector = FaceMeshDetector()
    print("System Started - Press ESC to exit")

    try:
        while True:
            success, frame = read_frame(cap)
            if not success or frame is None:
                continue

            frame = cv2.flip(frame, 1)

            face_detected, landmarks = detector.process(frame)

            if face_detected and landmarks:
                detector.draw_landmarks(frame, landmarks)

            cv2.imshow("SafeDrive AI - Face Mesh Test", frame)

            if cv2.waitKey(5) & 0xFF == 27:
                break

    finally:
        detector.close()
        release_camera(cap)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    run_face_mesh_test()
