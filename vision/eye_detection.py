"""
Step 5-6: Eye analysis
Calculate EAR (Eye Aspect Ratio) and detect eye closure
"""
import math
try:
    from .landmarks import LEFT_EYE, RIGHT_EYE
except ImportError:
    from landmarks import LEFT_EYE, RIGHT_EYE

# EAR threshold - below this eye is considered closed
EAR_THRESHOLD = 0.21

# Consecutive frames with eyes closed to consider drowsy
EYE_CLOSED_FRAMES_THRESHOLD = 3


def _distance(p1, p2):
    """Calculate distance between two points"""
    if p1 is None or p2 is None:
        return 0
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def _get_point(landmarks, index):
    """Extract point coordinates from landmarks"""
    if landmarks is None or index >= len(landmarks):
        return None
    lm = landmarks[index]
    return (lm.x, lm.y)


def _calculate_ear(landmarks, eye_indices):
    """
    Calculate Eye Aspect Ratio for one eye
    EAR = (|P2-P6| + |P3-P5|) / (2 * |P1-P4|)
    """
    if len(eye_indices) != 6:
        return 0.0

    p1 = _get_point(landmarks, eye_indices[0])
    p2 = _get_point(landmarks, eye_indices[1])
    p3 = _get_point(landmarks, eye_indices[2])
    p4 = _get_point(landmarks, eye_indices[3])
    p5 = _get_point(landmarks, eye_indices[4])
    p6 = _get_point(landmarks, eye_indices[5])

    if any(pt is None for pt in [p1, p2, p3, p4, p5, p6]):
        return 0.0

    vertical1 = _distance(p2, p6)
    vertical2 = _distance(p3, p5)
    horizontal = _distance(p1, p4)

    if horizontal == 0:
        return 0.0

    ear = (vertical1 + vertical2) / (2.0 * horizontal)
    return ear


def analyze_eyes(landmarks, closed_frames_counter=0):
    """
    Analyze eye state
    
    Args:
        landmarks: landmarks list from Face Mesh
        closed_frames_counter: closed frames counter (passed externally for tracking)
        
    Returns:
        dict: {
            "eyes_closed": bool,
            "ear": float,
            "left_ear": float,
            "right_ear": float
        }
    """
    if landmarks is None:
        return {
            "eyes_closed": False,
            "ear": 0.0,
            "left_ear": 0.0,
            "right_ear": 0.0,
        }

    left_ear = _calculate_ear(landmarks, LEFT_EYE)
    right_ear = _calculate_ear(landmarks, RIGHT_EYE)

    # Average of both eyes
    ear = (left_ear + right_ear) / 2.0 if (left_ear > 0 and right_ear > 0) else 0.0

    # Eye closed if EAR below threshold
    is_closed = ear < EAR_THRESHOLD if ear > 0 else True

    return {
        "eyes_closed": is_closed,
        "ear": round(ear, 3),
        "left_ear": round(left_ear, 3),
        "right_ear": round(right_ear, 3),
    }


class EyeStateTracker:
    """Track eye state across multiple frames"""

    def __init__(self, closed_threshold=EYE_CLOSED_FRAMES_THRESHOLD):
        self.closed_frames = 0
        self.closed_threshold = closed_threshold

    def update(self, landmarks):
        """
        Update state and return result.
        eyes_closed = True only if eye closed for multiple consecutive frames.
        """
        result = analyze_eyes(landmarks)

        if result["eyes_closed"]:
            self.closed_frames += 1
            result["eyes_closed"] = self.closed_frames >= self.closed_threshold
        else:
            self.closed_frames = 0

        return result
