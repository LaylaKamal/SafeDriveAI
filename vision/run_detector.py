"""
Driver Drowsiness Detection - SafeDrive AI
Camera detects if driver is sleepy or alert. Clear English feedback on screen.
Face mesh: RED = danger, GREEN = safe
"""
import cv2
import sys
import os

# Allow import from vision folder when running directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from camera import open_camera, read_frame, release_camera
from detector_manager import analyze_driver
from landmarks import LEFT_EYE, RIGHT_EYE, MOUTH_LEFT, MOUTH_RIGHT, MOUTH_TOP, MOUTH_BOTTOM, NOSE_TIP, NOSE_BRIDGE, FOREHEAD, CHIN

# Colors BGR: Red = danger, Green = safe
RED = (0, 0, 255)
GREEN = (0, 255, 0)


def _point(frame, landmarks, index, color, radius=4):
    """Draw landmark point on frame"""
    if landmarks is None or index >= len(landmarks):
        return
    h, w = frame.shape[:2]
    lm = landmarks[index]
    x, y = int(lm.x * w), int(lm.y * h)
    cv2.circle(frame, (x, y), radius, color, -1)


def _draw_face_mesh(frame, landmarks, result):
    """Draw face mesh: RED = danger zone, GREEN = safe zone"""
    if landmarks is None or not result.get("driver_detected"):
        return

    eye_color = RED if result.get("eyes_closed") else GREEN
    mouth_color = RED if result.get("yawning") else GREEN
    head_color = RED if result.get("head_drop") else GREEN

    # Eyes - left and right
    for idx in LEFT_EYE + RIGHT_EYE:
        _point(frame, landmarks, idx, eye_color, 3)

    # Mouth
    for idx in [MOUTH_LEFT, MOUTH_RIGHT, MOUTH_TOP, MOUTH_BOTTOM, 13, 14]:
        _point(frame, landmarks, idx, mouth_color, 3)

    # Head - nose, forehead, chin
    for idx in [NOSE_TIP, NOSE_BRIDGE, FOREHEAD, CHIN]:
        _point(frame, landmarks, idx, head_color, 4)

    # Draw mesh lines between key points
    h, w = frame.shape[:2]
    def line_between(indices, color):
        pts = [(int(landmarks[i].x * w), int(landmarks[i].y * h))
               for i in indices if i < len(landmarks)]
        for i in range(len(pts) - 1):
            cv2.line(frame, pts[i], pts[i + 1], color, 1)
    line_between(LEFT_EYE + [LEFT_EYE[0]], eye_color)
    line_between(RIGHT_EYE + [RIGHT_EYE[0]], eye_color)
    line_between([MOUTH_LEFT, MOUTH_RIGHT, MOUTH_LEFT], mouth_color)
    line_between([FOREHEAD, NOSE_TIP, CHIN, FOREHEAD], head_color)


def main():
    cap = open_camera(0)
    if not cap.isOpened():
        print("Error: Cannot open camera")
        return

    print("SafeDrive AI - Driver Drowsiness Detection")
    print("Press ESC to exit")

    while True:
        success, frame = read_frame(cap)
        if not success:
            continue
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        result = analyze_driver(frame)

        # Status bar: RED = danger, GREEN = safe
        # Eyes closed / Yawning / Head tilted = RED
        # Eyes open + Mouth closed + Head straight = GREEN
        if not result["driver_detected"]:
            status_text = "Look at camera"
            status_color = (128, 128, 128)  # Gray
            bg_color = (60, 60, 60)
        elif result["risk_level"] == "low":
            # All safe: eyes open, mouth closed, head straight
            status_text = "ALL CLEAR - Safe"
            status_color = (0, 255, 0)  # Green
            bg_color = (0, 100, 0)
        else:
            # Danger: show which indicator
            status_color = (0, 0, 255)  # Red
            bg_color = (0, 0, 100)
            if result.get("eyes_closed"):
                status_text = "DANGER - Eyes closed!"
            elif result.get("yawning"):
                status_text = "DANGER - Yawning!"
            elif result.get("head_drop"):
                status_text = "DANGER - Head tilted!"
            else:
                status_text = "DANGER - Stay alert!"

        # Large status bar at top
        bar_height = 80
        cv2.rectangle(frame, (0, 0), (w, bar_height), bg_color, -1)
        cv2.rectangle(frame, (0, 0), (w, bar_height), status_color, 3)

        # Main status text - big and clear
        font_scale = 1.2
        thickness = 3
        (tw, th), _ = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        x = (w - tw) // 2
        y = 55
        cv2.putText(
            frame, status_text, (x, y),
            cv2.FONT_HERSHEY_SIMPLEX, font_scale, status_color, thickness
        )

        # Extra warning when drowsy
        if result["risk_level"] in ("medium", "high") and result["driver_detected"]:
            warning = "STAY ALERT!"
            cv2.putText(frame, warning, ((w - 150) // 2, bar_height + 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

        # Face mesh: RED = danger, GREEN = safe
        _draw_face_mesh(frame, result.get("landmarks"), result)

        cv2.imshow("SafeDrive AI - Driver Drowsiness Detection", frame)
        if cv2.waitKey(5) & 0xFF == 27:
            break

    release_camera(cap)


if __name__ == "__main__":
    main()
