const alertnessScore = document.getElementById("alertnessScore");
const riskLevel = document.getElementById("riskLevel");
const riskMessage = document.getElementById("riskMessage");
const driverDetected = document.getElementById("driverDetected");
const statusTimestamp = document.getElementById("statusTimestamp");

const eyesClosedBadge = document.getElementById("eyesClosedBadge");
const yawningBadge = document.getElementById("yawningBadge");
const headDropBadge = document.getElementById("headDropBadge");
const sessionBadge = document.getElementById("sessionBadge");

const eventLog = document.getElementById("eventLog");
const sessionSummary = document.getElementById("sessionSummary");

const systemHealthText = document.getElementById("systemHealthText");
const alertBannerText = document.getElementById("alertBannerText");
const alertBannerTime = document.getElementById("alertBannerTime");

const startBtn = document.getElementById("startSessionBtn");
const endBtn = document.getElementById("endSessionBtn");
const refreshBtn = document.getElementById("refreshStatusBtn");

const voiceAssistantStatus = document.getElementById("voiceAssistantStatus");
const voiceQuestionText = document.getElementById("voiceQuestionText");
const voiceTranscriptText = document.getElementById("voiceTranscriptText");
const voiceResponseStatus = document.getElementById("voiceResponseStatus");
const testVoiceBtn = document.getElementById("testVoiceBtn");
const listenNowBtn = document.getElementById("listenNowBtn");

let sessionActive = false;
let lastRiskLevel = "Safe";
let voiceAssistantBusy = false;
let lastVoiceTriggerTime = 0;
let lastTranscript = "";
let latestSessionData = null;

const VOICE_COOLDOWN_MS = 12000;
const VOICE_RESPONSE_MIN_LENGTH = 2;

const warningSound = new Audio("/static/sounds/warning.wav");
const alertSound = new Audio("/static/sounds/alert.wav");

const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;

const voiceQuestions = [
  "Are you okay?",
  "Please say something so I know you are awake.",
  "What is your name?",
  "Can you tell me how you feel right now?",
  "Please answer: are you still focused?",
];

function addEvent(message) {
  const empty = eventLog.querySelector(".empty-state");
  if (empty) empty.remove();

  const item = document.createElement("div");
  item.className = "summary-item";
  item.innerHTML = `
    <span>${new Date().toLocaleTimeString()}</span>
    <span>${message}</span>
  `;
  eventLog.prepend(item);

  while (eventLog.children.length > 20) {
    eventLog.removeChild(eventLog.lastChild);
  }
}

function updateBadge(el, isActive) {
  el.textContent = isActive ? "Yes" : "No";
  el.className = "badge " + (isActive ? "badge-danger" : "badge-safe");
}

function chooseVoiceQuestion() {
  const index = Math.floor(Math.random() * voiceQuestions.length);
  return voiceQuestions[index];
}

function speakText(text, onEnd = null) {
  if (!("speechSynthesis" in window)) {
    addEvent("Speech synthesis is not supported in this browser");
    if (onEnd) onEnd();
    return;
  }

  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-US";
  utterance.rate = 1.0;
  utterance.pitch = 1.0;

  utterance.onstart = () => {
    voiceAssistantStatus.textContent = "Speaking";
  };

  utterance.onend = () => {
    voiceAssistantStatus.textContent = "Waiting for response";
    if (onEnd) onEnd();
  };

  utterance.onerror = () => {
    voiceAssistantStatus.textContent = "Speech error";
    if (onEnd) onEnd();
  };

  window.speechSynthesis.speak(utterance);
}

function analyzeDriverResponse(transcript) {
  const text = (transcript || "").trim().toLowerCase();

  if (text.length < VOICE_RESPONSE_MIN_LENGTH) {
    return {
      responded: false,
      message: "No valid response detected",
    };
  }

  return {
    responded: true,
    message: "Driver response detected",
  };
}

function startListeningForResponse() {
  if (!SpeechRecognition) {
    voiceAssistantStatus.textContent = "Speech recognition unsupported";
    voiceResponseStatus.textContent = "Browser does not support voice input";
    addEvent("Speech recognition is not supported in this browser");
    voiceAssistantBusy = false;
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  let gotResult = false;

  recognition.onstart = () => {
    voiceAssistantStatus.textContent = "Listening";
    addEvent("Voice assistant started listening");
  };

  recognition.onresult = (event) => {
    gotResult = true;
    const transcript = event.results[0][0].transcript || "";
    lastTranscript = transcript;

    voiceTranscriptText.textContent = transcript;
    addEvent(`Driver said: ${transcript}`);

    const analysis = analyzeDriverResponse(transcript);
    voiceResponseStatus.textContent = analysis.message;

    if (analysis.responded) {
      addEvent("Driver is responsive");
      speakText("Good. Please stay focused and drive safely.");
    } else {
      addEvent("No clear response from driver");
      speakText(
        "I could not detect a clear response. Please stop in a safe place if needed.",
      );
    }
  };

  recognition.onerror = () => {
    voiceAssistantStatus.textContent = "Listening error";
    voiceResponseStatus.textContent = "No response detected";
    addEvent("Voice listening error or no microphone permission");
    voiceAssistantBusy = false;
  };

  recognition.onend = () => {
    if (!gotResult) {
      voiceTranscriptText.textContent = "-";
      voiceResponseStatus.textContent = "No response detected";
      addEvent("No driver response detected");
      speakText(
        "No response detected. Please stay alert or stop in a safe place.",
      );
    }

    voiceAssistantStatus.textContent = "Idle";
    voiceAssistantBusy = false;
  };

  recognition.start();

  setTimeout(() => {
    try {
      recognition.stop();
    } catch (e) {}
  }, 6000);
}

function triggerVoiceAssistant(reason = "manual") {
  const now = Date.now();

  if (voiceAssistantBusy) return;
  if (now - lastVoiceTriggerTime < VOICE_COOLDOWN_MS && reason !== "manual")
    return;

  voiceAssistantBusy = true;
  lastVoiceTriggerTime = now;

  const question = chooseVoiceQuestion();
  voiceQuestionText.textContent = question;
  voiceTranscriptText.textContent = "-";
  voiceResponseStatus.textContent = "Checking...";
  addEvent(`Voice assistant triggered (${reason})`);

  speakText(question, () => {
    startListeningForResponse();
  });
}

function updateSummary(sessionData) {
  if (!sessionData) {
    sessionSummary.innerHTML = `
      <div class="summary-item">
        <span>Status</span>
        <span>No active session</span>
      </div>
    `;
    return;
  }

  sessionSummary.innerHTML = `
    <div class="summary-item">
      <span>Session ID</span>
      <span>${sessionData.session_id || "-"}</span>
    </div>
    <div class="summary-item">
      <span>Total Frames</span>
      <span>${sessionData.total_frames_analyzed ?? 0}</span>
    </div>
    <div class="summary-item">
      <span>Eye Closure Events</span>
      <span>${sessionData.eye_closure_count ?? 0}</span>
    </div>
    <div class="summary-item">
      <span>Yawning Events</span>
      <span>${sessionData.yawn_count ?? 0}</span>
    </div>
    <div class="summary-item">
      <span>Head Drop Events</span>
      <span>${sessionData.head_drop_count ?? 0}</span>
    </div>
    <div class="summary-item">
      <span>Alerts Triggered</span>
      <span>${sessionData.alerts_triggered ?? 0}</span>
    </div>
    <div class="summary-item">
      <span>Average Score</span>
      <span>${sessionData.average_alertness_score ?? 0}</span>
    </div>
    <div class="summary-item">
      <span>Max Risk</span>
      <span>${sessionData.max_risk_level || "-"}</span>
    </div>
  `;
}

async function fetchStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();

    alertnessScore.textContent = data.alertness_score ?? 0;
    riskLevel.textContent = data.risk_level ?? "-";
    riskMessage.textContent = data.message ?? "-";
    driverDetected.textContent = data.driver_detected ? "Yes" : "No";
    statusTimestamp.textContent = data.timestamp || "-";

    alertBannerText.textContent = data.message || "Status updated";
    alertBannerTime.textContent = data.timestamp || "";

    updateBadge(eyesClosedBadge, !!data.eyes_closed);
    updateBadge(yawningBadge, !!data.yawning);
    updateBadge(headDropBadge, !!data.head_drop);

    if (data.risk_level === "Medium" && lastRiskLevel !== "Medium") {
      warningSound.currentTime = 0;
      warningSound.play().catch(() => {});
      addEvent("Medium fatigue warning detected");
    }

    if (data.risk_level === "High" && lastRiskLevel !== "High") {
      alertSound.currentTime = 0;
      alertSound.play().catch(() => {});
      addEvent("High fatigue alert detected");
    }

    if (
      sessionActive &&
      (data.risk_level === "Medium" || data.risk_level === "High")
    ) {
      triggerVoiceAssistant(`risk-${data.risk_level.toLowerCase()}`);
    }

    lastRiskLevel = data.risk_level;
  } catch (error) {
    addEvent("Failed to fetch status");
  }
}

async function fetchCurrentSession() {
  try {
    const res = await fetch("/api/current-session");
    const data = await res.json();

    sessionActive = !!data.active;

    if (sessionActive) {
      sessionBadge.textContent = "Active";
      sessionBadge.className = "badge badge-safe";
      latestSessionData = data.session;
      updateSummary(data.session);
    } else {
      sessionBadge.textContent = "Inactive";
      sessionBadge.className = "badge";
      latestSessionData = null;
      updateSummary(null);
    }
  } catch (error) {
    addEvent("Failed to fetch session data");
  }
}

async function fetchHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();

    if (data.camera_available) {
      systemHealthText.textContent = data.session_active
        ? "Camera Ready • Session Active"
        : "Camera Ready";
    } else {
      systemHealthText.textContent = "Camera Unavailable";
    }
  } catch (error) {
    systemHealthText.textContent = "Health Check Failed";
  }
}

async function startSession() {
  try {
    const res = await fetch("/api/start-session", { method: "POST" });
    const data = await res.json();

    if (data.success) {
      sessionActive = true;
      sessionBadge.textContent = "Active";
      sessionBadge.className = "badge badge-safe";
      addEvent("Session started");
      fetchCurrentSession();
      fetchHealth();
    } else {
      addEvent(data.message || "Failed to start session");
    }
  } catch (error) {
    addEvent("Error starting session");
  }
}

async function endSession() {
  try {
    const res = await fetch("/api/end-session", { method: "POST" });
    const data = await res.json();

    if (data.success) {
      sessionActive = false;
      sessionBadge.textContent = "Inactive";
      sessionBadge.className = "badge";
      addEvent("Session ended");

      if (data.report_url) {
        window.open(data.report_url, "_blank");
      }

      fetchCurrentSession();
      fetchHealth();
    } else {
      addEvent(data.message || "Failed to end session");
    }
  } catch (error) {
    addEvent("Error ending session");
  }
}

startBtn.onclick = startSession;
endBtn.onclick = endSession;

refreshBtn.onclick = async () => {
  await fetchHealth();
  await fetchStatus();
  await fetchCurrentSession();
  addEvent("Manual refresh complete");
};

testVoiceBtn.onclick = () => {
  triggerVoiceAssistant("manual");
};

listenNowBtn.onclick = () => {
  startListeningForResponse();
};

setInterval(fetchStatus, 1500);
setInterval(fetchCurrentSession, 3000);
setInterval(fetchHealth, 5000);

fetchHealth();
fetchStatus();
fetchCurrentSession();
