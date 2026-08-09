document.addEventListener("DOMContentLoaded", () => {
  const API_BASE = "http://localhost:5000";
  const CALLER_ID_KEY = "arogya_sathi_caller_id";

  // Day 4: a persistent caller ID (kept in this browser's localStorage) is
  // how the agent recognises "the same caller calling again" across
  // separate sessions, so it can look up and continue from memory.
  function getStoredCallerId() {
    return localStorage.getItem(CALLER_ID_KEY);
  }
  function storeCallerId(id) {
    if (id) localStorage.setItem(CALLER_ID_KEY, id);
  }

  // --- Screens (the 5 required agent states) ---
  const screens = {
    ready: document.getElementById("screen-ready"),
    connecting: document.getElementById("screen-connecting"),
    micError: document.getElementById("screen-mic-error"),
    call: document.getElementById("screen-call"),
    ended: document.getElementById("screen-ended"),
  };

  // --- Elements ---
  const startBtn = document.getElementById("start-btn");
  const micRetryBtn = document.getElementById("mic-retry-btn");
  const micErrorDetail = document.getElementById("mic-error-detail");
  const endCallBtn = document.getElementById("end-call-btn");
  const restartBtn = document.getElementById("restart-btn");

  const agentText = document.getElementById("agent-text");
  const agentAvatar = document.getElementById("agent-avatar");
  const playerText = document.getElementById("player-text");
  const playerBubble = document.getElementById("player-bubble");
  const escalationBanner = document.getElementById("escalation-banner");

  const micBtn = document.getElementById("mic-btn");
  const statusLabel = document.getElementById("status-label");
  const statusDot = document.getElementById("status-dot");
  const agentAudio = document.getElementById("agent-audio");
  const visualizerCanvas = document.getElementById("visualizer");
  const vizCtx = visualizerCanvas ? visualizerCanvas.getContext("2d") : null;

  // --- State ---
  let mediaRecorder;
  let audioChunks = [];
  let isRecording = false;
  let micStream = null;
  let currentState = { phase: "active", history: [] };

  // Web Audio (for the "who is speaking" visualizer). Built lazily on first
  // user gesture, and degrades gracefully (no crash) if unsupported.
  let audioCtx = null;
  let micAnalyser = null;
  let agentAnalyser = null;
  let agentSourceNode = null;
  let vizRAF = null;

  // ---------- Screen state machine ----------
  function showScreen(name) {
    Object.entries(screens).forEach(([key, el]) => {
      if (!el) return;
      if (key === name) {
        el.classList.remove("hidden");
        el.classList.add(key === "connecting" || key === "call" ? "flex" : "block");
      } else {
        el.classList.add("hidden");
        el.classList.remove("flex", "block");
      }
    });
  }

  function setStatus(text, colorClass) {
    statusLabel.textContent = text;
    statusDot.className = "status-dot " + colorClass;
  }

  // ---------- Web Audio helpers ----------
  function ensureAudioContext() {
    if (audioCtx) return audioCtx;
    try {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      audioCtx = new Ctx();
    } catch (e) {
      console.warn("Web Audio not available, falling back to text-only status.", e);
      audioCtx = null;
    }
    return audioCtx;
  }

  function drawBars(analyser, colorHex) {
    if (!vizCtx || !analyser) return;
    const bufferLength = analyser.frequencyBinCount;
    const data = new Uint8Array(bufferLength);

    function frame() {
      vizRAF = requestAnimationFrame(frame);
      analyser.getByteFrequencyData(data);
      vizCtx.clearRect(0, 0, visualizerCanvas.width, visualizerCanvas.height);
      vizCtx.fillStyle = colorHex;
      const barCount = 16;
      const step = Math.floor(bufferLength / barCount) || 1;
      const barWidth = visualizerCanvas.width / barCount;
      for (let i = 0; i < barCount; i++) {
        const v = data[i * step] / 255;
        const h = Math.max(2, v * visualizerCanvas.height);
        vizCtx.fillRect(i * barWidth + 1, visualizerCanvas.height - h, barWidth - 2, h);
      }
    }
    frame();
  }

  function stopVisualizer() {
    if (vizRAF) cancelAnimationFrame(vizRAF);
    vizRAF = null;
    if (vizCtx) vizCtx.clearRect(0, 0, visualizerCanvas.width, visualizerCanvas.height);
  }

  function startMicVisualizer(stream) {
    const ctx = ensureAudioContext();
    if (!ctx) return;
    try {
      const source = ctx.createMediaStreamSource(stream);
      micAnalyser = ctx.createAnalyser();
      micAnalyser.fftSize = 128;
      source.connect(micAnalyser);
      drawBars(micAnalyser, "#2dd4bf"); // teal = you
    } catch (e) {
      console.warn("Mic visualizer failed to start:", e);
    }
  }

  function startAgentVisualizer() {
    const ctx = ensureAudioContext();
    if (!ctx) return;
    try {
      // A MediaElementSourceNode can only be created ONCE per <audio> element
      // for its entire lifetime, so we build it lazily and reuse it forever.
      if (!agentSourceNode) {
        agentSourceNode = ctx.createMediaElementSource(agentAudio);
        agentAnalyser = ctx.createAnalyser();
        agentAnalyser.fftSize = 128;
        agentSourceNode.connect(agentAnalyser);
        agentAnalyser.connect(ctx.destination); // must reconnect to speakers
      }
      drawBars(agentAnalyser, "#38bdf8"); // sky blue = agent
    } catch (e) {
      console.warn("Agent visualizer failed to start:", e);
    }
  }

  // ---------- 1. START CALL (Ready -> Connecting -> Call) ----------
  startBtn.addEventListener("click", () => connectToAgent());
  micRetryBtn.addEventListener("click", () => connectToAgent());

  async function connectToAgent() {
    showScreen("connecting");
    ensureAudioContext(); // must be created on a user gesture

    try {
      const storedId = getStoredCallerId();
      const url = storedId
        ? `${API_BASE}/start-session?user_id=${encodeURIComponent(storedId)}`
        : `${API_BASE}/start-session`;
      const res = await axios.post(url);

      // Remember this caller's ID for next time (new callers get one back
      // from the backend on their very first call).
      if (res.data.caller_id) storeCallerId(res.data.caller_id);

      agentText.textContent = res.data.text;
      if (res.data.initial_state) currentState = res.data.initial_state;

      showScreen("call");
      setStatus("Tap the mic to talk", "bg-slate-500");
      handleAudio(res.data);
    } catch (err) {
      console.error(err);
      showScreen("ready");
      alert("Could not connect to Arogya Sathi. Please make sure the backend server is running, then try again.");
    }
  }

  // ---------- 2. MIC LOGIC (Listening state) ----------
  micBtn.addEventListener("click", async () => {
    if (!isRecording) {
      await startListening();
    } else {
      stopListening();
    }
  });

  async function startListening() {
    try {
      micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      handleMicError(err);
      return;
    }

    mediaRecorder = new MediaRecorder(micStream);
    audioChunks = [];
    mediaRecorder.ondataavailable = (event) => audioChunks.push(event.data);
    mediaRecorder.onstop = onRecordingStopped;

    mediaRecorder.start();
    isRecording = true;

    setStatus("Listening to you...", "bg-teal-400");
    micBtn.innerHTML = "⏹️";
    micBtn.classList.add("pulse-listen");
    startMicVisualizer(micStream);
  }

  function stopListening() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
    isRecording = false;
    micBtn.classList.remove("pulse-listen");
    stopVisualizer();
    if (micStream) {
      micStream.getTracks().forEach((t) => t.stop());
      micStream = null;
    }
  }

  async function onRecordingStopped() {
    setStatus("Thinking...", "bg-amber-400");
    micBtn.innerHTML = "✨";
    micBtn.disabled = true;

    const blob = new Blob(audioChunks, { type: "audio/webm" });
    const formData = new FormData();
    formData.append("file", blob, "recording.webm");
    formData.append("current_state", JSON.stringify(currentState));

    try {
      const res = await axios.post(`${API_BASE}/chat-with-voice`, formData);

      if (res.data.user_transcript) {
        playerText.textContent = `"${res.data.user_transcript}"`;
        playerBubble.classList.remove("hidden");
      }

      agentText.textContent = res.data.ai_text;

      if (res.data.escalate) {
        escalationBanner.classList.remove("hidden");
        escalationBanner.classList.add("flex");
      } else {
        escalationBanner.classList.add("hidden");
        escalationBanner.classList.remove("flex");
      }

      if (res.data.updated_state) currentState = res.data.updated_state;

      handleAudio(res.data);
    } catch (err) {
      console.error(err);
      agentText.textContent = "ટેકનિકલ સમસ્યા આવી. કૃપા કરીને ફરી પ્રયત્ન કરો. (Technical issue, please retry.)";
      resetMicUI();
    }
  }

  // ---------- Mic permission error handling ----------
  function handleMicError(err) {
    let message = "Microphone access was blocked, so Arogya Sathi cannot hear you.";
    if (err && err.name === "NotAllowedError") {
      message = "Microphone access was denied. Please allow microphone permission for this site.";
    } else if (err && err.name === "NotFoundError") {
      message = "No microphone was found on this device. Please connect a microphone and try again.";
    } else if (err && err.name === "NotReadableError") {
      message = "Your microphone is being used by another app. Please close it and try again.";
    }
    micErrorDetail.textContent = message;
    showScreen("micError");
  }

  // ---------- Speaking state (agent audio playback) ----------
  function handleAudio(data) {
    const audioSrc = data.audioUrl || data.audio_url;
    if (audioSrc) {
      playAudio(audioSrc);
    } else {
      speakNative(data.ai_text || data.text);
    }
  }

  function playAudio(url) {
    agentAudio.src = url;
    setStatus("Arogya Sathi is speaking...", "bg-sky-400");
    agentAvatar.classList.add("breathe");
    startAgentVisualizer();

    agentAudio.play().catch((e) => {
      console.warn("Autoplay blocked, falling back to browser TTS.", e);
      resetMicUI();
    });
    agentAudio.onended = onAgentDoneSpeaking;
    agentAudio.onerror = onAgentDoneSpeaking;
  }

  function speakNative(text) {
    setStatus("Arogya Sathi is speaking...", "bg-sky-400");
    agentAvatar.classList.add("breathe");
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.onend = onAgentDoneSpeaking;
    window.speechSynthesis.speak(utterance);
  }

  function onAgentDoneSpeaking() {
    agentAvatar.classList.remove("breathe");
    stopVisualizer();
    resetMicUI();
  }

  function resetMicUI() {
    setStatus("Tap the mic to talk", "bg-slate-500");
    micBtn.disabled = false;
    micBtn.innerHTML = "🎙️";
    micBtn.classList.remove("pulse-listen");
  }

  // ---------- End Call / Start Again ----------
  endCallBtn.addEventListener("click", () => {
    stopListening();
    stopVisualizer();
    agentAudio.pause();
    window.speechSynthesis.cancel();
    showScreen("ended");
  });

  restartBtn.addEventListener("click", () => {
    location.reload();
  });
});
