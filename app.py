import os
import cv2
import json
import time
import uuid
from copy import deepcopy
from datetime import datetime
from threading import Lock

from flask import Flask, render_template, Response, jsonify, request

# =========================================================
# Import Vision Module
# =========================================================
try:
    from vision.detector_manager import analyze_driver
except ImportError:
    from detector_manager import analyze_driver


# =========================================================
# Flask App Config
# =========================================================
app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")
SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

CAMERA_INDEX = 0
EVENT_COOLDOWN_SECONDS = 2.0

# =========================================================
# Global Runtime State
# =========================================================
state_lock = Lock()

camera = None
session_active = False
current_session = None

latest_status = {
    "driver_detected": False,
    "eyes_closed": False,
    "yawning": False,
    "head_drop": False,
    "alertness_score": 100,
    "risk_level": "Safe",
    "message": "System ready",
    "timestamp": None,
}

last_event_times = {
    "eyes_closed": 0.0,
    "yawning": 0.0,
    "head_drop": 0.0,
    "medium_alert": 0.0,
    "high_alert": 0.0,
}


# =========================================================
# Helpers
# =========================================================
def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_sessions_file() -> None:
    if not os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)


def load_sessions() -> list:
    ensure_sessions_file()
    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_sessions(sessions: list) -> None:
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, indent=2, ensure_ascii=False)


def get_camera():
    global camera
    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(CAMERA_INDEX)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)
    return camera


def release_camera():
    global camera
    if camera is not None and camera.isOpened():
        camera.release()
    camera = None


def safe_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return bool(value)


def safe_number(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_analysis_result(result: dict) -> dict:
    if not isinstance(result, dict):
        result = {}

    driver_detected = safe_bool(
        result.get("driver_detected", result.get("face_detected", False))
    )
    eyes_closed = safe_bool(
        result.get("eyes_closed", result.get("eye_closed", False))
    )
    yawning = safe_bool(
        result.get("yawning", result.get("yawn_detected", False))
    )
    head_drop = safe_bool(
        result.get("head_drop", result.get("head_dropped", False))
    )

    score = result.get("alertness_score", result.get("fatigue_score", 100))
    score = int(max(0, min(100, safe_number(score, 100))))

    risk_level, message = classify_risk(score, driver_detected, eyes_closed, yawning, head_drop)

    normalized = {
        "driver_detected": driver_detected,
        "eyes_closed": eyes_closed,
        "yawning": yawning,
        "head_drop": head_drop,
        "alertness_score": score,
        "risk_level": risk_level,
        "message": message,
        "timestamp": now_iso(),
    }

    if "ear" in result:
        normalized["ear"] = result["ear"]
    if "mar" in result:
        normalized["mar"] = result["mar"]

    return normalized


def classify_risk(score: int, driver_detected: bool, eyes_closed: bool, yawning: bool, head_drop: bool):
    if not driver_detected:
        return "No Driver", "No face detected"

    if head_drop and eyes_closed:
        return "High", "Danger! Stop in a safe place immediately"

    if score >= 80:
        return "Safe", "Driver is alert"
    elif score >= 60:
        return "Low", "Mild fatigue detected"
    elif score >= 40:
        return "Medium", "Please focus and take a break soon"
    else:
        return "High", "Danger! Stop in a safe place immediately"


def create_session() -> dict:
    return {
        "session_id": str(uuid.uuid4())[:8],
        "start_time": now_iso(),
        "end_time": None,
        "duration_seconds": 0,
        "total_frames_analyzed": 0,
        "eye_closure_count": 0,
        "yawn_count": 0,
        "head_drop_count": 0,
        "alerts_triggered": 0,
        "medium_alert_count": 0,
        "high_alert_count": 0,
        "max_risk_level": "Safe",
        "average_alertness_score": 100.0,
        "score_sum": 0.0,
        "event_log": [],
        "last_status": None,

        # Voice assistant fields
        "voice_assistant_trigger_count": 0,
        "voice_response_success_count": 0,
        "voice_response_failure_count": 0,
        "voice_last_question": None,
        "voice_last_transcript": None,
        "voice_last_response_status": "Not checked",
        "voice_interactions": [],
    }


def risk_rank(level: str) -> int:
    order = {
        "No Driver": 0,
        "Safe": 1,
        "Low": 2,
        "Medium": 3,
        "High": 4,
    }
    return order.get(level, 0)


def log_event(event_type: str, message: str, extra: dict | None = None):
    global current_session
    if not session_active or current_session is None:
        return

    entry = {
        "time": now_iso(),
        "type": event_type,
        "message": message,
    }

    if extra and isinstance(extra, dict):
        entry["data"] = extra

    current_session["event_log"].append(entry)


def update_session_metrics(status: dict):
    global current_session, last_event_times

    if not session_active or current_session is None:
        return

    current_session["total_frames_analyzed"] += 1
    current_session["score_sum"] += status["alertness_score"]
    current_session["average_alertness_score"] = round(
        current_session["score_sum"] / max(1, current_session["total_frames_analyzed"]), 2
    )
    current_session["last_status"] = deepcopy(status)

    if risk_rank(status["risk_level"]) > risk_rank(current_session["max_risk_level"]):
        current_session["max_risk_level"] = status["risk_level"]

    current_ts = time.time()

    if status["eyes_closed"] and current_ts - last_event_times["eyes_closed"] >= EVENT_COOLDOWN_SECONDS:
        current_session["eye_closure_count"] += 1
        last_event_times["eyes_closed"] = current_ts
        log_event("eyes_closed", "Eyes closed detected", {"score": status["alertness_score"]})

    if status["yawning"] and current_ts - last_event_times["yawning"] >= EVENT_COOLDOWN_SECONDS:
        current_session["yawn_count"] += 1
        last_event_times["yawning"] = current_ts
        log_event("yawning", "Yawning detected", {"score": status["alertness_score"]})

    if status["head_drop"] and current_ts - last_event_times["head_drop"] >= EVENT_COOLDOWN_SECONDS:
        current_session["head_drop_count"] += 1
        last_event_times["head_drop"] = current_ts
        log_event("head_drop", "Head drop detected", {"score": status["alertness_score"]})

    if status["risk_level"] == "Medium":
        if current_ts - last_event_times["medium_alert"] >= EVENT_COOLDOWN_SECONDS:
            current_session["alerts_triggered"] += 1
            current_session["medium_alert_count"] += 1
            last_event_times["medium_alert"] = current_ts
            log_event("medium_alert", "Medium risk alert triggered", {"score": status["alertness_score"]})

    elif status["risk_level"] == "High":
        if current_ts - last_event_times["high_alert"] >= EVENT_COOLDOWN_SECONDS:
            current_session["alerts_triggered"] += 1
            current_session["high_alert_count"] += 1
            last_event_times["high_alert"] = current_ts
            log_event("high_alert", "High risk alert triggered", {"score": status["alertness_score"]})


def finalize_session(session: dict) -> dict:
    session["end_time"] = now_iso()

    start_dt = datetime.fromisoformat(session["start_time"])
    end_dt = datetime.fromisoformat(session["end_time"])
    session["duration_seconds"] = int((end_dt - start_dt).total_seconds())

    session.pop("score_sum", None)
    session["recommendation"] = generate_recommendation(session)
    return session


def generate_recommendation(session: dict) -> str:
    max_risk = session.get("max_risk_level", "Safe")
    avg_score = session.get("average_alertness_score", 100)
    yawns = session.get("yawn_count", 0)
    eyes = session.get("eye_closure_count", 0)
    head = session.get("head_drop_count", 0)
    voice_failures = session.get("voice_response_failure_count", 0)

    if max_risk == "High" or avg_score < 40 or voice_failures >= 2:
        return "High fatigue risk detected. The driver should stop in a safe place and rest before continuing."
    if max_risk == "Medium" or yawns >= 3 or eyes >= 3:
        return "Moderate fatigue signs detected. A short break, water, and fresh air are recommended."
    if head > 0:
        return "Head-drop behavior was detected. The driver should maintain focus and consider resting soon."
    return "Driver state was generally stable. Continue safe driving habits and take regular breaks on long trips."


def save_report_file(session: dict) -> str:
    report_path = os.path.join(REPORTS_DIR, f"report_{session['session_id']}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2, ensure_ascii=False)
    return report_path


def register_voice_event(payload: dict):
    global current_session

    if not session_active or current_session is None:
        return False, "No active session found"

    event_type = str(payload.get("event_type", "voice_event")).strip() or "voice_event"
    question = payload.get("question")
    transcript = payload.get("transcript")
    responded = safe_bool(payload.get("responded", False))
    response_status = payload.get("response_status")
    reason = payload.get("reason")
    risk_level = payload.get("risk_level")

    interaction = {
        "time": now_iso(),
        "event_type": event_type,
        "question": question,
        "transcript": transcript,
        "responded": responded,
        "response_status": response_status,
        "reason": reason,
        "risk_level": risk_level,
    }

    current_session["voice_interactions"].append(interaction)

    if event_type == "assistant_triggered":
        current_session["voice_assistant_trigger_count"] += 1
        if question:
            current_session["voice_last_question"] = question

        log_event(
            "voice_assistant_triggered",
            "Voice assistant triggered",
            {
                "question": question,
                "reason": reason,
                "risk_level": risk_level,
            }
        )

    elif event_type == "driver_response":
        current_session["voice_last_question"] = question
        current_session["voice_last_transcript"] = transcript
        current_session["voice_last_response_status"] = response_status or (
            "Driver response detected" if responded else "No response detected"
        )

        if responded:
            current_session["voice_response_success_count"] += 1
            log_event(
                "voice_response_success",
                "Driver responded to voice assistant",
                {
                    "question": question,
                    "transcript": transcript,
                    "risk_level": risk_level,
                }
            )
        else:
            current_session["voice_response_failure_count"] += 1
            log_event(
                "voice_response_failure",
                "No valid driver response detected",
                {
                    "question": question,
                    "transcript": transcript,
                    "risk_level": risk_level,
                }
            )

    else:
        log_event(
            "voice_event",
            "Voice assistant event recorded",
            {
                "event_type": event_type,
                "question": question,
                "transcript": transcript,
                "responded": responded,
                "response_status": response_status,
                "reason": reason,
                "risk_level": risk_level,
            }
        )

    return True, "Voice event saved successfully"


# =========================================================
# Video Processing
# =========================================================
def process_frame(frame):
    global latest_status

    try:
        raw_result = analyze_driver(frame)
        status = normalize_analysis_result(raw_result)
    except Exception as e:
        status = {
            "driver_detected": False,
            "eyes_closed": False,
            "yawning": False,
            "head_drop": False,
            "alertness_score": 0,
            "risk_level": "Error",
            "message": f"Vision error: {str(e)}",
            "timestamp": now_iso(),
        }

    with state_lock:
        latest_status = status
        update_session_metrics(status)

    annotated = draw_overlay(frame.copy(), status)
    return annotated


def draw_overlay(frame, status: dict):
    h, w = frame.shape[:2]

    risk = status.get("risk_level", "Safe")
    score = status.get("alertness_score", 100)

    color = (0, 255, 0)
    if risk == "Low":
        color = (0, 255, 255)
    elif risk == "Medium":
        color = (0, 165, 255)
    elif risk == "High":
        color = (0, 0, 255)
    elif risk in ("No Driver", "Error"):
        color = (180, 180, 180)

    cv2.rectangle(frame, (10, 10), (w - 10, 110), (20, 20, 20), -1)
    cv2.rectangle(frame, (10, 10), (w - 10, 110), color, 2)

    cv2.putText(frame, f"Risk: {risk}", (25, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.putText(frame, f"Score: {score}", (25, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    msg = status.get("message", "")
    cv2.putText(frame, msg[:60], (250, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

    flags = [
        f"Driver: {'Yes' if status.get('driver_detected') else 'No'}",
        f"Eyes Closed: {'Yes' if status.get('eyes_closed') else 'No'}",
        f"Yawning: {'Yes' if status.get('yawning') else 'No'}",
        f"Head Drop: {'Yes' if status.get('head_drop') else 'No'}",
    ]

    y = 140
    for item in flags:
        cv2.putText(frame, item, (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        y += 30

    return frame


def generate_frames():
    cap = get_camera()

    while True:
        success, frame = cap.read()
        if not success:
            break

        processed_frame = process_frame(frame)

        ret, buffer = cv2.imencode(".jpg", processed_frame)
        if not ret:
            continue

        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )


# =========================================================
# Routes - Pages
# =========================================================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/report/<session_id>")
def report_page(session_id):
    report_path = os.path.join(REPORTS_DIR, f"report_{session_id}.json")
    if not os.path.exists(report_path):
        return jsonify({"error": "Report not found"}), 404

    with open(report_path, "r", encoding="utf-8") as f:
        report_data = json.load(f)

    return render_template("report.html", report=report_data)


# =========================================================
# Routes - Video
# =========================================================
@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


# =========================================================
# Routes - API
# =========================================================
@app.route("/api/status", methods=["GET"])
def api_status():
    with state_lock:
        return jsonify(latest_status)


@app.route("/api/start-session", methods=["POST"])
def api_start_session():
    global session_active, current_session, last_event_times

    with state_lock:
        if session_active:
            return jsonify({
                "success": False,
                "message": "A session is already running",
                "session_id": current_session["session_id"] if current_session else None
            }), 400

        current_session = create_session()
        session_active = True

        last_event_times = {
            "eyes_closed": 0.0,
            "yawning": 0.0,
            "head_drop": 0.0,
            "medium_alert": 0.0,
            "high_alert": 0.0,
        }

        log_event("session_start", "Monitoring session started")

        return jsonify({
            "success": True,
            "message": "Session started successfully",
            "session_id": current_session["session_id"],
            "start_time": current_session["start_time"]
        })


@app.route("/api/end-session", methods=["POST"])
def api_end_session():
    global session_active, current_session

    with state_lock:
        if not session_active or current_session is None:
            return jsonify({
                "success": False,
                "message": "No active session found"
            }), 400

        log_event("session_end", "Monitoring session ended")
        finished_session = finalize_session(current_session)

        sessions = load_sessions()
        sessions.append(finished_session)
        save_sessions(sessions)

        save_report_file(finished_session)

        session_active = False
        report_data = deepcopy(finished_session)
        current_session = None

    return jsonify({
        "success": True,
        "message": "Session ended successfully",
        "report": report_data,
        "report_url": f"/report/{report_data['session_id']}"
    })


@app.route("/api/current-session", methods=["GET"])
def api_current_session():
    with state_lock:
        if not session_active or current_session is None:
            return jsonify({
                "active": False,
                "session": None
            })

        preview = deepcopy(current_session)
        preview.pop("score_sum", None)

        return jsonify({
            "active": True,
            "session": preview
        })


@app.route("/api/reports", methods=["GET"])
def api_reports():
    sessions = load_sessions()
    sessions = sorted(sessions, key=lambda x: x.get("start_time", ""), reverse=True)
    return jsonify({
        "count": len(sessions),
        "reports": sessions
    })


@app.route("/api/report/<session_id>", methods=["GET"])
def api_report(session_id):
    report_path = os.path.join(REPORTS_DIR, f"report_{session_id}.json")
    if not os.path.exists(report_path):
        return jsonify({"success": False, "message": "Report not found"}), 404

    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    return jsonify({
        "success": True,
        "report": report
    })


@app.route("/api/voice-event", methods=["POST"])
def api_voice_event():
    global current_session

    payload = request.get_json(silent=True) or {}

    with state_lock:
        ok, message = register_voice_event(payload)

        if not ok:
            return jsonify({
                "success": False,
                "message": message
            }), 400

        preview = deepcopy(current_session)
        if preview:
            preview.pop("score_sum", None)

        return jsonify({
            "success": True,
            "message": message,
            "session": preview
        })


@app.route("/api/health", methods=["GET"])
def api_health():
    cap = get_camera()
    camera_ok = cap is not None and cap.isOpened()

    return jsonify({
        "success": True,
        "app": "SafeDriveAI Backend",
        "camera_available": camera_ok,
        "session_active": session_active,
        "timestamp": now_iso()
    })


# =========================================================
# Graceful Shutdown
# =========================================================
@app.teardown_appcontext
def teardown(_exception=None):
    pass


# =========================================================
# Run App
# =========================================================
if __name__ == "__main__":
    ensure_sessions_file()
    app.run(host="0.0.0.0", port=5000, debug=True)