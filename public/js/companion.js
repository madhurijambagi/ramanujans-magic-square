(() => {
  if (["/", "/index.html", "/reset-password.html"].includes(location.pathname) || typeof api === "undefined") return;
  api.get("/api/auth/me").then(() => {
  const root = document.createElement("section");
  root.className = "game-companion";
  root.innerHTML = `
    <button class="companion-launch" type="button" aria-expanded="false" aria-controls="companion-panel">✦ MagicSquare companion</button>
    <div class="companion-backdrop" hidden>
      <section class="companion-panel" id="companion-panel" role="dialog" aria-modal="true" aria-label="MagicSquare chat" hidden>
        <header><div><strong>SquareVerse</strong><small id="companion-mode">MagicSquare and gaming help</small></div><button type="button" class="companion-close" aria-label="Close chat">×</button></header>
        <div class="companion-options"><select id="companion-game" aria-label="Game"><option>Ramanujan's Magic Square</option></select><select id="companion-language" aria-label="Reply language"><option value="en">English replies</option><option value="kn">ಕನ್ನಡ replies · English input</option></select></div>
        <div class="companion-log" id="companion-log" role="log" aria-live="polite"></div><div class="companion-status" id="companion-status" role="status"></div>
        <form class="companion-form" id="companion-form"><textarea id="companion-input" maxlength="500" rows="2" placeholder="Ask about MagicSquare or gaming…" aria-label="Message"></textarea><div><button type="button" id="companion-mic" aria-label="Open voice chat">🎙 Voice</button><button type="submit" class="btn">Send</button></div></form>
        <div class="companion-footer"><span>Keep personal information private.</span><button type="button" id="companion-clear">Clear history</button></div>
      </section>
      <section class="voice-panel" id="voice-panel" role="dialog" aria-modal="true" aria-label="Voice chat" hidden>
        <header><div><strong>Voice chat</strong><small>Ask about MagicSquare or gaming</small></div><button type="button" id="voice-close" aria-label="Close voice chat">×</button></header>
        <div id="voice-status" role="status">Tap the microphone to start speaking. Replies use a voice available on your device.</div>
        <button type="button" id="voice-listen" class="voice-mic" aria-label="Start voice chat">🎙</button>
      </section>
    </div>`;
  document.body.appendChild(root);

  const $ = (selector) => root.querySelector(selector);
  const launch = $(".companion-launch");
  const backdrop = $(".companion-backdrop");
  const panel = $(".companion-panel");
  const voicePanel = $(".voice-panel");
  const log = $("#companion-log");
  const input = $("#companion-input");
  const status = $("#companion-status");
  const language = $("#companion-language");
  let recognition = null;
  let voiceMode = false;
  let listening = false;
  let sentUtterance = false;
  let languageManuallyChosen = false;
  language.value = localStorage.getItem("squareverse-chat-language") === "kn" ? "kn" : "en";

  function setOpen(which) {
    const open = Boolean(which);
    if (voiceMode && which !== "voice" && "speechSynthesis" in window) speechSynthesis.cancel();
    backdrop.hidden = !open;
    panel.hidden = which !== "chat";
    voicePanel.hidden = which !== "voice";
    launch.setAttribute("aria-expanded", String(open));
    voiceMode = which === "voice";
    if (!open && recognition) {
      sentUtterance = true;
      recognition.abort();
      recognition = null;
      listening = false;
    }
  }

  function addMessage(text, role, id, suggestions = []) {
    const item = document.createElement("article");
    item.className = `companion-message ${role}`;
    const body = document.createElement("p");
    body.textContent = text;
    item.appendChild(body);
    if (suggestions.length) {
      const chips = document.createElement("div");
      chips.className = "companion-suggestions";
      suggestions.forEach((suggestion) => {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = suggestion.label || suggestion;
        button.addEventListener("click", () => {
          const label = suggestion.label || suggestion;
          const shortcuts = {
            "How to play": "How do I play Swap puzzle?",
            "Daily Challenge": "How does the Daily Challenge work?",
            "Hints": "How do hints work?",
            "Odd sizes": "Explain the Siamese method for odd magic square sizes",
            "Divisible by 4": "Explain the construction method for 4x4 and 8x8 squares",
            "6 and 10": "Explain the Strachey method for 6x6 and 10x10 squares",
            "English": "Change chat language to English",
            "ಕನ್ನಡ": "Change chat language to Kannada",
          };
          send(suggestion.question || shortcuts[label] || label, voiceMode);
        });
        chips.appendChild(button);
      });
      item.appendChild(chips);
    }
    if (role === "assistant" && id) {
      const actions = document.createElement("div");
      actions.className = "companion-feedback";
      [["helpful", "Helpful"], ["unhelpful", "Not helpful"], ["report", "Report"]].forEach(([rating, label]) => {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = label;
        button.addEventListener("click", async () => {
          try {
            await api.post("/api/chatbot/feedback", { message_id: id, rating });
            button.textContent = rating === "report" ? "Reported" : "Thanks";
            button.disabled = true;
          } catch (_) { status.textContent = "Sign in to send feedback or reports."; }
        });
        actions.appendChild(button);
      });
      item.appendChild(actions);
    }
    log.appendChild(item);
    log.scrollTop = log.scrollHeight;
  }

  function snapshot() {
    if (typeof state === "undefined" || !state) return {};
    return { order: state.order, mode: state.mode || "scramble", moves: state.moves || 0,
      hints: state.hints || 0, grid: Array.isArray(state.current) ? state.current : null,
      status: state.solvedFlag ? "completed" : state.startTime ? "in_progress" : "ready" };
  }

  async function loadHistory() {
    try {
      const history = await api.get("/api/chatbot/history");
      log.replaceChildren();
      history.forEach((message) => addMessage(message.content, message.role, message.role === "assistant" ? message.id : null));
    } catch (_) { /* Guest sessions do not have saved history. */ }
  }

  function speak(text, lang = language.value) {
    if (!("speechSynthesis" in window) || typeof SpeechSynthesisUtterance === "undefined") {
      $("#voice-status").textContent = "Spoken replies are not supported by this browser.";
      return;
    }
    speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang === "kn" ? "kn-IN" : lang === "hi" ? "hi-IN" : "en-IN";
    utterance.rate = 0.92;
    utterance.pitch = 0.92;
    const voices = speechSynthesis.getVoices();
    const wanted = /(?:^|[\s_-])male(?:$|[\s_-])|(?:^|[\s_-])man(?:$|[\s_-])|david|mark|daniel|james|guy/i;
    const matchingLanguage = voices.filter((voice) => voice.lang.toLowerCase().startsWith(utterance.lang.slice(0, 2)));
    // Prefer a voice labelled male, but Android and some mobile browsers do not
    // expose gendered voice names. In that case let the device choose its default.
    utterance.voice = matchingLanguage.find((voice) => wanted.test(voice.name))
      || matchingLanguage.find((voice) => voice.default)
      || matchingLanguage[0]
      || voices.find((voice) => voice.default)
      || null;
    speechSynthesis.speak(utterance);
  }

  async function send(question, voice = false) {
    const cleanQuestion = String(question || "").trim();
    if (!cleanQuestion) return;
    addMessage(cleanQuestion, "user");
    status.textContent = "Thinking…";
    $("#voice-status").textContent = "Thinking…";
    try {
      const result = await api.post("/api/chatbot", {
        question: cleanQuestion, game_title: $("#companion-game").value,
        language: language.value, game_context: snapshot(), voice_mode: voice
      });
      if (result.language) {
        language.value = result.language;
        localStorage.setItem("squareverse-chat-language", result.language);
      }
      addMessage(result.answer, "assistant", result.assistant_message_id, result.suggestions || []);
      status.textContent = "Curated MagicSquare guide";
      $("#voice-status").textContent = "Reply ready. Tap the microphone to ask another question.";
      if (voice && !voicePanel.hidden) speak(result.answer, result.speech_language || result.language || language.value);
    } catch (error) {
      status.textContent = error.message;
      $("#voice-status").textContent = error.message;
    }
  }

  async function openChat() {
    setOpen("chat");
    if (!log.childElementCount) await loadHistory();
    input.focus();
  }

  async function openVoice() {
    setOpen("voice");
    if (!log.childElementCount) await loadHistory();
  }

  function startListening() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      $("#voice-status").textContent = "Speech recognition is not supported by this browser. You can use text chat instead.";
      return;
    }
    if (listening && recognition) {
      recognition.stop();
      return;
    }
    sentUtterance = false;
    const utterance = new SpeechRecognition();
    recognition = utterance;
    // Speech recognition should understand the requested English voice input;
    // the backend independently returns Kannada text and Kannada speech.
    utterance.lang = "en-IN";
    utterance.continuous = false;
    utterance.interimResults = false;
    utterance.maxAlternatives = 1;
    let transcript = "";
    utterance.onresult = (event) => {
      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        if (event.results[index].isFinal) transcript += event.results[index][0].transcript;
      }
    };
    utterance.onerror = (event) => {
      if (event.error !== "aborted" && event.error !== "no-speech") $("#voice-status").textContent = "I couldn't hear that. Tap the microphone and try again.";
    };
    utterance.onend = () => {
      listening = false;
      $("#voice-listen").classList.remove("listening");
      $("#voice-listen").setAttribute("aria-label", "Start voice chat");
      recognition = null;
      const finalText = transcript.trim();
      if (finalText && !sentUtterance) {
        sentUtterance = true;
        send(finalText, true);
      } else if (!finalText && !sentUtterance) {
        $("#voice-status").textContent = "I didn't hear a question. Tap the microphone to try again.";
      }
    };
    try {
      utterance.start();
      listening = true;
      $("#voice-listen").classList.add("listening");
      $("#voice-listen").setAttribute("aria-label", "Stop listening");
      $("#voice-status").textContent = "Listening… speak now.";
    } catch (_) {
      $("#voice-status").textContent = "Microphone could not start. Check browser microphone permissions.";
    }
  }

  launch.addEventListener("click", openChat);
  $(".companion-close").addEventListener("click", () => setOpen(null));
  $("#companion-mic").addEventListener("click", openVoice);
  $("#voice-close").addEventListener("click", () => { if ("speechSynthesis" in window) speechSynthesis.cancel(); setOpen(null); });
  backdrop.addEventListener("click", (event) => { if (event.target === backdrop) setOpen(null); });
  document.addEventListener("keydown", (event) => { if (event.key === "Escape" && !backdrop.hidden) setOpen(null); });
  $("#companion-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const question = input.value;
    input.value = "";
    send(question, voiceMode);
  });
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); $("#companion-form").requestSubmit(); }
  });
  $("#voice-listen").addEventListener("click", startListening);
  $("#companion-clear").addEventListener("click", async () => {
    try { await api.del("/api/chatbot/history"); log.replaceChildren(); status.textContent = "Saved chat history cleared."; }
    catch (_) { status.textContent = "Sign in to manage saved history."; }
  });
  language.addEventListener("change", () => {
    languageManuallyChosen = true;
    localStorage.setItem("squareverse-chat-language", language.value);
  });
  api.get("/api/auth/me").then((me) => {
    if (me.chatbot_language && !languageManuallyChosen) {
      language.value = me.chatbot_language === "kn" ? "kn" : "en";
      localStorage.setItem("squareverse-chat-language", language.value);
    }
  }).catch(() => {});
  $("#companion-mode").textContent = "Curated MagicSquare guide";
  }).catch(() => {});
})();
