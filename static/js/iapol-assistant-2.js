let mediaRecorder;
let audioChunks = [];
let isRecording = false;

function byId(id) {
  return document.getElementById(id);
}

function escapeHtml(s) {
  return String(s ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function getPriorityClass(priority) {
    switch (priority) {
        case 'high': return 'priority-high';
        case 'medium': return 'priority-medium';
        case 'low': return 'priority-low';
        default: return '';
    }
}

function getPriorityLabel(priority) {
    switch (priority) {
        case 'high': return 'Riesgo crítico';
        case 'medium': return 'Revisar';
        case 'low': return 'Seguro';
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

    const template = document.getElementById('user-message-template');
    const clone = template.content.cloneNode(true);

    // Insertar texto de forma segura
    clone.querySelector('.message-text').textContent = text;

    chatContainer.appendChild(clone);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addAssistantMessage(response, init=false) {
    if (init) {
        //console.log(response);
        response = JSON.parse(response.replace(/&#x27;/g, '"').replace(/\r?\n/g, '\\n'))
    }

    const chatContainer = byId('chat-container');
    if (!chatContainer) return;

    const template = document.getElementById('assistant-message-template');
    const clone = template.content.cloneNode(true);

    const priorityLabel = getPriorityLabel(response.priority);
    const priorityClass = getPriorityClass(response.priority);
    const priorityColor = getPriorityColor(response.priority);

    const factsList = `<ul> ${response.facts_list.map(item => `<li>${item}</li>`).join('')} </ul>`;

    // Rellenar datos
    const messageBox = clone.querySelector('.message-box');
    messageBox.classList.add(priorityClass);

    clone.querySelector('.priority-dot').classList.add(priorityColor);

    clone.querySelector('.priority-label').textContent = priorityLabel;

    try {
        clone.querySelector('.message-text').innerHTML = marked.parse(response.message);
    } catch(e){}

    clone.querySelector('.message-advice').textContent = response.advice || '';

    clone.querySelector('.posible-action').innerHTML = response.posible_action;
    clone.querySelector('.decision').innerHTML = response.decision;
    clone.querySelector('.basis-for-action').innerHTML = response.basis_for_action;
    clone.querySelector('.factual-reason').innerHTML = response.factual_reason;
    clone.querySelector('.critical-state').innerHTML = response.critical_state;
    clone.querySelector('.structural-framework').innerHTML = response.structural_framework;
    clone.querySelector('.structural-question').innerHTML = response.structural_question;
    //clone.querySelector('.facts-list').innerHTML = response.facts_list;
    clone.querySelector('.facts-list').innerHTML = factsList;

    chatContainer.appendChild(clone);
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

function showRecordIndicator() {
    $("#mic-btn").removeClass("bg-primary").addClass("bg-danger");
    $("#record-indicator").show();
}

function hideRecordIndicator() {
    $("#mic-btn").addClass("bg-primary").removeClass("bg-danger");
    $("#record-indicator").hide();
}

function showBtn(show){
    $(".btn-action").hide();
    $("#"+show).show();
}

/*function normalizeAssistantResponse(payload) {
    // payload puede ser:
    // - string
    // - {answer: "..."} o {answer: {priority,text,advice}}
    // - {response: {priority,text,advice}}
    // - {priority,text,advice}
    if (payload == null) { return { priority: "medium", text: "", advice: "" }; }

    if (typeof payload === "string") { return { priority: "medium", text: payload, advice: "" }; }

    // Si viene un objeto "respuesta" en campos comunes:
    const candidate =
        payload.response ??
        payload.answer ??
        payload.assistant ??
        payload;

    if (typeof candidate === "string") { return { priority: "medium", text: candidate, advice: "" }; }

    if (candidate && typeof candidate === "object") {
        const priority = candidate.priority || payload.priority || "medium";
        const text = candidate.text || payload.text || candidate.message || "";
        const advice = candidate.advice || payload.advice || candidate.recommendation || "";
        return { priority: priority, text: text, advice: advice };
    }

    return { priority: "medium", text: String(candidate), advice: "" };
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

    utterance.onend = () => {
        //byId("btn-stop-speak").style.display = "none";
        //byId("mic-btn").style.display = "block";
        showBtn("mic-btn");
    }

    // Ajustes de naturalidad
    utterance.rate = 1.05;   // velocidad (1 es normal)
    //utterance.pitch = 1;     // tono (1 es normal)
    utterance.volume = 1;    // volumen

    speechSynthesis.speak(utterance);
}

async function postChat(text, mode) {
    apiChatUrl = "/assistant/chat-with-llm"; // DO NOT CHANGE
    //
    form = new FormData();
    const report_id = byId('report-id') ? byId('report-id').value : null;
    form.append("report_id", report_id);
    form.append("message", text);
    form.append("mode", mode);
    const csrftoken = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
    if (csrftoken) { form.append("csrfmiddlewaretoken", csrftoken.split('=')[1]); }

    //console.log("Posting chat message to backend:", { report_id, text });
    const resp = await fetch(apiChatUrl, {
        method: "POST",
        body: form
    });
    return await resp.json();
}

async function sendTextMessage(text) {
    const input = byId('text-input');
    addUserMessage(text);

    showTypingIndicator();
    try {
        const data = await postChat(text, input.dataset.mode);
        console.log("--1--");
        console.log(data);

        // Normaliza y renderiza
        //const assistant = normalizeAssistantResponse(data);
        hideTypingIndicator();
        //addAssistantMessage(assistant);
        addAssistantMessage(data);

        //byId("mic-btn").style.display = "none";
        //byId("btn-stop-speak").style.display = "block";
        showBtn("stop-btn");
        //const spoken = [assistant.text, assistant.advice].filter(Boolean).join(" ");
        //const spoken = assistant.advice ? assistant.advice : assistant.text;
        const spoken = data.advice ? data.advice : data.text;
        speakText(spoken, "es-ES");
    } catch (e) {
        hideTypingIndicator();
        console.error(e);
        addAssistantMessage({priority:"low",text:"No he podido enviar el mensaje.",advice:"Inténtalo de nuevo en unos segundos."});
    }
}

async function startRecording() {
    try {
        // 🎙 Iniciar grabación
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        //mediaRecorder = new MediaRecorder(stream);
        mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" }); // No hay mp3 nativo en MediaRecorder
        audioChunks = [];

        mediaRecorder.ondataavailable = event => { audioChunks.push(event.data); };

        mediaRecorder.onstop = async () => {
            showTypingIndicator();
            const audioBlob = new Blob(audioChunks, { type: "audio/webm" });

            const formData = new FormData();
            formData.append("audio", audioBlob, "audio.webm");

            const csrftoken = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
            if (csrftoken) { formData.append("csrfmiddlewaretoken", csrftoken.split('=')[1]); }

            try {
                const response = await fetch("/assistant/start-voice-turn", {
                    method: "POST",
                    body: formData
                });

                if (!response.ok) { throw new Error("Error en el servidor"); }

                const data = await response.json();
                //console.log("Respuesta del backend:", data);

                hideTypingIndicator();
                sendTextMessage(data.texto);
            } catch (error) { 
                console.error("Error enviando audio:", error); 
            }
        };

        mediaRecorder.start();
        isRecording = true;
    } catch (err) {
        console.error("Error accediendo al micrófono:", err);
    }
}

$(document).ready(()=>{

    $("body").on("click", "#mic-btn", async function(e){
        if (!isRecording) {
            showRecordIndicator(); 
            await startRecording();
        } else {
            hideRecordIndicator(); 
            // 🛑 Detener grabación
            if (mediaRecorder && mediaRecorder.state !== "inactive") {
                mediaRecorder.stop();
            }
            isRecording = false;
        }
    });

    $("body").on("keyup", "#text-input", function(e){
        let text = $(this).val();
        if (e.key === 'Enter') {
            if (text != "")
            {
                sendTextMessage($(this).val());
                $(this).val("");
                showBtn("mic-btn");
            }
        }
        else {
            if (text != "")
                showBtn("send-btn");
            else
                showBtn("mic-btn");
        }
    });

    $("body").on("click", "#send-btn", function(e){
        sendTextMessage($("#text-input").val());
        $("#text-input").val("");
        showBtn("mic-btn");
    });

    $("body").on("click", "#stop-btn", function(e){
        //byId("btn-stop-speak").style.display = "none";
        //byId("mic-btn").style.display = "block";
        showBtn("mic-btn");
        speechSynthesis.cancel();
    });

});

/*function addAssistantMessage(response, cfg) {
    const chatContainer = byId('chat-container');
    if (!chatContainer) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message-enter flex gap-3';

    const priorityLabel = getPriorityLabel(response.priority);
    const priorityClass = getPriorityClass(response.priority);
    const priorityColor = getPriorityColor(response.priority);

    const html = marked.parse(response.text);
    //const html = `${escapeHtml(response.text || '')}`;
    messageDiv.innerHTML = `
        <div class="flex-1">
            <div class="overflow-hidden">
                <div class="${priorityClass} px-4 py-3">
                    <div class="flex items-center gap-2 mb-2">
                        <div class="w-2 h-2 ${priorityColor}"></div>
                        <span class="small">${escapeHtml(priorityLabel)}</span>
                    </div>
                    <p class="text-response">${html} </p>
                </div>
                <div class="px-4 pb-2">
                    <p class="text-advice">${escapeHtml(response.advice || '')}</p>
                </div>
            </div>
            <span class="msg-time">Ahora</span>
        </div>
    `;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}*/
/*function addUserMessage(text) {
    const chatContainer = byId('chat-container');
    if (!chatContainer) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message-enter flex justify-end';
    messageDiv.innerHTML = `
        <div class="message-agent">
            <div class="message-box px-4 py-3">
                <p class="">${escapeHtml(text)}</p>
            </div>
            <span class="msg-time">Ahora</span>
        </div>
    `;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}*/


