"""
Step 9-10: Head tilt analysis
Detect head drop (loss of focus / drowsiness)
"""
import math
try:
    from .landmarks import NOSE_TIP, NOSE_BRIDGE, FOREHEAD, CHIN, HEAD_POINTS
except ImportError:
    from landmarks import NOSE_TIP, NOSE_BRIDGE, FOREHEAD, CHIN, HEAD_POINTS


def _get_point(landmarks, index):
    """Extract point coordinates from landmarks"""
    if landmarks is None or index >= len(landmarks):
        return None
    lm = landmarks[index]
    return (lm.x, lm.y)


def analyze_head_pose(landmarks):
    """
    Analyze head tilt.
    Uses y ratio for nose, forehead, chin:
    - Chin (y) higher than usual + nose tilted = head dropped
    - y in OpenCV/MediaPipe: higher = lower in image
    
    Args:
        landmarks: landmarks list from Face Mesh
        
    Returns:
        dict: {
            "head_drop": bool,
            "head_status": str  # "straight" | "down" | "up"
        }
    """
    if landmarks is None:
        return {"head_drop": False, "head_status": "unknown"}

    nose_tip = _get_point(landmarks, NOSE_TIP)
    nose_bridge = _get_point(landmarks, NOSE_BRIDGE)
    forehead = _get_point(landmarks, FOREHEAD)
    chin = _get_point(landmarks, CHIN)

    if any(pt is None for pt in [nose_tip, nose_bridge, forehead, chin]):
        return {"head_drop": False, "head_status": "unknown"}

    # Vertical distance between forehead and chin
    face_height = chin[1] - forehead[1]

    # Nose position relative to face height (0 to 1 ratio)
    # Normal: nose roughly in middle
    nose_position = (nose_tip[1] - forehead[1]) / face_height if face_height != 0 else 0.5

    # Nose tilt angle (from bridge to tip) - increases when head tilts down
    nose_angle = 0
    if nose_bridge and nose_tip:
        dx = nose_tip[0] - nose_bridge[0]
        dy = nose_tip[1] - nose_bridge[1]
        if dx != 0:
            nose_angle = math.degrees(math.atan2(dy, dx))

    # Lateral head tilt: angle of forehead-to-chin line (sideways tilt)
    face_dx = chin[0] - forehead[0]
    face_dy = chin[1] - forehead[1]
    lateral_angle = 0
    if face_dy != 0:
        lateral_angle = math.degrees(math.atan2(abs(face_dx), face_dy))

    # Head dropped: only on CLEAR tilt (avoid false alarm when straight)
    # Forward: nose_position > 0.55 (head nodding down)
    # Lateral: lateral_angle > 22 (head tilted sideways)
    forward_tilt = nose_position > 0.55
    lateral_tilt = lateral_angle > 22
    head_drop = forward_tilt or lateral_tilt

    if head_drop:
        head_status = "down"
    elif nose_position < 0.4:
        head_status = "up"
    else:
        head_status = "straight"

    return {
        "head_drop": head_drop,
        "head_status": head_status,
        "nose_angle": round(nose_angle, 1),
    }
