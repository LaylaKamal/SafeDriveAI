"""
Step 4: Important landmark indices
Eye, mouth, and head points
"""

# ========== Left Eye (EAR - Eye Aspect Ratio) ==========
# 6 points to calculate eye openness ratio
LEFT_EYE = [362, 385, 387, 263, 373, 380]  # P1-P6 left eye

# ========== Right Eye ==========
RIGHT_EYE = [33, 160, 158, 133, 153, 144]  # P1-P6 right eye

# ========== Mouth (MAR - Mouth Aspect Ratio) ==========
# Horizontal and vertical mouth points
MOUTH_LEFT = 61
MOUTH_RIGHT = 291
MOUTH_TOP = 0
MOUTH_BOTTOM = 17
MOUTH_POINTS = [61, 291, 0, 17]

# ========== Head (Head Pose) ==========
# Nose and eye points for head tilt detection
NOSE_TIP = 1
NOSE_BRIDGE = 168
LEFT_EYE_CENTER = 468   # approximate center
RIGHT_EYE_CENTER = 473  # approximate center
FOREHEAD = 10
CHIN = 152

# Additional points for head tilt estimation
HEAD_POINTS = [1, 168, 10, 152, 33, 263]  # nose, bridge, forehead, chin, eyes
