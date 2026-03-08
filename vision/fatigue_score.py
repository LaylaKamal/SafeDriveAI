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

# Base score
BASE_SCORE = 100

# Penalty per indicator
PENALTY_EYES_CLOSED = 40
PENALTY_YAWNING = 20
PENALTY_HEAD_DROP = 50   # Head tilt alone should trigger danger


def calculate_alertness_score(eyes_result, mouth_result, head_result):
    """
    Calculate alertness score from analysis results
    
    Args:
        eyes_result: from eye_detection.analyze_eyes
        mouth_result: from yawn_detection.analyze_mouth
        head_result: from head_pose.analyze_head_pose
        
    Returns:
        dict: {
            "alertness_score": int (0-100),
            "risk_level": str ("low" | "medium" | "high")
        }
    """
    score = BASE_SCORE

    if eyes_result.get("eyes_closed"):
        score -= PENALTY_EYES_CLOSED

    if mouth_result.get("yawning"):
        score -= PENALTY_YAWNING

    if head_result.get("head_drop"):
        score -= PENALTY_HEAD_DROP

    # Clamp score between 0 and 100
    score = max(0, min(100, score))

    # Risk level
    if score >= 70:
        risk_level = "low"
    elif score >= 45:
        risk_level = "medium"
    else:
        risk_level = "high"

    return {
        "alertness_score": score,
        "risk_level": risk_level,
    }


def get_combined_result(landmarks, eye_tracker=None):
    """
    Unified function that analyzes landmarks and returns full result
    
    Args:
        landmarks: from face_mesh
        eye_tracker: EyeStateTracker (optional - for tracking across frames)
        
    Returns:
        Full result dict
    """
    if eye_tracker:
        eyes_result = eye_tracker.update(landmarks)
    else:
        eyes_result = analyze_eyes(landmarks)

    mouth_result = analyze_mouth(landmarks)
    head_result = analyze_head_pose(landmarks)

    score_result = calculate_alertness_score(
        eyes_result, mouth_result, head_result
    )

    return {
        **eyes_result,
        **mouth_result,
        **head_result,
        **score_result,
    }
