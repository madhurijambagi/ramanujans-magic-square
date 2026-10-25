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
        <div class="companion-options"><select id="companion-game" aria-label="Game"><option>Ramanujan's Magic Square</option></select><select id="companion-language" aria-label="Reply language"><option value="en">English</option><option value="kn">Kannada</option></select></div>
        <div class="companion-log" id="companion-log" role="log" aria-live="polite"></div><div class="companion-status" id="companion-status" role="status"></div>
        <form class="companion-form" id="companion-form"><textarea id="companion-input" maxlength="500" rows="2" placeholder="Ask about MagicSquare or gaming…" aria-label="Message"></textarea><div><button type="submit" class="btn">Send</button></div></form>
        <div class="companion-footer"><span id="companion-privacy">Keep personal information private.</span><button type="button" id="companion-clear">Clear history</button></div>
      </section>
    </div>`;
  document.body.appendChild(root);

  const $ = (selector) => root.querySelector(selector);
  const launch = $(".companion-launch");
  const backdrop = $(".companion-backdrop");
  const panel = $(".companion-panel");
  const log = $("#companion-log");
  const input = $("#companion-input");
  const status = $("#companion-status");
  const language = $("#companion-language");
  let languageManuallyChosen = false;
  language.value = localStorage.getItem("squareverse-chat-language") === "kn" ? "kn" : "en";

  function setOpen(which) {
    const open = Boolean(which);
    backdrop.hidden = !open;
    panel.hidden = which !== "chat";
    launch.setAttribute("aria-expanded", String(open));
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
          send(suggestion.question || shortcuts[label] || label);
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

  async function send(question) {
    const cleanQuestion = String(question || "").trim();
    if (!cleanQuestion) return;
    addMessage(cleanQuestion, "user");
    status.textContent = "Thinking…";
    try {
      const result = await api.post("/api/chatbot", {
        question: cleanQuestion, game_title: $("#companion-game").value,
        language: language.value, game_context: snapshot()
      });
      if (result.language) {
        language.value = result.language;
        localStorage.setItem("squareverse-chat-language", result.language);
      }
      addMessage(result.answer, "assistant", result.assistant_message_id, result.suggestions || []);
      status.textContent = result.ai ? "AI-powered MagicSquare guide" : "Curated MagicSquare guide";
    } catch (error) {
      status.textContent = error.message;
    }
  }

  async function openChat() {
    setOpen("chat");
    if (!log.childElementCount) await loadHistory();
    input.focus();
  }

  launch.addEventListener("click", openChat);
  $(".companion-close").addEventListener("click", () => setOpen(null));
  backdrop.addEventListener("click", (event) => { if (event.target === backdrop) setOpen(null); });
  document.addEventListener("keydown", (event) => { if (event.key === "Escape" && !backdrop.hidden) setOpen(null); });
  $("#companion-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const question = input.value;
    input.value = "";
    send(question);
  });
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
  api.get("/api/chatbot/status").then((info) => {
    $("#companion-mode").textContent = info.ai_enabled
      ? `AI-powered MagicSquare guide · ${info.model}`
      : "Curated MagicSquare guide";
    if (info.ai_enabled) {
      $("#companion-privacy").textContent = "AI sends your current question, language and relevant guide excerpts to OpenAI. Avoid personal details.";
    }
  }).catch(() => { $("#companion-mode").textContent = "MagicSquare guide"; });
  }).catch(() => {});
})();
