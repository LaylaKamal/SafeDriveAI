# Output Specification

## Main Function

```python
from vision.detector_manager import analyze_driver

result = analyze_driver(frame)
```

- **frame**: BGR image from `cv2.VideoCapture.read()` or Flask/camera feed
- **result**: Dictionary with the following shape

---

## Return Data Shape

```python
{
    "driver_detected": True,   # Face detected
    "eyes_closed": False,      # Eyes closed (multiple consecutive frames)
    "yawning": False,          # Yawning detected
    "head_drop": False,        # Head lowered
    "ear": 0.28,               # Eye Aspect Ratio (0.0 - 1.0)
    "mar": 0.35,               # Mouth Aspect Ratio
    "alertness_score": 80,     # Alertness score (0 - 100)
    "risk_level": "low"        # "low" | "medium" | "high"
}
```

---

## When No Face Detected

```python
{
    "driver_detected": False,
    "eyes_closed": False,
    "yawning": False,
    "head_drop": False,
    "ear": 0.0,
    "mar": 0.0,
    "alertness_score": 0,
    "risk_level": "unknown"
}
```

---

## Risk Levels (risk_level)

| risk_level | alertness_score | Meaning    |
|------------|-----------------|------------|
| low        | 70 - 100        | Normal     |
| medium     | 45 - 69         | Warning    |
| high       | 0 - 44          | Danger     |

---

## Flask Usage Example

```python
from flask import Flask, Response
import cv2
from vision.detector_manager import analyze_driver

app = Flask(__name__)
cap = cv2.VideoCapture(0)

@app.route('/analyze')
def analyze():
    ret, frame = cap.read()
    if not ret:
        return {"error": "no frame"}
    result = analyze_driver(frame)
    return result
```
