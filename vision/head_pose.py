"""
Step 9-10: Head tilt analysis
Detect head drop (loss of focus / drowsiness)
"""

import math

try:
    from .landmarks import NOSE_TIP, NOSE_BRIDGE, FOREHEAD, CHIN
except ImportError:
    from landmarks import NOSE_TIP, NOSE_BRIDGE, FOREHEAD, CHIN


def _get_point(landmarks, index):
    """Extract point coordinates from landmarks."""
    if landmarks is None or index >= len(landmarks):
        return None
    lm = landmarks[index]
    return (lm.x, lm.y)


def analyze_head_pose(landmarks):
    """
    Analyze head tilt using a few stable facial reference points.

    Logic:
    - Compare nose position relative to forehead/chin
    - Detect forward head drop
    - Detect strong sideways tilt
    - Return richer information for debugging and scoring

    Args:
        landmarks: landmarks list from Face Mesh

    Returns:
        dict:
        {
            "head_drop": bool,
            "head_status": str,   # "straight" | "down" | "up" | "side"
            "nose_angle": float,
            "lateral_angle": float,
            "nose_position_ratio": float
        }
    """
    if landmarks is None:
        return {
            "head_drop": False,
            "head_status": "unknown",
            "nose_angle": 0.0,
            "lateral_angle": 0.0,
            "nose_position_ratio": 0.0,
        }

    nose_tip = _get_point(landmarks, NOSE_TIP)
    nose_bridge = _get_point(landmarks, NOSE_BRIDGE)
    forehead = _get_point(landmarks, FOREHEAD)
    chin = _get_point(landmarks, CHIN)

    if any(pt is None for pt in [nose_tip, nose_bridge, forehead, chin]):
        return {
            "head_drop": False,
            "head_status": "unknown",
            "nose_angle": 0.0,
            "lateral_angle": 0.0,
            "nose_position_ratio": 0.0,
        }

    face_height = chin[1] - forehead[1]
    if abs(face_height) < 1e-6:
        return {
            "head_drop": False,
            "head_status": "unknown",
            "nose_angle": 0.0,
            "lateral_angle": 0.0,
            "nose_position_ratio": 0.0,
        }

    # Nose vertical position inside the face box
    nose_position_ratio = (nose_tip[1] - forehead[1]) / face_height

    # Nose direction angle
    dx = nose_tip[0] - nose_bridge[0]
    dy = nose_tip[1] - nose_bridge[1]
    nose_angle = math.degrees(math.atan2(dy, dx)) if abs(dx) > 1e-6 else 90.0

    # Side tilt angle based on forehead->chin axis
    face_dx = chin[0] - forehead[0]
    face_dy = chin[1] - forehead[1]
    lateral_angle = (
        math.degrees(math.atan2(abs(face_dx), face_dy))
        if abs(face_dy) > 1e-6
        else 0.0
    )

    # Thresholds tuned to reduce false positives
    forward_tilt = nose_position_ratio > 0.60
    side_tilt = lateral_angle > 18

    head_drop = forward_tilt or side_tilt

    if forward_tilt:
        head_status = "down"
    elif side_tilt:
        head_status = "side"
    elif nose_position_ratio < 0.38:
        head_status = "up"
    else:
        head_status = "straight"

    return {
        "head_drop": head_drop,
        "head_status": head_status,
        "nose_angle": round(nose_angle, 1),
        "lateral_angle": round(lateral_angle, 1),
        "nose_position_ratio": round(nose_position_ratio, 3),
    }
