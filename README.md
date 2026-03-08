# SafeDriveAI

SafeDriveAI is an AI-powered driver drowsiness detection system that monitors the driver's face in real time using computer vision and generates smart alerts when fatigue signs are detected.

The system analyzes:

- Eye closure
- Yawning
- Head drop
- Alertness score
- Risk level

It also provides:

- Live monitoring dashboard
- Session logging
- Final trip report
- Smart visual and audio alerts

---

## Project Idea

Driver fatigue and drowsiness are among the leading causes of road accidents, especially during long-distance driving. SafeDriveAI addresses this problem by using AI and computer vision to monitor the driver's state in real time and warn them before the situation becomes dangerous.

---

## Main Features

- Real-time camera feed
- Face and landmark detection using MediaPipe
- Eye closure detection
- Yawn detection
- Head drop detection
- Alertness score calculation
- Risk level classification
- Audio alert system
- Session summary and final report generation

---

## Tech Stack

### Frontend

- HTML
- CSS
- JavaScript

### Backend

- Python
- Flask

### AI / Computer Vision

- OpenCV
- MediaPipe
- NumPy

---

## Project Structure

```bash
SafeDriveAI/
│
├── app.py
├── requirements.txt
├── README.md
│
├── data/
│   ├── sessions.json
│   └── reports/
│
├── templates/
│   ├── index.html
│   └── report.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── app.js
│   ├── sounds/
│   │   ├── alert.wav
│   │   └── warning.wav
│   └── images/
│       └── logo.png
│
└── vision/
    ├── __init__.py
    ├── camera.py
    ├── detector_manager.py
    ├── eye_detection.py
    ├── face_mesh.py
    ├── fatigue_score.py
    ├── head_pose.py
    ├── landmarks.py
    ├── yawn_detection.py
    ├── face_landmarker.task
    ├── OUTPUT_SPEC.md
    └── README.md
```
