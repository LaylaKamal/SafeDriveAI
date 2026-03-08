"""
Step 7-8: Yawn detection
Calculate MAR (Mouth Aspect Ratio) and detect yawning
"""
import math
try:
    from .landmarks import MOUTH_LEFT, MOUTH_RIGHT, MOUTH_TOP, MOUTH_BOTTOM
except ImportError:
    from landmarks import MOUTH_LEFT, MOUTH_RIGHT, MOUTH_TOP, MOUTH_BOTTOM

# MAR threshold - above this is considered yawning
# Lowered from 0.55 to 0.38 for better yawn detection
MAR_YAWN_THRESHOLD = 0.38

# Mouth points - upper lip and lower lip (or jaw)
MOUTH_UPPER = 13   # upper lip
MOUTH_LOWER = 14   # lower lip


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


def analyze_mouth(landmarks):
    """
    Analyze mouth state and detect yawning.
    MAR = vertical distance / horizontal distance
    Large mouth opening = high MAR = yawning
    
    Args:
        landmarks: landmarks list from Face Mesh
        
    Returns:
        dict: {
            "yawning": bool,
            "mar": float
        }
    """
    if landmarks is None:
        return {"yawning": False, "mar": 0.0}

    # Horizontal distance (between mouth corners)
    left = _get_point(landmarks, MOUTH_LEFT)
    right = _get_point(landmarks, MOUTH_RIGHT)
    horizontal = _distance(left, right)

    # Vertical distance - use upper lip (13) and lower lip (14)
    # Also try chin (17) for larger mouth opening during yawn
    upper = _get_point(landmarks, MOUTH_UPPER)
    lower = _get_point(landmarks, MOUTH_LOWER)
    chin = _get_point(landmarks, MOUTH_BOTTOM)
    vertical1 = _distance(upper, lower)
    vertical2 = _distance(upper, chin) if chin else 0
    vertical = max(vertical1, vertical2)  # Use larger opening

    if horizontal == 0:
        return {"yawning": False, "mar": 0.0}

    mar = vertical / horizontal

    # Yawning = large mouth opening
    yawning = mar > MAR_YAWN_THRESHOLD

    return {
        "yawning": yawning,
        "mar": round(mar, 3),
    }
