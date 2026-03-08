"""
Step 12: Unified API
analyze_driver(frame) - takes frame and returns all results
"""
try:
    from .face_mesh import FaceMeshDetector
    from .eye_detection import EyeStateTracker
    from .fatigue_score import get_combined_result
except ImportError:
    from face_mesh import FaceMeshDetector
    from eye_detection import EyeStateTracker
    from fatigue_score import get_combined_result


class DetectorManager:
    """Detector manager - created once and used for each frame"""

    def __init__(self):
        self.face_detector = FaceMeshDetector()
        self.eye_tracker = EyeStateTracker()

    def analyze_driver(self, frame):
        """
        Main function - takes camera frame and returns full driver state
        
        Args:
            frame: BGR image from cv2.VideoCapture or Flask
            
        Returns:
            dict: {
                "driver_detected": bool,
                "eyes_closed": bool,
                "yawning": bool,
                "head_drop": bool,
                "ear": float,
                "mar": float,
                "alertness_score": int,
                "risk_level": str
            }
        """
        face_detected, landmarks = self.face_detector.process(frame)

        if not face_detected or landmarks is None:
            return {
                "driver_detected": False,
                "eyes_closed": False,
                "yawning": False,
                "head_drop": False,
                "ear": 0.0,
                "mar": 0.0,
                "alertness_score": 0,
                "risk_level": "unknown",
                "landmarks": None,
            }

        # Full analysis
        result = get_combined_result(landmarks, eye_tracker=self.eye_tracker)

        return {
            "driver_detected": True,
            "eyes_closed": result["eyes_closed"],
            "yawning": result["yawning"],
            "head_drop": result["head_drop"],
            "ear": result["ear"],
            "mar": result["mar"],
            "alertness_score": result["alertness_score"],
            "risk_level": result["risk_level"],
            "landmarks": landmarks,
        }

    def close(self):
        """Release resources"""
        self.face_detector.close()


# Standalone function for direct use
_detector = None


def analyze_driver(frame):
    """
    Unified function - takes frame and returns result.
    Use this function directly.
    
    Example:
        from vision.detector_manager import analyze_driver
        result = analyze_driver(frame)
    """
    global _detector
    if _detector is None:
        _detector = DetectorManager()

    return _detector.analyze_driver(frame)


def reset_detector():
    """Reset detector (e.g. when changing camera)"""
    global _detector
    if _detector:
        _detector.close()
        _detector = None
