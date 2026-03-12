"""
Step 7-8: Yawn detection
Calculate MAR (Mouth Aspect Ratio) and detect yawning
"""

import math

try:
    from .landmarks import MOUTH_LEFT, MOUTH_RIGHT, MOUTH_TOP, MOUTH_BOTTOM
except ImportError:
    from landmarks import MOUTH_LEFT, MOUTH_RIGHT, MOUTH_TOP, MOUTH_BOTTOM


MAR_YAWN_THRESHOLD = 0.38

# Optional extra inner lip points
MOUTH_UPPER = 13
MOUTH_LOWER = 14


def _distance(p1, p2):
    """Calculate Euclidean distance between two points."""
    if p1 is None or p2 is None:
        return 0.0
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def _get_point(landmarks, index):
    """Extract point coordinates from landmarks."""
    if landmarks is None or index >= len(landmarks):
        return None
    lm = landmarks[index]
    return (lm.x, lm.y)


def analyze_mouth(landmarks):
    """
    Analyze mouth state and detect yawning.

    MAR = vertical mouth opening / horizontal mouth width

    Args:
        landmarks: landmarks list from Face Mesh

    Returns:
        dict:
        {
            "yawning": bool,
            "mar": float
        }
    """
    if landmarks is None:
        return {
            "yawning": False,
            "mar": 0.0,
        }

    left = _get_point(landmarks, MOUTH_LEFT)
    right = _get_point(landmarks, MOUTH_RIGHT)
    top = _get_point(landmarks, MOUTH_TOP)
    bottom = _get_point(landmarks, MOUTH_BOTTOM)

    upper = _get_point(landmarks, MOUTH_UPPER)
    lower = _get_point(landmarks, MOUTH_LOWER)

    horizontal = _distance(left, right)

    # Use the largest valid vertical opening
    vertical_candidates = [
        _distance(top, bottom),
        _distance(upper, lower),
        _distance(upper, bottom),
    ]
    vertical = max(vertical_candidates)

    if horizontal <= 0:
        return {
            "yawning": False,
            "mar": 0.0,
        }

    mar = vertical / horizontal

    # Require a stronger opening to count as yawn
    yawning = mar > MAR_YAWN_THRESHOLD

    return {
        "yawning": yawning,
        "mar": round(mar, 3),
    }
