let phone = "08030000001";
let phones = ["08030000001", "08030000002", "08030000003"];
let conversationId = null;
let voiceMode = false;
let voiceSessionId = null;
let conversationHistory = [];
let currentLanguage = "en";
let browserRecognition = null;

function storageKey(customerPhone = phone) {
  return `livebox-conversation-v0.4:${customerPhone}`;
}

function saveConversation() {
  try {
    localStorage.setItem(storageKey(), JSON.stringify({ conversationId, messages: conversationHistory }));
  } catch (error) {
    // The chat should continue working if browser storage is unavailable or full.
  }
}

function restoreConversation(customerPhone = phone) {
  let saved;
  try {
    saved = JSON.parse(localStorage.getItem(storageKey(customerPhone)) || "null");
  } catch (error) {
    saved = null;
  }
  conversationHistory = Array.isArray(saved?.messages) ? saved.messages : [];
  conversationId = saved?.conversationId || null;
  const messages = document.getElementById("msgs");
  messages.replaceChildren();
  for (const message of conversationHistory) {
    messages.appendChild(renderMessage(message.text, message.kind, message.meta || {}));
  }
  messages.scrollTop = 99999;
  updateHistoryPanel();
}

function getSpeechRecognitionConstructor() {
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

function updateAudioStatus(message) {
  const status = document.getElementById("audio-status");
  if (status) status.textContent = message;
}

function browserSpeechLocale(language) {
  return ({ pid: "en-NG", yo: "yo-NG", ha: "ha-NG", ig: "ig-NG", en: "en-NG" })[language] || "en-NG";
}

function speakAudio(text, language = currentLanguage, force = false) {
  if (!text || (!voiceMode && !force)) return;
  if (!("speechSynthesis" in window) || typeof SpeechSynthesisUtterance === "undefined") {
    updateAudioStatus("Spoken audio is not supported by this browser");
    return;
  }

  const synth = window.speechSynthesis;
  synth.cancel();
  synth.resume();
  const utterance = new SpeechSynthesisUtterance(text);
  const locale = browserSpeechLocale(language);
  utterance.lang = locale;
  utterance.rate = 0.96;
  utterance.pitch = 1;

  const voices = synth.getVoices();
  const requested = locale.toLowerCase();
  const languagePrefix = requested.split("-")[0];
  const voice = voices.find((item) => item.lang.toLowerCase() === requested)
    || voices.find((item) => item.lang.toLowerCase().startsWith(`${languagePrefix}-`))
    || voices.find((item) => item.default)
    || voices[0];
  if (voice) utterance.voice = voice;

  utterance.onstart = () => updateAudioStatus(`Speaking (${language || "en"})`);
  utterance.onend = () => updateAudioStatus("Voice output ready");
  utterance.onerror = (event) => updateAudioStatus(`Audio error: ${event.error || "could not speak"}`);
  synth.speak(utterance);
  updateAudioStatus("Preparing voice output…");
}

function prepareBrowserAudio() {
  if (!("speechSynthesis" in window)) {
    updateAudioStatus("Spoken audio is not supported by this browser");
    return;
  }
  window.speechSynthesis.getVoices();
  window.speechSynthesis.resume();
  updateAudioStatus("Voice output ready");
}

async function loadUsers() {
  document.getElementById("users").innerHTML = phones
    .map((p) => `<div class="user ${p === phone ? "active" : ""}" onclick="choose('${p}')">${p}</div>`)
    .join("");

  const customer = await fetch(`http://127.0.0.1:8000/api/customer/${phone}`).then((res) => res.json());
  document.getElementById("name").textContent = customer.name;
  document.getElementById("phone").textContent = phone;
  document.getElementById("lang-badge").textContent = "en";
  const consentControl = document.getElementById("consent-control");
  consentControl.innerHTML = `<p>Marketing offers: <b>${customer.marketing_consent ? "Allowed" : "Off"}</b></p><button onclick="toggleMarketingConsent(${!customer.marketing_consent})">${customer.marketing_consent ? "Turn offers off" : "Allow offers"}</button>`;
}

async function toggleMarketingConsent(marketingConsent) {
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/customer/${phone}/consent`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ marketing_consent: marketingConsent }),
    });
    if (!response.ok) throw new Error("Consent update failed");
    await loadUsers();
  } catch (error) {
    say("I couldn't update the marketing preference. Please try again.");
  }
}

async function choose(p) {
  saveConversation();
  phone = p;
  restoreConversation(phone);
  await loadUsers();
  if (!conversationHistory.length) say("Hello. I'm LiveBox AI. How can I help you today?");
  updateVoiceIndicator();
}

function renderMessage(text, kind, meta = {}) {
  const el = document.createElement("div");
  el.className = `m ${kind}`;
  
  const content = document.createElement("div");
  content.textContent = text;
  el.appendChild(content);
  
  if (meta.language || meta.intent) {
    const metaEl = document.createElement("div");
    metaEl.className = "meta";
    const parts = [];
    if (meta.language) parts.push(`Lang: ${meta.language}`);
    if (meta.intent) parts.push(`Intent: ${meta.intent}`);
    if (meta.action) parts.push(`Tool: ${meta.action}`);
    if (meta.escalate) parts.push("Escalation: YES");
    metaEl.textContent = parts.join(" | ");
    el.appendChild(metaEl);
  }
  
  return el;
}

function add(text, kind, meta = {}) {
  const message = { text, kind, meta, timestamp: new Date().toISOString() };
  document.getElementById("msgs").appendChild(renderMessage(text, kind, meta));
  document.getElementById("msgs").scrollTop = 99999;
  conversationHistory.push(message);
  saveConversation();
  updateHistoryPanel();
}

function say(text, meta = {}) {
  add(text, "ai", meta);
  updateLanguageBadge(meta.language);
  if (meta.language) currentLanguage = meta.language;
  speakAudio(text, currentLanguage);
}

function updateLanguageBadge(lang) {
  if (lang) {
    document.getElementById("lang-badge").textContent = lang;
    currentLanguage = lang;
  }
}

function updateVoiceIndicator() {
  const indicator = document.getElementById("voice-indicator");
  const btn = document.getElementById("voice-btn");
  if (voiceMode) {
    indicator.textContent = "VOICE ON";
    indicator.className = "voice-indicator on";
    btn.classList.add("active");
  } else {
    indicator.textContent = "VOICE OFF";
    indicator.className = "voice-indicator off";
    btn.classList.remove("active");
  }
  document.getElementById("barge-btn").disabled = !voiceMode || !voiceSessionId;
  document.getElementById("silence-btn").disabled = !voiceMode || !voiceSessionId;
  document.getElementById("speak-btn").disabled = !voiceMode || !voiceSessionId || !getSpeechRecognitionConstructor();
  if (voiceMode && !getSpeechRecognitionConstructor()) {
    document.getElementById("speak-btn").title = "Voice recognition is unavailable here; type what the customer says.";
  }
}

function toggleVoice() {
  voiceMode = !voiceMode;
  if (voiceMode) {
    prepareBrowserAudio();
    startVoiceSession();
  } else {
    endVoiceSession();
  }
  updateVoiceIndicator();
}

async function startVoiceSession() {
  try {
    const response = await fetch("http://127.0.0.1:8000/api/voice/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone }),
    });
    const json = await response.json();
    voiceSessionId = json.session_id;
    say(json.greeting, { language: json.language });
    updateVoiceIndicator();
  } catch (error) {
    say("Failed to start voice session. Is backend running?");
    voiceMode = false;
    updateVoiceIndicator();
  }
}

async function endVoiceSession() {
  if (!voiceSessionId) return;
  try {
    const response = await fetch("http://127.0.0.1:8000/api/voice/end", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: voiceSessionId }),
    });
    const result = await response.json();
    voiceSessionId = null;
    add(result.farewell || "Call ended. Thank you for calling LiveBox.", "ai");
    speakAudio(result.farewell || "Call ended. Thank you for calling LiveBox.", currentLanguage, true);
  } catch (error) {
    say("Failed to end voice session.");
  }
}

async function sendVoice(text) {
  if (!voiceSessionId) return;
  try {
    const response = await fetch("http://127.0.0.1:8000/api/voice/speech", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: voiceSessionId, text }),
    });
    const json = await response.json();
    say(json.reply, { language: json.language, intent: json.intent, action: json.action });
    if (json.proactive_offer) {
      say(`[Proactive Offer: ${json.proactive_offer}]`, { language: json.language });
    }
  } catch (error) {
    say("Voice input failed.");
  }
}

async function simulateBargeIn() {
  if (!voiceSessionId) return;
  if ("speechSynthesis" in window) window.speechSynthesis.cancel();
  try {
    const response = await fetch("http://127.0.0.1:8000/api/voice/barge", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: voiceSessionId }),
    });
    const json = await response.json();
    if (json.reply) say(json.reply, { language: json.language });
  } catch (error) {
    say("Could not interrupt the mock voice response.");
  }
}

function startBrowserSpeechInput() {
  const Recognition = getSpeechRecognitionConstructor();
  if (!Recognition) {
    updateAudioStatus("Microphone recognition is unavailable; type the customer's words instead");
    return;
  }
  if (browserRecognition) browserRecognition.abort();

  browserRecognition = new Recognition();
  browserRecognition.lang = browserSpeechLocale(currentLanguage);
  browserRecognition.continuous = false;
  browserRecognition.interimResults = false;
  browserRecognition.maxAlternatives = 1;
  browserRecognition.onstart = () => updateAudioStatus("Listening…");
  browserRecognition.onresult = (event) => {
    const transcript = event.results?.[0]?.[0]?.transcript?.trim();
    if (transcript) {
      document.getElementById("q").value = transcript;
      send();
    }
  };
  browserRecognition.onerror = (event) => {
    updateAudioStatus(`Microphone error: ${event.error || "check microphone permission"}`);
  };
  browserRecognition.onend = () => {
    browserRecognition = null;
    if (voiceMode) updateAudioStatus("Voice output ready");
  };
  try {
    browserRecognition.start();
  } catch (error) {
    browserRecognition = null;
    updateAudioStatus("Could not start the microphone; check browser permissions");
  }
}

async function simulateSilence() {
  if (!voiceSessionId) return;
  try {
    const response = await fetch("http://127.0.0.1:8000/api/voice/no-input", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: voiceSessionId }),
    });
    const json = await response.json();
    say(json.reply, { language: json.language });
  } catch (error) {
    say("Could not send the mock silence prompt.");
  }
}

async function send() {
  const value = document.getElementById("q").value.trim();
  if (!value) return;
  document.getElementById("q").value = "";
  add(value, "me");

  if (voiceMode && voiceSessionId) {
    await sendVoice(value);
    return;
  }

  try {
    const response = await fetch("http://127.0.0.1:8000/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone, message: value, conversation_id: conversationId }),
    });
    const json = await response.json();
    conversationId = json.conversation_id;
    say(json.reply, { language: json.language, intent: json.intent, action: json.action, escalate: json.escalate });
    if (json.proactive_offer) {
      say(`[Proactive Offer: ${json.proactive_offer}]`, { language: json.language });
    }
  } catch (error) {
    say("Backend is not running. Start it using README.md.");
  }
}

function updateHistoryPanel() {
  const panel = document.getElementById("history-msgs");
  panel.replaceChildren();
  for (const message of conversationHistory) {
    const item = document.createElement("div");
    item.className = `hm ${message.kind}`;
    const text = document.createElement("div");
    text.textContent = message.text;
    item.appendChild(text);

    const metadata = document.createElement("div");
    metadata.className = "meta";
    const meta = message.meta || {};
    metadata.textContent = [
      meta.language ? `Lang: ${meta.language}` : "",
      meta.intent ? `Intent: ${meta.intent}` : "",
      meta.action ? `Tool: ${meta.action}` : "",
      meta.escalate ? "Escalation: YES" : "",
    ].filter(Boolean).join(" | ");
    item.appendChild(metadata);
    panel.appendChild(item);
  }
  panel.scrollTop = 99999;
}

window.choose = choose;
window.toggleMarketingConsent = toggleMarketingConsent;
window.toggleVoice = toggleVoice;
window.simulateBargeIn = simulateBargeIn;
window.simulateSilence = simulateSilence;
window.startBrowserSpeechInput = startBrowserSpeechInput;
window.send = send;
loadUsers();
restoreConversation(phone);
if (!conversationHistory.length) say("Hello. I'm LiveBox AI. How can I help you today?");
if ("speechSynthesis" in window) {
  window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
  updateAudioStatus("Audio ready — turn on Voice to hear responses");
} else {
  updateAudioStatus("Spoken audio is not supported by this browser");
}
