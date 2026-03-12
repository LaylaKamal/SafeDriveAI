const alertnessScore = document.getElementById("alertnessScore");
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
const voiceLanguageText = document.getElementById("voiceLanguageText");

const testVoiceBtn = document.getElementById("testVoiceBtn");
const listenNowBtn = document.getElementById("listenNowBtn");

const overviewSessionState = document.getElementById("overviewSessionState");
const overviewRiskLevel = document.getElementById("overviewRiskLevel");
const overviewRiskMessage = document.getElementById("overviewRiskMessage");
const overviewScore = document.getElementById("overviewScore");
const riskLevelPill = document.getElementById("riskLevelPill");
const heroRiskCard = document.getElementById("heroRiskCard");
const cameraStateChip = document.getElementById("cameraStateChip");

let sessionActive = false;
let lastRiskLevel = "Safe";
let lastVoiceTriggerTime = 0;
let voiceAssistantBusy = false;

let currentVoiceQuestion = "";
let currentVoiceReason = "manual";
let currentVoiceRiskLevel = "Safe";
let currentDialogueStage = 0;
let currentTranscript = "";
let escalationCount = 0;

let headDropStartTime = null;
let eyesClosedStartTime = null;
let highRiskStartTime = null;

const HEAD_DROP_DELAY_MS = 5000;
const EYES_CLOSED_DELAY_MS = 3000;
const HIGH_RISK_DELAY_MS = 2500;

const VOICE_COOLDOWN_MS = 15000;
const LISTEN_TIMEOUT_MS = 5000;

const warningSound = new Audio("/static/sounds/warning.wav");
const alertSound = new Audio("/static/sounds/alert.wav");

const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;

const DIALOG_FLOW = {
  Medium: [
    "You seem a little tired. Are you okay?",
    "Please stay focused. Can you confirm that you are alert?",
    "Say yes if you are fine and still paying attention.",
  ],
  High: [
    "Warning. You appear very fatigued. Are you still awake?",
    "Please respond now so I can confirm you are okay.",
    "I could not confirm your condition. Do you need to stop and take a break?",
  ],
  manual: [
    "Hello. This is a voice assistant test. Can you hear me?",
    "Please say yes if you can hear me clearly.",
    "Thank you. The voice assistant test is complete.",
  ],
};

const POSITIVE_WORDS = [
  "yes",
  "yeah",
  "yep",
  "i am okay",
  "i'm okay",
  "i am fine",
  "i'm fine",
  "fine",
  "good",
  "awake",
  "alert",
  "i can hear you",
  "hear you",
  "i am here",
  "still awake",
  "focused",
  "attentive",
  "i am alert",
  "i'm alert",
  "i am good",
  "i'm good",
  "okay",
  "all good",
];

const NEGATIVE_WORDS = [
  "no",
  "not okay",
  "tired",
  "sleepy",
  "drowsy",
  "exhausted",
  "fatigued",
  "need a break",
  "need rest",
  "stop",
  "rest",
  "pull over",
  "i am not fine",
  "i'm not fine",
  "can't focus",
  "cannot focus",
  "need to stop",
  "i am tired",
  "i'm tired",
  "i am sleepy",
  "i'm sleepy",
  "not good",
  "i need rest",
  "i need a break",
];

function setRiskVisual(level) {
  riskLevelPill.className = "risk-pill";
  heroRiskCard.style.background =
    "linear-gradient(135deg, rgba(34, 197, 94, 0.12), rgba(78, 163, 255, 0.08)), rgba(17, 26, 45, 0.82)";

  if (level === "Safe") {
    riskLevelPill.classList.add("safe");
  } else if (level === "Low") {
    riskLevelPill.classList.add("low");
    heroRiskCard.style.background =
      "linear-gradient(135deg, rgba(234, 179, 8, 0.12), rgba(78, 163, 255, 0.08)), rgba(17, 26, 45, 0.82)";
  } else if (level === "Medium") {
    riskLevelPill.classList.add("medium");
    heroRiskCard.style.background =
      "linear-gradient(135deg, rgba(249, 115, 22, 0.15), rgba(78, 163, 255, 0.08)), rgba(17, 26, 45, 0.82)";
  } else if (level === "High") {
    riskLevelPill.classList.add("high");
    heroRiskCard.style.background =
      "linear-gradient(135deg, rgba(239, 68, 68, 0.16), rgba(78, 163, 255, 0.08)), rgba(17, 26, 45, 0.82)";
  } else {
    riskLevelPill.classList.add("safe");
  }

  riskLevelPill.textContent = level || "Safe";
}

function addEvent(message) {
  const empty = eventLog.querySelector(".empty-state");
  if (empty) empty.remove();

  const item = document.createElement("div");
  item.className = "log-item";
  item.innerHTML = `
    <span class="log-time">${new Date().toLocaleTimeString()}</span>
    <span class="log-message">${message}</span>
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

function resetFatigueTimers() {
  headDropStartTime = null;
  eyesClosedStartTime = null;
  highRiskStartTime = null;
}

async function postVoiceEvent(payload) {
  try {
    await fetch("/api/voice-event", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  } catch (error) {
    addEvent("Unable to save voice assistant event");
  }
}

function normalizeSpeechText(text) {
  return (text || "")
    .toLowerCase()
    .replace(/[^\w\s']/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function getVoiceSequenceKey(reason, risk) {
  if (reason === "manual-test") return "manual";
  if (risk === "High") return "High";
  return "Medium";
}

function getQuestionByStage(reason, risk, stage) {
  const key = getVoiceSequenceKey(reason, risk);
  const sequence = DIALOG_FLOW[key] || DIALOG_FLOW.Medium;
  return sequence[Math.min(stage, sequence.length - 1)];
}

function analyzeEnglishResponse(transcript) {
  const text = normalizeSpeechText(transcript);

  if (!text || text.length < 2) {
    return {
      responded: false,
      status: "no_response",
      message: "No clear response detected",
    };
  }

  const hasPositive = POSITIVE_WORDS.some((word) =>
    text.includes(normalizeSpeechText(word)),
  );

  const hasNegative = NEGATIVE_WORDS.some((word) =>
    text.includes(normalizeSpeechText(word)),
  );

  if (hasNegative && !hasPositive) {
    return {
      responded: true,
      status: "needs_break",
      message: "Driver sounds fatigued and may need a break",
    };
  }

  if (hasPositive && !hasNegative) {
    return {
      responded: true,
      status: "responsive",
      message: "Driver is responsive",
    };
  }

  if (hasPositive && hasNegative) {
    return {
      responded: true,
      status: "unclear_response",
      message: "Mixed response detected, confirmation needed",
    };
  }

  const shortSafeReplies = ["yes", "okay", "fine", "awake", "here", "good"];
  if (shortSafeReplies.includes(text)) {
    return {
      responded: true,
      status: "responsive",
      message: "Driver is responsive",
    };
  }

  if (text.length >= 4) {
    return {
      responded: true,
      status: "unclear_response",
      message: "Response detected, but it is unclear",
    };
  }

  return {
    responded: false,
    status: "no_response",
    message: "No clear response detected",
  };
}

function speakEnglish(text, onEnd = null) {
  if (!("speechSynthesis" in window)) {
    voiceAssistantStatus.textContent = "Speech unsupported";
    if (onEnd) onEnd();
    return;
  }

  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-US";
  utterance.rate = 0.95;
  utterance.pitch = 1.0;
  utterance.volume = 1.0;

  const voices = window.speechSynthesis.getVoices();
  const englishVoice =
    voices.find((v) => v.lang && v.lang.toLowerCase().includes("en-us")) ||
    voices.find((v) => v.lang && v.lang.toLowerCase().startsWith("en"));

  if (englishVoice) {
    utterance.voice = englishVoice;
    if (voiceLanguageText) {
      voiceLanguageText.textContent = englishVoice.lang;
    }
  } else if (voiceLanguageText) {
    voiceLanguageText.textContent = "English";
  }

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

async function speakAndListen(question) {
  currentVoiceQuestion = question;
  voiceQuestionText.textContent = question;
  voiceTranscriptText.textContent = "-";
  voiceResponseStatus.textContent = "Checking response...";

  await postVoiceEvent({
    event_type: "assistant_triggered",
    question: question,
    transcript: "",
    responded: false,
    response_status: "Assistant triggered",
    reason: currentVoiceReason,
    risk_level: currentVoiceRiskLevel,
  });

  speakEnglish(question, () => {
    startListening();
  });
}

function finishVoiceCycle() {
  voiceAssistantBusy = false;
  voiceAssistantStatus.textContent = "Idle";
}

async function handleResponseAnalysis(analysis, transcript) {
  voiceResponseStatus.textContent = analysis.message;
  currentTranscript = transcript || "";
  voiceTranscriptText.textContent = currentTranscript || "-";

  await postVoiceEvent({
    event_type: "driver_response",
    question: currentVoiceQuestion,
    transcript: currentTranscript,
    responded: analysis.responded,
    response_status: analysis.message,
    reason: currentVoiceReason,
    risk_level: currentVoiceRiskLevel,
  });

  if (analysis.status === "responsive") {
    addEvent("Driver response confirmed");
    speakEnglish("Good. Stay focused and keep your attention on the road.");
    finishVoiceCycle();
    return;
  }

  if (analysis.status === "needs_break") {
    addEvent("Driver may need a break");
    speakEnglish(
      "You may be too fatigued to continue safely. Please pull over in a safe place and take a short break.",
    );
    finishVoiceCycle();
    return;
  }

  if (analysis.status === "unclear_response") {
    addEvent("Unclear driver response detected");
    currentDialogueStage += 1;

    if (currentDialogueStage <= 1) {
      const followUp = getQuestionByStage(
        currentVoiceReason,
        currentVoiceRiskLevel,
        currentDialogueStage,
      );
      speakAndListen(followUp);
    } else {
      speakEnglish(
        "I could not clearly understand your response. If you feel tired, please stop in a safe place.",
      );
      finishVoiceCycle();
    }
    return;
  }

  escalationCount += 1;
  addEvent("No valid response detected from driver");
  currentDialogueStage += 1;

  if (currentDialogueStage <= 1) {
    const followUp = getQuestionByStage(
      currentVoiceReason,
      currentVoiceRiskLevel,
      currentDialogueStage,
    );
    speakAndListen(followUp);
  } else {
    speakEnglish(
      "No response detected. Please pull over safely if you are feeling sleepy or unwell.",
    );
    finishVoiceCycle();
  }
}

function startListening() {
  if (!SpeechRecognition) {
    voiceAssistantStatus.textContent = "Speech unsupported";
    voiceResponseStatus.textContent =
      "Speech recognition is not supported in this browser";
    addEvent("Speech recognition is not supported in this browser");
    finishVoiceCycle();
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  recognition.continuous = false;

  let gotResult = false;
  let alreadyHandled = false;
  let forceStopTimeout = null;

  recognition.onstart = () => {
    voiceAssistantStatus.textContent = "Listening";
    addEvent("Voice assistant started listening");
  };

  recognition.onresult = async (event) => {
    if (alreadyHandled) return;

    const result = event.results[event.results.length - 1];
    if (!result || !result.isFinal) return;

    alreadyHandled = true;
    gotResult = true;

    if (forceStopTimeout) {
      clearTimeout(forceStopTimeout);
      forceStopTimeout = null;
    }

    const transcript = result[0]?.transcript || "";
    addEvent(`Driver response: ${transcript}`);

    const analysis = analyzeEnglishResponse(transcript);
    await handleResponseAnalysis(analysis, transcript);

    try {
      recognition.stop();
    } catch (e) {}
  };

  recognition.onerror = async () => {
    if (alreadyHandled) return;
    alreadyHandled = true;

    if (forceStopTimeout) {
      clearTimeout(forceStopTimeout);
      forceStopTimeout = null;
    }

    addEvent("An error occurred while listening");
    const analysis = {
      responded: false,
      status: "no_response",
      message: "Unable to capture driver response",
    };
    await handleResponseAnalysis(analysis, "");
  };

  recognition.onend = async () => {
    if (forceStopTimeout) {
      clearTimeout(forceStopTimeout);
      forceStopTimeout = null;
    }

    if (alreadyHandled) return;

    if (!gotResult) {
      alreadyHandled = true;
      const analysis = {
        responded: false,
        status: "no_response",
        message: "No response detected",
      };
      await handleResponseAnalysis(analysis, "");
    }
  };

  recognition.start();

  forceStopTimeout = setTimeout(() => {
    try {
      recognition.stop();
    } catch (e) {}
  }, LISTEN_TIMEOUT_MS);
}

async function triggerSmartVoiceAssistant(reason = "manual-test") {
  const now = Date.now();

  if (voiceAssistantBusy) return;
  if (
    reason !== "manual-test" &&
    now - lastVoiceTriggerTime < VOICE_COOLDOWN_MS
  ) {
    return;
  }

  lastVoiceTriggerTime = now;
  voiceAssistantBusy = true;
  currentDialogueStage = 0;
  currentTranscript = "";
  escalationCount = 0;
  currentVoiceReason = reason;
  currentVoiceRiskLevel = lastRiskLevel;

  const firstQuestion = getQuestionByStage(reason, currentVoiceRiskLevel, 0);
  addEvent(`Voice assistant triggered (${reason})`);

  await speakAndListen(firstQuestion);
}

function handleSmartVoiceTrigger(data) {
  const now = Date.now();

  const riskLevel = (data.risk_level || "").toString().toLowerCase();
  const isHeadDrop = !!data.head_drop;
  const isEyesClosed = !!data.eyes_closed;
  const isYawning = !!data.yawning;
  const score = data.alertness_score ?? 100;

  let fatigueSignals = 0;
  if (isHeadDrop) fatigueSignals++;
  if (isEyesClosed) fatigueSignals++;
  if (isYawning) fatigueSignals++;
  if (score < 70) fatigueSignals++;

  if (isHeadDrop) {
    if (!headDropStartTime) headDropStartTime = now;
  } else {
    headDropStartTime = null;
  }

  if (isEyesClosed) {
    if (!eyesClosedStartTime) eyesClosedStartTime = now;
  } else {
    eyesClosedStartTime = null;
  }

  if (riskLevel === "high") {
    if (!highRiskStartTime) highRiskStartTime = now;
  } else {
    highRiskStartTime = null;
  }

  const headDropElapsed = headDropStartTime ? now - headDropStartTime : 0;
  const eyesClosedElapsed = eyesClosedStartTime ? now - eyesClosedStartTime : 0;
  const highRiskElapsed = highRiskStartTime ? now - highRiskStartTime : 0;

  if (highRiskElapsed >= HIGH_RISK_DELAY_MS) {
    addEvent("High risk persisted long enough - triggering voice assistant");
    triggerSmartVoiceAssistant("risk-high");
    resetFatigueTimers();
    return;
  }

  if (eyesClosedElapsed >= EYES_CLOSED_DELAY_MS && fatigueSignals >= 2) {
    addEvent("Persistent eye closure detected - triggering voice assistant");
    triggerSmartVoiceAssistant("eyes-closed-persistent");
    resetFatigueTimers();
    return;
  }

  if (
    headDropElapsed >= HEAD_DROP_DELAY_MS &&
    score < 70 &&
    fatigueSignals >= 2
  ) {
    addEvent("Persistent head drop detected - triggering voice assistant");
    triggerSmartVoiceAssistant("head-drop-persistent");
    resetFatigueTimers();
  }
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
    <div class="summary-item">
      <span>Voice Triggers</span>
      <span>${sessionData.voice_assistant_trigger_count ?? 0}</span>
    </div>
    <div class="summary-item">
      <span>Voice Success</span>
      <span>${sessionData.voice_response_success_count ?? 0}</span>
    </div>
    <div class="summary-item">
      <span>Voice Failures</span>
      <span>${sessionData.voice_response_failure_count ?? 0}</span>
    </div>
  `;
}

async function fetchStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();

    alertnessScore.textContent = data.alertness_score ?? 0;
    riskMessage.textContent = data.message ?? "-";
    driverDetected.textContent = data.driver_detected ? "Yes" : "No";
    statusTimestamp.textContent = data.timestamp || "-";

    alertBannerText.textContent = data.message || "Status updated";
    alertBannerTime.textContent = data.timestamp || "";

    overviewScore.textContent = data.alertness_score ?? 0;
    overviewRiskLevel.textContent = data.risk_level ?? "-";
    overviewRiskMessage.textContent = data.message ?? "-";

    updateBadge(eyesClosedBadge, !!data.eyes_closed);
    updateBadge(yawningBadge, !!data.yawning);
    updateBadge(headDropBadge, !!data.head_drop);

    setRiskVisual(data.risk_level ?? "Safe");

    if (data.driver_detected) {
      cameraStateChip.textContent = "Driver Detected";
    } else {
      cameraStateChip.textContent = "Waiting for Driver";
    }

    if (data.risk_level === "Medium" && lastRiskLevel !== "Medium") {
      warningSound.currentTime = 0;
      warningSound.play().catch(() => {});
      addEvent("Medium fatigue detected");
    }

    if (data.risk_level === "High" && lastRiskLevel !== "High") {
      alertSound.currentTime = 0;
      alertSound.play().catch(() => {});
      addEvent("High fatigue detected");
    }

    lastRiskLevel = data.risk_level || "Safe";

    if (sessionActive) {
      handleSmartVoiceTrigger(data);
    } else {
      resetFatigueTimers();
    }
  } catch (error) {
    addEvent("Failed to fetch driver status");
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
      overviewSessionState.textContent = "Active";
      updateSummary(data.session);
    } else {
      sessionBadge.textContent = "Inactive";
      sessionBadge.className = "badge neutral";
      overviewSessionState.textContent = "Inactive";
      updateSummary(null);
      resetFatigueTimers();
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
      overviewSessionState.textContent = "Active";
      addEvent("Session started");
      await fetchCurrentSession();
      await fetchHealth();
    } else {
      addEvent(data.message || "Failed to start session");
    }
  } catch (error) {
    addEvent("An error occurred while starting the session");
  }
}

async function endSession() {
  try {
    const res = await fetch("/api/end-session", { method: "POST" });
    const data = await res.json();

    if (data.success) {
      sessionActive = false;
      sessionBadge.textContent = "Inactive";
      sessionBadge.className = "badge neutral";
      overviewSessionState.textContent = "Inactive";
      resetFatigueTimers();
      addEvent("Session ended");

      if (data.report_url) {
        window.open(data.report_url, "_blank");
      }

      await fetchCurrentSession();
      await fetchHealth();
    } else {
      addEvent(data.message || "Failed to end session");
    }
  } catch (error) {
    addEvent("An error occurred while ending the session");
  }
}

startBtn.onclick = startSession;
endBtn.onclick = endSession;

refreshBtn.onclick = async () => {
  await fetchHealth();
  await fetchStatus();
  await fetchCurrentSession();
  addEvent("Status refreshed manually");
};

testVoiceBtn.onclick = async () => {
  await triggerSmartVoiceAssistant("manual-test");
};

listenNowBtn.onclick = () => {
  currentVoiceReason = "manual-listen";
  currentVoiceRiskLevel = lastRiskLevel;
  currentDialogueStage = 0;
  startListening();
};

if ("speechSynthesis" in window) {
  window.speechSynthesis.onvoiceschanged = () => {
    const voices = window.speechSynthesis.getVoices();
    const englishVoice =
      voices.find((v) => v.lang && v.lang.toLowerCase().includes("en-us")) ||
      voices.find((v) => v.lang && v.lang.toLowerCase().startsWith("en"));

    if (voiceLanguageText) {
      voiceLanguageText.textContent = englishVoice
        ? englishVoice.lang
        : "English";
    }
  };
}

setInterval(fetchStatus, 1500);
setInterval(fetchCurrentSession, 3000);
setInterval(fetchHealth, 5000);

fetchHealth();
fetchStatus();
fetchCurrentSession();
