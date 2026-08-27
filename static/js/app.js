(() => {
  "use strict";

  const state = {
    options: null,
    localeById: {},
    difficulty: "neutral",
    session: null,
    messages: [],
    recognizing: false,
    autoplayEnabled: true,
    playbackSession: null,
    playbackMessages: [],
    playbackPlaying: false,
    playbackStopRequested: false,
  };

  const recordState = { active: false, recorder: null, chunks: [], stream: null };

  // ---------- helpers ----------
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  function showToast(msg, ms = 2600) {
    const el = $("#toast");
    el.textContent = msg;
    el.hidden = false;
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => { el.hidden = true; }, ms);
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  async function api(path, opts = {}) {
    const res = await fetch(path, {
      headers: { "Content-Type": "application/json" },
      ...opts,
    });
    let data = null;
    try { data = await res.json(); } catch (e) { /* no body */ }
    if (!res.ok) {
      throw new Error((data && data.error) || `Request failed (${res.status})`);
    }
    return data;
  }

  function setView(name) {
    $$(".view").forEach((v) => v.classList.remove("active"));
    $(`#view-${name}`).classList.add("active");
    $$(".nav-btn").forEach((b) => b.classList.remove("active"));
    if (name === "setup") $("#nav-new").classList.add("active");
    if (name === "history") $("#nav-history").classList.add("active");
    if (name === "history") loadHistory();
    stopAllSpeech();
    if (name !== "call" && recordState.active) stopRecording();
  }

  // ---------- speech: text to speech ----------
  let cachedVoices = [];
  function refreshVoices() {
    if ("speechSynthesis" in window) {
      cachedVoices = window.speechSynthesis.getVoices();
    }
  }
  if ("speechSynthesis" in window) {
    refreshVoices();
    window.speechSynthesis.onvoiceschanged = refreshVoices;
  }

  function pickVoice(langCode) {
    if (!cachedVoices.length) refreshVoices();
    if (!cachedVoices.length) return null;
    const exact = cachedVoices.find((v) => v.lang && v.lang.toLowerCase() === langCode.toLowerCase());
    if (exact) return exact;
    const prefix = langCode.split("-")[0];
    const partial = cachedVoices.find((v) => v.lang && v.lang.toLowerCase().startsWith(prefix));
    return partial || null;
  }

  function speak(text, langCode, { pitch = 1 } = {}) {
    return new Promise((resolve) => {
      if (!("speechSynthesis" in window)) { resolve(); return; }
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = langCode;
      utter.pitch = pitch;
      utter.rate = 1;
      const voice = pickVoice(langCode);
      if (voice) utter.voice = voice;
      utter.onend = resolve;
      utter.onerror = resolve;
      window.speechSynthesis.speak(utter);
    });
  }

  function stopAllSpeech() {
    if ("speechSynthesis" in window) window.speechSynthesis.cancel();
    state.playbackStopRequested = true;
    state.playbackPlaying = false;
  }

  function currentSpeechLang() {
    const localeId = state.session ? state.session.locale : (state.playbackSession && state.playbackSession.locale);
    const locale = localeId && state.localeById[localeId];
    return (locale && locale.speech_lang) || "en-US";
  }

  // ---------- speech: speech to text ----------
  const SpeechRecognitionImpl = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recognizer = null;

  function initRecognizer(langCode) {
    if (!SpeechRecognitionImpl) return null;
    const r = new SpeechRecognitionImpl();
    r.lang = langCode;
    r.interimResults = true;
    r.maxAlternatives = 1;
    r.continuous = false;
    return r;
  }

  function toggleMic() {
    if (!SpeechRecognitionImpl) {
      showToast("Voice input isn't supported in this browser — try Chrome, or just type.");
      return;
    }
    if (state.recognizing) {
      recognizer && recognizer.stop();
      return;
    }
    recognizer = initRecognizer(currentSpeechLang());
    if (!recognizer) return;

    const micBtn = $("#btn-mic");
    const indicator = $("#rec-indicator");
    const input = $("#input-text");

    recognizer.onstart = () => {
      state.recognizing = true;
      micBtn.classList.add("recording");
      indicator.hidden = false;
    };
    recognizer.onend = () => {
      state.recognizing = false;
      micBtn.classList.remove("recording");
      indicator.hidden = true;
    };
    recognizer.onerror = (e) => {
      state.recognizing = false;
      micBtn.classList.remove("recording");
      indicator.hidden = true;
      if (e.error !== "no-speech" && e.error !== "aborted") {
        showToast("Voice input error: " + e.error);
      }
    };
    recognizer.onresult = (event) => {
      let finalText = "";
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const chunk = event.results[i][0].transcript;
        if (event.results[i].isFinal) finalText += chunk;
        else interim += chunk;
      }
      input.value = (finalText || interim).trim();
      if (finalText.trim()) {
        recognizer.stop();
        sendCurrentInput();
      }
    };

    try { recognizer.start(); } catch (e) { /* already started */ }
  }

  // ---------- video recording ----------
  function updateRecordButton() {
    const btn = $("#btn-record");
    if (!btn) return;
    btn.classList.toggle("recording", recordState.active);
    btn.innerHTML = recordState.active ? "⏹ Stop &amp; Save" : "⏺ Record";
  }

  async function toggleRecording() {
    if (recordState.active) {
      stopRecording();
      return;
    }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) {
      showToast("Screen recording isn't supported in this browser — try Chrome or Edge.");
      return;
    }
    let stream;
    try {
      stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
    } catch (e) {
      if (e.name !== "NotAllowedError") showToast("Could not start recording: " + e.message);
      return;
    }
    recordState.stream = stream;
    recordState.chunks = [];
    const mimeType = ["video/webm;codecs=vp9,opus", "video/webm"]
      .find((t) => window.MediaRecorder && MediaRecorder.isTypeSupported(t));
    recordState.recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    recordState.recorder.addEventListener("dataavailable", (e) => {
      if (e.data && e.data.size) recordState.chunks.push(e.data);
    });
    recordState.recorder.addEventListener("stop", saveRecording);
    stream.getVideoTracks()[0].addEventListener("ended", () => {
      if (recordState.active) stopRecording();
    });
    recordState.recorder.start();
    recordState.active = true;
    updateRecordButton();
    showToast("Recording started — choose “This Tab” and enable “Share tab audio” to capture the voice.", 5000);
  }

  function stopRecording() {
    if (recordState.recorder && recordState.recorder.state !== "inactive") recordState.recorder.stop();
    if (recordState.stream) recordState.stream.getTracks().forEach((t) => t.stop());
    recordState.active = false;
    updateRecordButton();
  }

  function saveRecording() {
    if (!recordState.chunks.length) return;
    const blob = new Blob(recordState.chunks, { type: "video/webm" });
    const url = URL.createObjectURL(blob);
    const name = (state.session ? state.session.hotel_name : "call").replace(/[^a-z0-9]+/gi, "-");
    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    const a = document.createElement("a");
    a.href = url;
    a.download = `call-${name}-${stamp}.webm`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
    recordState.chunks = [];
    showToast("Recording saved to your Downloads folder.");
  }

  // ---------- API key setup ----------
  async function checkConfig() {
    try {
      const status = await api("/api/config");
      if (!status.configured) openKeyModal(false);
    } catch (e) { /* ignore — user can still open settings manually */ }
  }

  function openKeyModal(dismissible) {
    $("#key-modal").hidden = false;
    $("#key-input").value = "";
    $("#key-error").hidden = true;
    $("#btn-close-key-modal").hidden = !dismissible;
    $("#key-input").focus();
  }

  function closeKeyModal() {
    $("#key-modal").hidden = true;
  }

  async function saveKey() {
    const input = $("#key-input");
    const btn = $("#btn-save-key");
    const spinner = btn.querySelector(".spinner");
    const errEl = $("#key-error");
    const key = input.value.trim();
    errEl.hidden = true;
    if (!key) {
      errEl.textContent = "Paste your API key first.";
      errEl.hidden = false;
      return;
    }
    btn.disabled = true;
    spinner.hidden = false;
    try {
      await api("/api/config", { method: "POST", body: JSON.stringify({ api_key: key }) });
      closeKeyModal();
      showToast("API key saved.");
    } catch (e) {
      errEl.textContent = e.message;
      errEl.hidden = false;
    } finally {
      btn.disabled = false;
      spinner.hidden = true;
    }
  }

  // ---------- options / setup ----------
  async function loadOptions() {
    state.options = await api("/api/options");
    state.options.locales.forEach((l) => { state.localeById[l.id] = l; });

    const localeSel = $("#opt-locale");
    localeSel.innerHTML = state.options.locales
      .map((l) => `<option value="${l.id}">${l.flag} ${escapeHtml(l.label)}</option>`)
      .join("");

    const hotelSel = $("#opt-hotel");
    hotelSel.innerHTML = state.options.hotel_types
      .map((h) => `<option value="${h.id}">${escapeHtml(h.label)}</option>`)
      .join("");

    const personaSel = $("#opt-persona");
    personaSel.innerHTML = state.options.personas
      .map((p) => `<option value="${p.id}">${escapeHtml(p.label)}</option>`)
      .join("");

    const diffWrap = $("#opt-difficulty");
    diffWrap.innerHTML = state.options.difficulties
      .map((d) => `<button type="button" data-id="${d.id}" class="${d.id === state.difficulty ? "active" : ""}">${escapeHtml(d.label)}</button>`)
      .join("");
    diffWrap.addEventListener("click", (e) => {
      const btn = e.target.closest("button");
      if (!btn) return;
      state.difficulty = btn.dataset.id;
      $$("#opt-difficulty button").forEach((b) => b.classList.toggle("active", b === btn));
    });

    updateHint("#hint-hotel", state.options.hotel_types, hotelSel.value);
    updateHint("#hint-persona", state.options.personas, personaSel.value);
    hotelSel.addEventListener("change", () => updateHint("#hint-hotel", state.options.hotel_types, hotelSel.value));
    personaSel.addEventListener("change", () => updateHint("#hint-persona", state.options.personas, personaSel.value));
  }

  function updateHint(sel, list, id) {
    const item = list.find((x) => x.id === id);
    $(sel).textContent = item ? item.description : "";
  }

  async function startCall() {
    const btn = $("#btn-start");
    const spinner = btn.querySelector(".spinner");
    btn.disabled = true;
    spinner.hidden = false;

    try {
      const session = await api("/api/sessions", {
        method: "POST",
        body: JSON.stringify({
          locale_id: $("#opt-locale").value,
          hotel_type_id: $("#opt-hotel").value,
          persona_id: $("#opt-persona").value,
          difficulty_id: state.difficulty,
        }),
      });
      state.session = session;
      state.messages = [];
      renderBrief(session, "#call-brief", "#brief-title", "#brief-body", "#brief-toggle");
      renderChat();
      setView("call");
      $("#input-text").focus();
    } catch (e) {
      showToast(e.message);
    } finally {
      btn.disabled = false;
      spinner.hidden = true;
    }
  }

  function renderBrief(session, briefSel, titleSel, bodySel, toggleSel) {
    $(titleSel).textContent = `${session.hotel_name} · ${session.persona_label}`;
    $(bodySel).innerHTML = `
      <p><strong>${escapeHtml(session.hotel_name)}</strong> — ${escapeHtml(session.hotel_type_label)}</p>
      <p><strong>Manager:</strong> ${escapeHtml(session.manager_name)} (${escapeHtml(session.persona_label)})</p>
      <p><strong>Locale:</strong> ${escapeHtml(session.locale_label)} &nbsp; <strong>Difficulty:</strong> ${escapeHtml(session.difficulty_id)}</p>
      <p>${escapeHtml(session.scenario_brief)}</p>
    `;
    const briefEl = $(briefSel);
    briefEl.classList.remove("open");
    const toggle = $(toggleSel);
    toggle.onclick = () => briefEl.classList.toggle("open");
  }

  // ---------- chat (live call) ----------
  function bubbleHtml(msg, { readonly = false } = {}) {
    const roleLabel = msg.role === "user" ? "You (rep)" : state.session ? state.session.manager_name : (state.playbackSession && state.playbackSession.manager_name) || "Manager";
    const translationHtml = msg.translation
      ? `<div class="translation" data-mid="${msg.id}">${escapeHtml(msg.translation)}</div>`
      : "";
    return `
      <div class="bubble-row ${msg.role}" data-id="${msg.id}">
        <div class="bubble-label">${escapeHtml(roleLabel)}</div>
        <div class="bubble">${escapeHtml(msg.text)}</div>
        <div class="bubble-actions">
          <button class="mini-btn act-speak" data-id="${msg.id}">🔊 Play</button>
          <button class="mini-btn act-translate" data-id="${msg.id}">🌐 Translate</button>
        </div>
        ${translationHtml}
      </div>
    `;
  }

  function renderChat() {
    const log = $("#chat-log");
    log.innerHTML = state.messages.map((m) => bubbleHtml(m)).join("");
    log.scrollTop = log.scrollHeight;
  }

  function autoResizeTextarea(el) {
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 110) + "px";
  }

  async function sendCurrentInput() {
    const input = $("#input-text");
    const text = input.value.trim();
    if (!text || !state.session) return;
    input.value = "";
    autoResizeTextarea(input);

    const userMsg = { id: `tmp-${Date.now()}`, role: "user", text, translation: null };
    state.messages.push(userMsg);
    renderChat();

    const log = $("#chat-log");
    const typingEl = document.createElement("div");
    typingEl.className = "bubble-row assistant";
    typingEl.innerHTML = `<div class="bubble-label">${escapeHtml(state.session.manager_name)}</div><div class="bubble typing"><span></span><span></span><span></span></div>`;
    log.appendChild(typingEl);
    log.scrollTop = log.scrollHeight;

    $("#btn-send").disabled = true;
    try {
      const reply = await api(`/api/sessions/${state.session.id}/messages`, {
        method: "POST",
        body: JSON.stringify({ text }),
      });
      typingEl.remove();
      state.messages.push(reply);
      renderChat();
      if ($("#opt-autoplay").checked) {
        speak(reply.text, currentSpeechLang());
      }
    } catch (e) {
      typingEl.remove();
      showToast(e.message);
    } finally {
      $("#btn-send").disabled = false;
    }
  }

  async function handleBubbleAction(e, messages, rerender) {
    const speakBtn = e.target.closest(".act-speak");
    const translateBtn = e.target.closest(".act-translate");
    if (speakBtn) {
      const msg = messages.find((m) => String(m.id) === speakBtn.dataset.id);
      if (msg) {
        speakBtn.classList.add("speaking");
        await speak(msg.text, currentSpeechLang(), { pitch: msg.role === "user" ? 1.08 : 0.95 });
        speakBtn.classList.remove("speaking");
      }
      return;
    }
    if (translateBtn) {
      const msg = messages.find((m) => String(m.id) === translateBtn.dataset.id);
      if (!msg) return;
      if (msg.translation) {
        msg.translation = null;
        rerender();
        return;
      }
      translateBtn.textContent = "…";
      try {
        const updated = await api(`/api/messages/${msg.id}/translate`, { method: "POST" });
        msg.translation = updated.translation;
        rerender();
      } catch (err) {
        showToast(err.message);
        translateBtn.textContent = "🌐 Translate";
      }
    }
  }

  // ---------- history / playback ----------
  async function loadHistory() {
    const list = await api("/api/sessions");
    const wrap = $("#history-list");
    $("#history-empty").hidden = list.length > 0;
    wrap.innerHTML = list.map((s) => `
      <div class="history-item" data-id="${s.id}">
        <div class="history-main">
          <div class="history-title">${escapeHtml(s.hotel_name)}</div>
          <div class="history-meta">
            <span class="pill">${escapeHtml(s.locale_label)}</span>
            <span>${escapeHtml(s.hotel_type_label)}</span>
            <span>·</span>
            <span>${escapeHtml(s.persona_label)}</span>
            <span>·</span>
            <span>${s.message_count} msgs</span>
          </div>
        </div>
        <span class="chev-right">›</span>
      </div>
    `).join("");
    $$(".history-item").forEach((el) => {
      el.addEventListener("click", () => openPlayback(el.dataset.id));
    });
  }

  async function openPlayback(sessionId) {
    const session = await api(`/api/sessions/${sessionId}`);
    state.playbackSession = session;
    state.playbackMessages = session.messages;
    renderBrief(session, "#playback-brief", "#playback-title", "#playback-brief-body", "#playback-brief-toggle");
    renderPlaybackLog();
    setView("playback");
  }

  function renderPlaybackLog() {
    const log = $("#playback-log");
    log.innerHTML = state.playbackMessages.map((m) => bubbleHtml(m)).join("");
  }

  async function playWholeConversation() {
    if (!state.playbackMessages.length) return;
    state.playbackPlaying = true;
    state.playbackStopRequested = false;
    $("#btn-play-all").hidden = true;
    $("#btn-stop-all").hidden = false;

    for (const msg of state.playbackMessages) {
      if (state.playbackStopRequested) break;
      const row = $(`#playback-log .bubble-row[data-id="${msg.id}"]`);
      if (row) row.querySelector(".bubble").style.outline = "2px solid var(--accent)";
      await speak(msg.text, currentSpeechLang(), { pitch: msg.role === "user" ? 1.08 : 0.95 });
      if (row) row.querySelector(".bubble").style.outline = "none";
    }

    state.playbackPlaying = false;
    $("#btn-play-all").hidden = false;
    $("#btn-stop-all").hidden = true;
  }

  // ---------- wiring ----------
  document.addEventListener("DOMContentLoaded", async () => {
    try {
      await loadOptions();
    } catch (e) {
      showToast("Could not load options: " + e.message, 5000);
    }
    setView("setup");
    checkConfig();

    $("#nav-new").addEventListener("click", () => setView("setup"));
    $("#nav-history").addEventListener("click", () => setView("history"));
    $("#nav-settings").addEventListener("click", () => openKeyModal(true));
    $("#btn-close-key-modal").addEventListener("click", closeKeyModal);
    $("#btn-save-key").addEventListener("click", saveKey);
    $("#key-input").addEventListener("keydown", (e) => {
      if (e.key === "Enter") { e.preventDefault(); saveKey(); }
    });
    $("#btn-start").addEventListener("click", startCall);
    $("#btn-record").addEventListener("click", toggleRecording);

    $("#btn-mic").addEventListener("click", toggleMic);
    $("#btn-send").addEventListener("click", sendCurrentInput);
    $("#input-text").addEventListener("input", (e) => autoResizeTextarea(e.target));
    $("#input-text").addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendCurrentInput();
      }
    });

    $("#chat-log").addEventListener("click", (e) => handleBubbleAction(e, state.messages, renderChat));
    $("#playback-log").addEventListener("click", (e) => handleBubbleAction(e, state.playbackMessages, renderPlaybackLog));

    $("#btn-play-all").addEventListener("click", playWholeConversation);
    $("#btn-stop-all").addEventListener("click", () => {
      state.playbackStopRequested = true;
      if ("speechSynthesis" in window) window.speechSynthesis.cancel();
      $("#btn-play-all").hidden = false;
      $("#btn-stop-all").hidden = true;
    });
    $("#btn-delete-session").addEventListener("click", async () => {
      if (!state.playbackSession) return;
      if (!confirm("Delete this saved conversation?")) return;
      await api(`/api/sessions/${state.playbackSession.id}`, { method: "DELETE" });
      showToast("Conversation deleted.");
      setView("history");
    });
  });
})();
