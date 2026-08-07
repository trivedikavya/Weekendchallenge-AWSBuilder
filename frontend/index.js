document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const joinScreen = document.getElementById("join-screen");
  const gameStage = document.getElementById("game-stage");
  const controlsFooter = document.getElementById("controls-footer");
  
  const agentText = document.getElementById("agent-text");
  const playerText = document.getElementById("player-text");
  const playerBubble = document.getElementById("player-bubble");
  
  const micBtn = document.getElementById("mic-btn");
  const startBtn = document.getElementById("start-btn");
  const statusLabel = document.getElementById("status-label");
  const agentAudio = document.getElementById("agent-audio");
  const escalationBanner = document.getElementById("escalation-banner");

  let mediaRecorder;
  let audioChunks = [];
  let isRecording = false;

  // Track conversation state (Health Access agent: ongoing history-based chat)
  let currentState = { phase: "active", history: [] };

  // --- 1. START CONNECTION ---
  startBtn.addEventListener("click", async () => {
    // UI Transition
    joinScreen.classList.add("hidden");
    gameStage.classList.remove("hidden");
    gameStage.classList.add("flex");
    controlsFooter.classList.remove("hidden");
    controlsFooter.classList.add("flex");
    
    statusLabel.textContent = "Connecting...";

    try {
      const res = await axios.post("http://localhost:5000/start-session");
      
      // Initial Response
      agentText.textContent = res.data.text;
      
      if (res.data.initial_state) currentState = res.data.initial_state;
      
      handleAudio(res.data);
      
    } catch (err) {
      console.error(err);
      agentText.textContent = "Error connecting to the agent server.";
    }
  });

  // --- 2. MIC LOGIC ---
  micBtn.addEventListener("click", async () => {
    if (!isRecording) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        mediaRecorder.ondataavailable = event => audioChunks.push(event.data);
        
        mediaRecorder.onstop = async () => {
          // UI: Thinking State
          statusLabel.textContent = "Thinking...";
          statusLabel.classList.add("text-orange-400");
          micBtn.innerHTML = "✨"; 
          micBtn.disabled = true;
          micBtn.classList.remove("pulse-record");

          const blob = new Blob(audioChunks, { type: 'audio/webm' });
          const formData = new FormData();
          formData.append("file", blob, "recording.webm");
          formData.append("current_state", JSON.stringify(currentState));

          try {
            const res = await axios.post("http://localhost:5000/chat-with-voice", formData);

            // 1. Show Player Text
            if (res.data.user_transcript) {
                playerText.textContent = `"${res.data.user_transcript}"`;
                playerBubble.classList.remove("hidden");
            }

            // 2. Show Agent Text
            agentText.textContent = res.data.ai_text;

            // 3. Guardrail: show/hide the emergency escalation banner
            if (res.data.escalate) {
                escalationBanner.classList.remove("hidden");
                escalationBanner.classList.add("flex");
            } else {
                escalationBanner.classList.add("hidden");
                escalationBanner.classList.remove("flex");
            }

            // 4. Update State
            if (res.data.updated_state) {
                currentState = res.data.updated_state;
            }

            // 5. Handle Audio
            handleAudio(res.data);

          } catch (err) {
            console.error(err);
            agentText.textContent = "Technical difficulties. Please retry.";
            resetMicUI();
          }
        };

        mediaRecorder.start();
        isRecording = true;
        statusLabel.textContent = "Listening...";
        statusLabel.classList.add("text-red-400");
        micBtn.innerHTML = "⏹️"; 
        micBtn.classList.add("pulse-record");

      } catch (err) {
        alert("Microphone access denied. Please check your browser settings.");
      }

    } else {
      mediaRecorder.stop();
      isRecording = false;
    }
  });

  // --- HELPERS ---
  function handleAudio(data) {
      // Check for both camelCase and snake_case depending on backend payload
      const audioSrc = data.audioUrl || data.audio_url; 
      
      if (audioSrc) {
          playAudio(audioSrc);
      } else {
          // Browser TTS Fallback
          speakNative(data.ai_text || data.text);
      }
  }

  function playAudio(url) {
    agentAudio.src = url;
    statusLabel.textContent = "Speaking...";
    statusLabel.classList.remove("text-orange-400", "text-red-400");
    statusLabel.classList.add("text-green-400");
    
    agentAudio.play();
    agentAudio.onended = resetMicUI;
    agentAudio.onerror = resetMicUI;
  }

  function speakNative(text) {
      console.log("Using Browser TTS fallback");
      statusLabel.textContent = "Speaking...";
      statusLabel.classList.add("text-green-400");
      
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.1; 
      utterance.onend = resetMicUI;
      window.speechSynthesis.speak(utterance);
  }

  function resetMicUI() {
    statusLabel.textContent = "Ready";
    statusLabel.classList.remove("text-orange-400", "text-red-400", "text-green-400");
    statusLabel.classList.add("text-slate-500");
    
    micBtn.disabled = false;
    micBtn.innerHTML = "🎙️";
    micBtn.classList.remove("pulse-record");
  }
});