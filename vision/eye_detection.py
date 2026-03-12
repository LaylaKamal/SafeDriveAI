"""
Step 5-6: Eye analysis
Calculate EAR (Eye Aspect Ratio) and detect eye closure
"""

import math

try:
    from .landmarks import LEFT_EYE, RIGHT_EYE
except ImportError:
    from landmarks import LEFT_EYE, RIGHT_EYE


EAR_THRESHOLD = 0.21
EYE_CLOSED_FRAMES_THRESHOLD = 3

# Adaptive baseline settings
BASELINE_FRAMES_REQUIRED = 30
BASELINE_MIN_EAR = 0.18
BASELINE_MAX_EAR = 0.5
BASELINE_FACTOR = 0.78


def _distance(p1, p2):
    """Calculate Euclidean distance between two points."""
    if p1 is None or p2 is None:
        return 0.0
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def _get_point(landmarks, index):
    """Extract normalized point coordinates from landmarks."""
    if landmarks is None or index >= len(landmarks):
        return None
    lm = landmarks[index]
    return (lm.x, lm.y)


def _calculate_ear(landmarks, eye_indices):
    """
    Calculate Eye Aspect Ratio for one eye.

    EAR = (|P2-P6| + |P3-P5|) / (2 * |P1-P4|)
    """
    if landmarks is None or len(eye_indices) != 6:
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


def analyze_eyes(landmarks, threshold=EAR_THRESHOLD):
    """
    Analyze eye state from a single frame.

    Args:
        landmarks: landmarks list from Face Mesh
        threshold: EAR threshold for closed-eye detection

    Returns:
        dict:
        {
            "eyes_closed": bool,
            "ear": float,
            "left_ear": float,
            "right_ear": float,
            "ear_threshold": float
        }
    """
    if landmarks is None:
        return {
            "eyes_closed": False,
            "ear": 0.0,
            "left_ear": 0.0,
            "right_ear": 0.0,
            "ear_threshold": round(threshold, 3),
        }

    left_ear = _calculate_ear(landmarks, LEFT_EYE)
    right_ear = _calculate_ear(landmarks, RIGHT_EYE)

    valid_values = [v for v in [left_ear, right_ear] if v > 0]
    ear = sum(valid_values) / len(valid_values) if valid_values else 0.0

    # Do not mark as closed if EAR could not be calculated
    if ear <= 0:
        is_closed = False
    else:
        is_closed = ear < threshold

    return {
        "eyes_closed": is_closed,
        "ear": round(ear, 3),
        "left_ear": round(left_ear, 3),
        "right_ear": round(right_ear, 3),
        "ear_threshold": round(threshold, 3),
    }


class EyeStateTracker:
    """Track eye state across multiple frames with adaptive baseline."""

    def __init__(
        self,
        closed_threshold=EYE_CLOSED_FRAMES_THRESHOLD,
        baseline_frames_required=BASELINE_FRAMES_REQUIRED,
    ):
        self.closed_frames = 0
        self.closed_threshold = closed_threshold

        self.baseline_frames_required = baseline_frames_required
        self.ear_history = []
        self.baseline_ear = None

    def _update_baseline(self, ear):
        """
        Collect EAR values during normal-looking frames to build a personal baseline.
        """
        if ear <= 0:
            return

        if not (BASELINE_MIN_EAR <= ear <= BASELINE_MAX_EAR):
            return

        if self.baseline_ear is None:
            self.ear_history.append(ear)

            if len(self.ear_history) >= self.baseline_frames_required:
                self.baseline_ear = sum(self.ear_history) / len(self.ear_history)

    def _get_dynamic_threshold(self):
        """
        Use personal EAR baseline if available, otherwise fallback to static threshold.
        """
        if self.baseline_ear is None:
            return EAR_THRESHOLD

        dynamic_threshold = self.baseline_ear * BASELINE_FACTOR
        return max(0.16, min(dynamic_threshold, 0.30))

    def reset(self):
        """Reset eye tracker state."""
        self.closed_frames = 0
        self.ear_history = []
        self.baseline_ear = None

    def update(self, landmarks):
        """
        Update tracker and return smoothed eye-closure result.

        Eyes are considered truly closed only after consecutive closed frames.
        """
        threshold = self._get_dynamic_threshold()
        result = analyze_eyes(landmarks, threshold=threshold)

        ear = result["ear"]

        # Update baseline only from likely-open eyes
        if ear > threshold:
            self._update_baseline(ear)

        if result["eyes_closed"]:
            self.closed_frames += 1
            result["eyes_closed"] = self.closed_frames >= self.closed_threshold
        else:
            self.closed_frames = 0

        result["closed_frames"] = self.closed_frames
        result["baseline_ear"] = (
            round(self.baseline_ear, 3) if self.baseline_ear is not None else None
        )

        return result