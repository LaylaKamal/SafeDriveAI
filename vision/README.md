# Driver Drowsiness Detection - SafeDrive AI

## File Structure

```
vision/
├── camera.py           # Step 2: Camera
├── face_mesh.py        # Step 3-4: Face Mesh + landmarks
├── landmarks.py        # Step 4: Landmark indices for eye/mouth/head
├── eye_detection.py    # Step 5-6: Eye analysis (EAR)
├── yawn_detection.py   # Step 7-8: Yawn detection (MAR)
├── head_pose.py        # Step 9-10: Head tilt
├── fatigue_score.py    # Step 11: Alertness score
├── detector_manager.py # Step 12: Unified API
├── run_detector.py     # Run detector for testing
├── face_landmarker.task # MediaPipe model
├── requirements.txt
├── OUTPUT_SPEC.md      # Output specs
└── README.md
```

## Run

```bash
cd vision
source .venv/bin/activate
pip install -r requirements.txt

# Camera test only
python camera.py

# Face Mesh test
python face_mesh.py

# Full detector
python run_detector.py
```

## Usage

```python
from vision.detector_manager import analyze_driver

result = analyze_driver(frame)
# result: driver_detected, eyes_closed, yawning, head_drop, ear, mar, alertness_score, risk_level
```

See `OUTPUT_SPEC.md` for output details.
