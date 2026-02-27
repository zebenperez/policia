// iapol-assistant.fixed.js
// Drop-in replacement for iapol-assistant.js with working backend integration.
// URLs are preserved exactly as in the original file: /agents/assistant/start-voice-turn, /chat, /stt

var stream;
var recorder;
let chunks = []; // kept for backward compatibility, but not used in conversation mode.
var config;

const defaultConfig = {
  assistant_name: 'IAPol',
  welcome_message: '¡Hola! Soy tu asistente para tomar decisiones. Cuéntame qué situación te preocupa y te ayudaré a evaluarla. Puedes hablarme usando el botón de micrófono. 🎙️',
  //high_priority_label: 'Alta',
  //medium_priority_label: 'Media',
  //low_priority_label: 'Baja',
  high_priority_label: 'Riesgo crítico',
  medium_priority_label: 'Revisar',
  low_priority_label: 'Seguro',
  primary_color: '#8b5cf6',
  secondary_color: '#1a1a2e',
  text_color: '#ffffff',
  accent_color: '#d946ef',
  surface_color: '#ffffff'
};

// ---- UI helpers ----
function $(sel) { return window.jQuery ? window.jQuery(sel) : null; }

function escapeHtml(s) {
  return String(s ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function byId(id) {
  return document.getElementById(id);
}

function safeSetText(id, text) {
  const el = byId(id);
  if (el) el.textContent = text;
}

function safeAddClass(id, ...cls) {
  const el = byId(id);
  if (el) el.classList.add(...cls);
}

function safeRemoveClass(id, ...cls) {
  const el = byId(id);
  if (el) el.classList.remove(...cls);
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function getPriorityClass(priority) {
  switch (priority) {
    case 'high': return 'priority-high';
    case 'medium': return 'priority-medium';
    case 'low': return 'priority-low';
    default: return '';
  }
}

function getPriorityLabel(priority, cfg) {
  switch (priority) {
    case 'high': return (cfg.high_priority_label || defaultConfig.high_priority_label);
    case 'medium': return (cfg.medium_priority_label || defaultConfig.medium_priority_label);
    case 'low': return (cfg.low_priority_label || defaultConfig.low_priority_label);
    default: return '';
  }
}

function getPriorityColor(priority) {
  switch (priority) {
    case 'high': return 'bg-red-500';
    case 'medium': return 'bg-amber-500';
    case 'low': return 'bg-emerald-500';
    default: return 'bg-gray-500';
  }
}

function addUserMessage(text) {
  const chatContainer = byId('chat-container');
  if (!chatContainer) return;

  const messageDiv = document.createElement('div');
  messageDiv.className = 'message-enter flex justify-end';
  messageDiv.innerHTML = `
    <div class="max-w-[80%]">
      <div class="bg-violet-500/80 backdrop-blur-sm rounded-2xl rounded-tr-sm px-4 py-3">
        <p class="text-white text-sm leading-relaxed">${escapeHtml(text)}</p>
      </div>
      <span class="text-white/30 text-xs mt-1 block text-right">Ahora</span>
    </div>
  `;
  chatContainer.appendChild(messageDiv);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addAssistantMessage(response, cfg) {
  const chatContainer = byId('chat-container');
  if (!chatContainer) return;

  const messageDiv = document.createElement('div');
  messageDiv.className = 'message-enter flex gap-3';

  const priorityLabel = getPriorityLabel(response.priority, cfg);
  const priorityClass = getPriorityClass(response.priority);
  const priorityColor = getPriorityColor(response.priority);

  const html = marked.parse(response.text);
  /*${escapeHtml(response.text || '')}*/
  messageDiv.innerHTML = `
    <div class="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex-shrink-0 flex items-center justify-center">
      <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z">
        </path>
      </svg>
    </div>
    <div class="flex-1">
      <div class="bg-white/10 backdrop-blur-sm rounded-2xl rounded-tl-sm overflow-hidden">
        <div class="${priorityClass} px-4 py-3">
          <div class="flex items-center gap-2 mb-2">
            <div class="w-2 h-2 rounded-full ${priorityColor}"></div>
            <span class="text-xs font-medium text-white/70">${escapeHtml(priorityLabel)}</span>
          </div>
          <p class="text-white/90 text-sm leading-relaxed">${html} </p>
        </div>
        <div class="px-4 py-3 bg-white/5 border-t border-white/10">
          <p class="text-white/70 text-sm">${escapeHtml(response.advice || '')}</p>
        </div>
      </div>
      <span class="text-white/30 text-xs mt-1 block">Ahora</span>
    </div>
  `;
  chatContainer.appendChild(messageDiv);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function showTypingIndicator() {
  const ti = byId('typing-indicator');
  if (ti) ti.classList.remove('hidden');
  const cc = byId('chat-container');
  if (cc) cc.scrollTop = cc.scrollHeight;
}

function hideTypingIndicator() {
  const ti = byId('typing-indicator');
  if (ti) ti.classList.add('hidden');
}

/*function speakText(text, lang = "es-ES") {
  try {
    if (!text) return;
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(String(text));
    u.lang = lang;
    speechSynthesis.speak(u);
  } catch (e) {
    // no-op (TTS puede fallar según navegador)
    console.warn("TTS error:", e);
  }
}*/
function speakText(text, lang = "es-ES") {
  if (!text) return;

  speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(String(text));
  utterance.lang = lang;

  const voices = speechSynthesis.getVoices();

  // Buscar una voz en español que suene mejor
  const preferredVoice = voices.find(v =>
    v.lang.startsWith("es") && v.name.includes("Google")
  ) || voices.find(v =>
    v.lang.startsWith("es")
  );

  if (preferredVoice) {
    utterance.voice = preferredVoice;
  }

  // Ajustes de naturalidad
  utterance.rate = 0.95;   // velocidad (1 es normal)
  //utterance.pitch = 1;     // tono (1 es normal)
  utterance.volume = 1;    // volumen

  speechSynthesis.speak(utterance);
}

// ---- Backend helpers ----
function ensureSessionId() {
  const KEY = "iapol_session_id";
  let sid = localStorage.getItem(KEY);
  if (!sid) {
    sid = (crypto && crypto.randomUUID) ? crypto.randomUUID() : String(Date.now()) + "-" + Math.random().toString(16).slice(2);
    localStorage.setItem(KEY, sid);
  }
  return sid;
}

/**
 * Normaliza la respuesta del backend a la forma esperada por addAssistantMessage():
 * { priority: 'high'|'medium'|'low', text: string, advice: string }
 */
function normalizeAssistantResponse(payload) {
  // payload puede ser:
  // - string
  // - {answer: "..."} o {answer: {priority,text,advice}}
  // - {response: {priority,text,advice}}
  // - {priority,text,advice}
  if (payload == null) {
    return { priority: "medium", text: "", advice: "" };
  }

  if (typeof payload === "string") {
    return { priority: "medium", text: payload, advice: "" };
  }

  // Si viene un objeto "respuesta" en campos comunes:
  const candidate =
    payload.response ??
    payload.answer ??
    payload.assistant ??
    payload;

  if (typeof candidate === "string") {
    return { priority: "medium", text: candidate, advice: "" };
  }

  if (candidate && typeof candidate === "object") {
    const priority = candidate.priority || payload.priority || "medium";
    const text = candidate.text || payload.text || candidate.message || "";
    const advice = candidate.advice || payload.advice || candidate.recommendation || "";
    return { priority, text, advice };
  }

  return { priority: "medium", text: String(candidate), advice: "" };
}

async function postChat(text, mode) {
  // Mantiene URL y forma de request similares a las del archivo original
  const session_id = ensureSessionId();

  //apiChatUrl = "/agents/chat-with-llm"; // DO NOT CHANGE
  apiChatUrl = "/assistant/chat-with-llm"; // DO NOT CHANGE
  form = new FormData();
  const report_id = byId('report-id') ? byId('report-id').value : null;
  // Append report_id, csrfmiddlewaretoken if available, and message
  form.append("report_id", report_id);
  form.append("message", text);
  form.append("mode", mode);
  // Add csrftoken if available
  const csrftoken = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
  if (csrftoken) {
    form.append("csrfmiddlewaretoken", csrftoken.split('=')[1]);
  }

  console.log("Posting chat message to backend:", { report_id, text });
  const resp = await fetch(apiChatUrl, {
    method: "POST",
    body: form
  });
  return await resp.json();
}

// ---- Voice conversation mode (one tap to start/stop) ----
let voiceSession = null;
let voiceUptimeTimer = null;
let voiceUptimeSeconds = 0;

function setMicUiActive(active) {
  if (active) {
    safeRemoveClass('recording-indicator', 'hidden');
    safeAddClass('mic-icon', 'hidden');
    safeRemoveClass('stop-icon', 'hidden');
    safeRemoveClass('mic-pulse', 'hidden');

    const btn = byId('mic-btn');
    if (btn) {
      btn.classList.add('bg-red-500', 'from-red-500', 'to-red-600');
      btn.classList.remove('from-fuchsia-500', 'to-violet-600');
    }
    safeSetText('mic-instruction', 'Escuchando... Toca para detener');
  } else {
    safeAddClass('recording-indicator', 'hidden');
    safeRemoveClass('mic-icon', 'hidden');
    safeAddClass('stop-icon', 'hidden');
    safeAddClass('mic-pulse', 'hidden');

    const btn = byId('mic-btn');
    if (btn) {
      btn.classList.remove('bg-red-500', 'from-red-500', 'to-red-600');
      btn.classList.add('from-fuchsia-500', 'to-violet-600');
    }
    safeSetText('mic-instruction', 'Toca el micrófono para comenzar');
    safeSetText('recording-time', '0:00');
  }
}

function startUptimeTimer() {
  stopUptimeTimer();
  voiceUptimeSeconds = 0;
  safeSetText('recording-time', formatTime(voiceUptimeSeconds));
  voiceUptimeTimer = setInterval(() => {
    voiceUptimeSeconds += 1;
    safeSetText('recording-time', formatTime(voiceUptimeSeconds));
  }, 1000);
}

function stopUptimeTimer() {
  if (voiceUptimeTimer) clearInterval(voiceUptimeTimer);
  voiceUptimeTimer = null;
  voiceUptimeSeconds = 0;
}

async function toggleVoiceConversation(cfg) {
  if (voiceSession) {
    // Stop conversation mode
    try { speechSynthesis.cancel(); } catch (_) { }
    await voiceSession.stop();
    voiceSession = null;
    hideTypingIndicator();
    stopUptimeTimer();
    setMicUiActive(false);
    return;
  }

  // Start conversation mode
  setMicUiActive(true);
  startUptimeTimer();

  // Captura config "viva" por si cambia desde elementSdk
  const getLiveConfig = () => window.elementSdk?.config || cfg || defaultConfig;

  try {
    voiceSession = await startBackendMode({
      //apiUrl: "/agents/assistant/start-voice-turn", // DO NOT CHANGE
      apiUrl: "/assistant/start-voice-turn", // DO NOT CHANGE
      language: "es",
      onStateChange: (s) => {
        // UI/UX: typing indicator cuando el backend está procesando
        if (s === "PROCESSING") showTypingIndicator();
        else hideTypingIndicator();
      },
      onTurn: (data) => {
        const liveCfg = getLiveConfig();

        // transcript -> mensaje de usuario
        const transcript = (data && (data.transcript || data.text || data.user_text)) ? (data.transcript || data.text || data.user_text) : "";
        if (transcript) addUserMessage(`🎙️ "${transcript}"`);

        // respuesta del asistente
        const assistant = normalizeAssistantResponse(data);
        addAssistantMessage(assistant, liveCfg);

        // TTS: pronunciar lo más importante
        // const spoken = [assistant.text, assistant.advice].filter(Boolean).join(" ");
        // speakText(spoken, "es-ES");
      },
      onError: (err) => {
        console.error(err);
        addAssistantMessage(
          { priority: "low", text: "No he podido procesar el audio.", advice: "Revisa permisos del micrófono o tu conexión, e inténtalo de nuevo." },
          getLiveConfig()
        );
      }
    });
  } catch (e) {
    // Si falla el arranque, vuelve a estado idle
    voiceSession = null;
    stopUptimeTimer();
    setMicUiActive(false);
    throw e;
  }
}

// ---- Text messages ----
async function sendTextMessage(cfg) {
  const input = byId('text-input');
  if (!input) return;

  const text = (input.value || "").trim();
  if (!text) return;

  const liveCfg = window.elementSdk?.config || cfg || defaultConfig;

  addUserMessage(text);
  input.value = '';
  if (window.jQuery) window.jQuery('#send-btn').prop('disabled', true);

  showTypingIndicator();
  try {
    const data = await postChat(text, input.dataset.mode);

    // Normaliza y renderiza
    const assistant = normalizeAssistantResponse(data);
    hideTypingIndicator();
    addAssistantMessage(assistant, liveCfg);

    byId("mic-btn").style.display = "none";
    byId("btn-stop-speak").style.display = "block";
    //const spoken = [assistant.text, assistant.advice].filter(Boolean).join(" ");
    const spoken = assistant.text;
    speakText(spoken, "es-ES");
  } catch (e) {
    hideTypingIndicator();
    console.error(e);
    addAssistantMessage(
      { priority: "low", text: "No he podido enviar el mensaje.", advice: "Inténtalo de nuevo en unos segundos." },
      liveCfg
    );
  }
}

// ---- elementSdk integration ----
async function onConfigChange(cfg) {
  // Update assistant name
  const nameEl = byId('assistant-name');
  if (nameEl) nameEl.textContent = cfg.assistant_name || defaultConfig.assistant_name;

  // Update welcome message
  const welcomeEl = byId('welcome-text');
  if (welcomeEl) welcomeEl.textContent = cfg.welcome_message || defaultConfig.welcome_message;

  // Update priority legend labels
  const legendHigh = byId('legend-high');
  const legendMedium = byId('legend-medium');
  const legendLow = byId('legend-low');

  if (legendHigh) legendHigh.textContent = cfg.high_priority_label || defaultConfig.high_priority_label;
  if (legendMedium) legendMedium.textContent = cfg.medium_priority_label || defaultConfig.medium_priority_label;
  if (legendLow) legendLow.textContent = cfg.low_priority_label || defaultConfig.low_priority_label;
}

function mapToCapabilities(cfg) {
  return {
    recolorables: [],
    borderables: [],
    fontEditable: undefined,
    fontSizeable: undefined
  };
}

function mapToEditPanelValues(cfg) {
  return new Map([
    ['assistant_name', cfg.assistant_name || defaultConfig.assistant_name],
    ['welcome_message', cfg.welcome_message || defaultConfig.welcome_message],
    ['high_priority_label', cfg.high_priority_label || defaultConfig.high_priority_label],
    ['medium_priority_label', cfg.medium_priority_label || defaultConfig.medium_priority_label],
    ['low_priority_label', cfg.low_priority_label || defaultConfig.low_priority_label]
  ]);
}

// Initialize element SDK (si existe)
if (window.elementSdk) {
  window.elementSdk.init({
    defaultConfig,
    onConfigChange,
    mapToCapabilities,
    mapToEditPanelValues
  });
}

// ---- Backend voice-turn engine ----
/**
 * startBackendMode()
 * One-tap conversation mode: VAD-based turn detection + POST audio to backend.
 *
 * It calls cfg.onTurn(data) once per completed user turn.
 *
 * URLs preserved:
 *   - cfg.apiUrl defaults to "/agents/assistant/start-voice-turn"
 */
async function startBackendMode(options = {}) {
  const cfg = {
    //apiUrl: "/agents/assistant/start-voice-turn",
    apiUrl: "/assistant/start-voice-turn",
    language: "es",
    startThreshold: 0.000,
    stopThreshold: 0.012,
    minSpeechMs: 250,
    silenceMs: 800,
    maxTurnMs: 20000,
    vadFps: 30,
    onStateChange: () => { },
    onTurn: () => { },
    onError: (err) => console.error(err),
    ...options,
  };

  const State = {
    IDLE: "IDLE",
    LISTENING: "LISTENING",
    RECORDING: "RECORDING",
    PROCESSING: "PROCESSING",
    STOPPED: "STOPPED",
  };

  let state = State.IDLE;
  const setState = (s) => {
    state = s;
    try { cfg.onStateChange(s); } catch (_) { }
  };

  const STORAGE_KEY = "voice_conversation_id";
  let conversationId = localStorage.getItem(STORAGE_KEY) || "";

  // 1) Get mic (must be called after user gesture)
  let mediaStream;
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true }
    });
  } catch (e) {
    cfg.onError(new Error("No se pudo acceder al micrófono. Revisa permisos."));
    throw e;
  }

  // 2) VAD via WebAudio Analyser
  const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  const sourceNode = audioCtx.createMediaStreamSource(mediaStream);
  const analyser = audioCtx.createAnalyser();
  analyser.fftSize = 2048;
  sourceNode.connect(analyser);

  const buffer = new Float32Array(analyser.fftSize);

  let vadTimer = null;
  let voiceActive = false;
  let voiceStartAt = 0;
  let silenceSince = 0;

  let mediaRecorder = null;
  let turnChunks = [];
  let turnStartedAt = 0;
  let turnInFlight = false;

  function buildRecorder() {
    turnChunks = [];
    const mimeType = "audio/webm;codecs=opus";
    const r = new MediaRecorder(mediaStream, { mimeType });

    r.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) turnChunks.push(e.data);
    };
    r.onerror = (e) => cfg.onError(e);
    return r;
  }

  async function stopRecorder() {
    if (!mediaRecorder) return;
    if (mediaRecorder.state === "inactive") return;

    await new Promise((resolve) => {
      mediaRecorder.onstop = () => resolve();
      try { mediaRecorder.stop(); } catch (_) { resolve(); }
    });
  }

  async function sendTurn(blob) {
    const form = new FormData();
    if (conversationId) form.append("conversation_id", conversationId);
    form.append("language", cfg.language);
    form.append("audio", blob, "turn.webm");
    // Add csrftoken if available
    const csrftoken = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
    if (csrftoken) {
      form.append("csrfmiddlewaretoken", csrftoken.split('=')[1]);
    }

    const resp = await fetch(cfg.apiUrl, { method: "POST", body: form });

    if (!resp.ok) {
      const txt = await resp.text().catch(() => "");
      throw new Error(`Backend error ${resp.status}: ${txt || resp.statusText}`);
    }

    const data = await resp.json();

    // tolerante: si no viene ok, pero hay contenido, lo dejamos pasar.
    if (data && data.ok === false) {
      throw new Error(data.detail || "Respuesta del backend no ok.");
    }

    if (data && data.conversation_id) {
      conversationId = data.conversation_id;
      localStorage.setItem(STORAGE_KEY, conversationId);
    }

    return data;
  }

  async function finishTurn() {
    if (!mediaRecorder || mediaRecorder.state === "inactive") return;
    if (turnInFlight) return; // evita doble envío por loops

    turnInFlight = true;
    setState(State.PROCESSING);

    try {
      await stopRecorder();
      const blob = new Blob(turnChunks, { type: "audio/webm" });

      // reset VAD flags for next turn
      voiceActive = false;
      voiceStartAt = 0;
      silenceSince = 0;

      const data = await sendTurn(blob);

      // callback a UI
      try { cfg.onTurn(data || {}); } catch (e) { cfg.onError(e); }

      setState(State.LISTENING);
    } catch (e) {
      cfg.onError(e);
      setState(State.LISTENING);
    } finally {
      mediaRecorder = null;
      turnChunks = [];
      turnInFlight = false;
    }
  }

  function startTurn() {
    if (turnInFlight) return;
    if (state === State.PROCESSING) return;

    mediaRecorder = buildRecorder();
    turnStartedAt = performance.now();
    try {
      mediaRecorder.start();
      setState(State.RECORDING);
    } catch (e) {
      cfg.onError(e);
      mediaRecorder = null;
      setState(State.LISTENING);
    }
  }

  function vadLoop() {
    if (state === State.STOPPED) return;
    if (state === State.PROCESSING) return;

    analyser.getFloatTimeDomainData(buffer);

    let sum = 0;
    for (let i = 0; i < buffer.length; i++) sum += buffer[i] * buffer[i];
    const rms = Math.sqrt(sum / buffer.length);

    const now = performance.now();

    if (!voiceActive) {
      if (rms >= cfg.startThreshold) {
        if (!voiceStartAt) voiceStartAt = now;
        if (now - voiceStartAt >= cfg.minSpeechMs) {
          voiceActive = true;
          silenceSince = 0;
          startTurn();
        }
      } else {
        voiceStartAt = 0;
      }
    } else {
      if (rms <= cfg.stopThreshold) {
        if (!silenceSince) silenceSince = now;
        if (now - silenceSince >= cfg.silenceMs) {
          finishTurn();
        }
      } else {
        silenceSince = 0;
      }

      if (mediaRecorder && mediaRecorder.state !== "inactive") {
        const dur = now - turnStartedAt;
        if (dur >= cfg.maxTurnMs) {
          finishTurn();
        }
      }
    }
  }

  setState(State.LISTENING);
  vadTimer = setInterval(vadLoop, Math.max(10, Math.floor(1000 / cfg.vadFps)));

  async function stop() {
    setState(State.STOPPED);

    try {
      if (vadTimer) clearInterval(vadTimer);
      vadTimer = null;

      try { speechSynthesis.cancel(); } catch (_) { }

      await stopRecorder();

      if (mediaStream) mediaStream.getTracks().forEach((t) => t.stop());
      try { await audioCtx.close(); } catch (_) { }
    } catch (e) {
      cfg.onError(e);
    }
  }

  function resetConversation() {
    conversationId = "";
    localStorage.removeItem(STORAGE_KEY);
  }

  return {
    stop,
    resetConversation,
    getState: () => state,
    getConversationId: () => conversationId,
  };
}

// ---- Hook UI events ----
if (window.jQuery) {
  window.jQuery(document).ready(function () {
    window.jQuery("#mic-btn").on("click", async function () {
      const cfg = window.elementSdk?.config || defaultConfig;
      try {
        await toggleVoiceConversation(cfg);
      } catch (e) {
        console.error(e);
        setMicUiActive(false);
        stopUptimeTimer();
      }
    });

    window.jQuery('#text-input').on('input', function () {
      const hasText = window.jQuery(this).val().trim().length > 0;
      window.jQuery('#send-btn').prop('disabled', !hasText);
    });

    window.jQuery('#send-btn').on('click', function () {
      const cfg = window.elementSdk?.config || defaultConfig;
      sendTextMessage(cfg);
    });

    window.jQuery('#text-input').on('keypress', function (e) {
      if (e.key === 'Enter') {
        const cfg = window.elementSdk?.config || defaultConfig;
        sendTextMessage(cfg);
      }
    });

    window.jQuery('#btn-stop-speak').on('click', function (e) {
        byId("btn-stop-speak").style.display = "none";
        byId("mic-btn").style.display = "block";
        speechSynthesis.cancel();
    });

  });
} else {
  // Minimal non-jQuery fallback for environments without jQuery
  document.addEventListener("DOMContentLoaded", () => {
    const micBtn = byId("mic-btn");
    if (micBtn) {
      micBtn.addEventListener("click", async () => {
        const cfg = window.elementSdk?.config || defaultConfig;
        try { await toggleVoiceConversation(cfg); } catch (e) { console.error(e); }
      });
    }

    const sendBtn = byId("send-btn");
    if (sendBtn) {
      sendBtn.addEventListener("click", () => {
        const cfg = window.elementSdk?.config || defaultConfig;
        sendTextMessage(cfg);
      });
    }

    const textInput = byId("text-input");
    if (textInput) {
      textInput.addEventListener("input", () => {
        const hasText = (textInput.value || "").trim().length > 0;
        if (sendBtn) sendBtn.disabled = !hasText;
      });
      textInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
          const cfg = window.elementSdk?.config || defaultConfig;
          sendTextMessage(cfg);
        }
      });
    }
  });
}
