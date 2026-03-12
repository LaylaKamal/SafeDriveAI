"""
Step 11: Alertness / fatigue score
Combine eye, yawn, and head results
"""

try:
    from .eye_detection import analyze_eyes, EyeStateTracker
    from .yawn_detection import analyze_mouth
    from .head_pose import analyze_head_pose
except ImportError:
    from eye_detection import analyze_eyes, EyeStateTracker
    from yawn_detection import analyze_mouth
    from head_pose import analyze_head_pose


BASE_SCORE = 100

# Penalties
PENALTY_EYES_CLOSED = 35
PENALTY_YAWNING = 15
PENALTY_HEAD_DROP = 25

# Extra penalties for combined fatigue signals
COMBO_PENALTY_EYES_AND_HEAD = 15
COMBO_PENALTY_EYES_AND_YAWN = 10
COMBO_PENALTY_HEAD_AND_YAWN = 10
COMBO_PENALTY_ALL = 15


def calculate_alertness_score(eyes_result, mouth_result, head_result):
    """
    Calculate alertness score from analysis results

    Args:
        eyes_result: dict from eye_detection
        mouth_result: dict from yawn_detection
        head_result: dict from head_pose

    Returns:
        dict:
        {
            "alertness_score": int,
            "risk_level": str
        }
    """
    score = BASE_SCORE

    eyes_closed = bool(eyes_result.get("eyes_closed", False))
    yawning = bool(mouth_result.get("yawning", False))
    head_drop = bool(head_result.get("head_drop", False))

    if eyes_closed:
        score -= PENALTY_EYES_CLOSED

    if yawning:
        score -= PENALTY_YAWNING

    if head_drop:
        score -= PENALTY_HEAD_DROP

    # Multi-signal fatigue penalties
    if eyes_closed and head_drop:
        score -= COMBO_PENALTY_EYES_AND_HEAD

    if eyes_closed and yawning:
        score -= COMBO_PENALTY_EYES_AND_YAWN

    if head_drop and yawning:
        score -= COMBO_PENALTY_HEAD_AND_YAWN

    if eyes_closed and yawning and head_drop:
        score -= COMBO_PENALTY_ALL

    score = max(0, min(100, score))

    if score >= 80:
        risk_level = "Safe"
    elif score >= 60:
        risk_level = "Low"
    elif score >= 40:
        risk_level = "Medium"
    else:
        risk_level = "High"

    return {
        "alertness_score": score,
        "risk_level": risk_level,
    }


def get_combined_result(landmarks, eye_tracker=None):
    """
    Unified function that analyzes landmarks and returns full result

    Args:
        landmarks: list of face landmarks from face_mesh
        eye_tracker: EyeStateTracker instance (optional)

    Returns:
        dict with combined results
    """
    if landmarks is None:
        return {
            "eyes_closed": False,
            "ear": 0.0,
            "left_ear": 0.0,
            "right_ear": 0.0,
            "yawning": False,
            "mar": 0.0,
            "head_drop": False,
            "alertness_score": 0,
            "risk_level": "Unknown",
        }

    if eye_tracker:
        eyes_result = eye_tracker.update(landmarks)
    else:
        eyes_result = analyze_eyes(landmarks)

    mouth_result = analyze_mouth(landmarks)
    head_result = analyze_head_pose(landmarks)

    score_result = calculate_alertness_score(
        eyes_result=eyes_result,
        mouth_result=mouth_result,
        head_result=head_result,
    )

    return {
        **eyes_result,
        **mouth_result,
        **head_result,
        **score_result,
    }
