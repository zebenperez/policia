let mediaRecorder;
let audioChunks = [];
let isRecording = false;

function byId(id) {
    return document.getElementById(id);
}

function decodeHTML(html) {
    const txt = document.createElement("textarea");
    txt.innerHTML = html;
    return txt.value;
}

function removeHtmlTags(html){
    const div = document.createElement("div");
    div.innerHTML = html;
    const text = div.textContent || div.innerText;
    return text
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

function addUserMessage(text, temp="user-message-template") {
    //console.log(temp);
    const chatContainer = byId('chat-container');
    if (!chatContainer) return;

    const template = document.getElementById(temp);
    const clone = template.content.cloneNode(true);

    // Insertar texto de forma segura
    clone.querySelector('.message-text').innerHTML = decodeHTML(text).replace(/\n/g, "<br>");

    chatContainer.appendChild(clone);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addCompMessage(response, temp="comp-message-template") {
    //console.log(temp);
    const chatContainer = byId('chat-container');
    if (!chatContainer) return;

    const template = document.getElementById(temp);
    const clone = template.content.cloneNode(true);

    // Insertar texto de forma segura
    clone.querySelector('.message-text').innerHTML = marked.parse(response.message);
    clone.querySelector('.template').innerHTML = marked.parse(response.template);
    clone.querySelector('.questions').innerHTML = marked.parse(response.questions.join('<br/>'));

    chatContainer.appendChild(clone);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addFileMessage(text, url, temp="file-message-template") {
    //console.log(temp);
    const chatContainer = byId('chat-container');
    if (!chatContainer) return;

    const template = document.getElementById(temp);
    const clone = template.content.cloneNode(true);

    // Insertar texto de forma segura
    clone.querySelector('.message-text').innerHTML = `<a href="${url}" target="_blank"> ${text} </a>`;

    chatContainer.appendChild(clone);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addAssistantMessage(response) {
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

function addMessage(data, init=false) {
    if (init) { data = JSON.parse(data.replace(/&#x27;/g, '"').replace(/\r?\n/g, '\\n')).message }

    //console.log(data.submode);
    // MENSAJE DEL USUARIO
    if (typeof data === "string") {
        addUserMessage(data);
    } else {
        //MENSAJE DEL SISTEMA
        if (data.submode == "U0") { //Submodo Urgencia
            addAssistantMessage(data);
        } else if (data.submode.toUpperCase() == "I1") {
            addCompMessage(data);
        } else {
            addUserMessage(data.message, data.mode+"-message-template");
        }
    }
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

function speakText(text, lang = "es-ES") {
    if (!text) return;


    speechSynthesis.cancel();

    text = text.substring(0, 2500);
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

async function postChat(text, mode, submode) {
    apiChatUrl = "/assistant/chat-with-llm"; // DO NOT CHANGE
    //
    form = new FormData();
    const report_id = byId('report-id') ? byId('report-id').value : null;
    form.append("report_id", report_id);
    form.append("message", text);
    form.append("mode", mode);
    form.append("submode", submode);
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
        const data = await postChat(text, input.dataset.mode, input.dataset.submode);
        //console.log("--1--");
        console.log(data);

        hideTypingIndicator();
        addMessage(data);

        if (data.submode == "U0") //Submodo Urgencia
        {
            showBtn("stop-btn");
            //const spoken = data.advice ? data.advice : data.text;
            const spoken = data.advice;
            speakText(removeHtmlTags(spoken), "es-ES");
        }
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
                console.log("Respuesta del backend:", data);

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

async function uploadPDF(formData, token) {
    showTypingIndicator();
    try {
        const response = await fetch("/assistant/chat-upload-file", {
            method: "POST",
            headers: { "X-CSRFToken": token },
            body: formData
        });

        if (!response.ok) { throw new Error(`HTTP error ${response.status}`); }

        const data = await response.json();
        console.log("PDF subido correctamente");
        console.log(data);
        hideTypingIndicator();
        addMessage("PDF subido correctamente")
        return data;
    } catch (error) {
        console.log("Error subida");
        console.error(error);
        hideTypingIndicator();
        addMessage("Error en la subida del fichero!")
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

    $("body").on("input", "#text-input", function(e){
        let text = $(this).val();
        if (text != "") {
            let tp = $("<div>").html(text).text();
            $(this).val(tp);
            showBtn("send-btn");
        } else {
            showBtn("mic-btn");
        }
    });

    $("body").on("keydown", "#text-input", function(e){
        let text = $(this).val();
        if (e.key === 'Enter') {
            if (text != "")
            {
                sendTextMessage($(this).val());
                $(this).val("");
                showBtn("mic-btn");
            }
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

    $("body").on("click", ".message-box #copy-btn", function(e){
        var text = $(this).next('.message-text').html();
        navigator.clipboard.writeText(text).then(function() { alert('¡Texto copiado con éxito!'); })
        .catch(function(err) { console.error('No se pudo copiar el texto: ', err); });
    });

    $("body").on("change", "#file-btn", function(e){
        let file = this.files[0];

        if (!file) { return; }

        // 1. Validar tamaño (2MB)
        let maxSize = 2 * 1024 * 1024;
        if (file.size > maxSize) {
            alert("El PDF no puede superar 2MB");
            $(this).val("");
            return;
        }

        // 2. Validar PDF
        let allowedType = "application/pdf";
        if (file.type !== allowedType) {
            alert("Solo se permiten archivos PDF");
            $(this).val("");
            return;
        }

        // 3. Mostrar preview PDF
        addFileMessage(file.name, URL.createObjectURL(file));

        // 4. Enviar a Django
        let formData = new FormData();
        console.log($(this).data('report'));
        formData.append("report", $(this).data('report'));
        formData.append("file", file);
        uploadPDF(formData, $(this).data('token'));

        // if(file){ console.log(file.name); }
    });
});

