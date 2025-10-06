//const WS_URL = "{{ ws_url|default:'' }}";

//const btnStart = document.getElementById("btnStart");
//const btnStop = document.getElementById("btnStop");
const stateEl = document.getElementById("state");
const outputEl = document.getElementById("output");
const outputStartEl = document.getElementById("output_start");
const outputEndEl = document.getElementById("output_end");

let audioCtx, processor, source, socket, stream;
let targetSampleRate = 16000;
let inputSampleRate = null;

const mensajes = new Set();

function ajaxGet(url, datas)
{
    $.ajax({
        url : url,
        type : 'GET',
        data : datas,
        cache : false,
        dataType : 'html',
        beforeSend : function(){},
        success : function(data){/*console.log(data)*/},
        error : function(e){alert("Error: "+e.responseText);},
        complete : function(){}
    });
};


function decodeUnicode(str) {
    return str.replace(/\\u[\dA-F]{4}/gi,
        match => String.fromCharCode(parseInt(match.replace(/\\u/g, ''), 16))
    );
}

function log(msg, box, obj_id) {
    if (box == "start")
        outputStartEl.textContent += msg + "\n";
    else {
        if (box == "end")
            outputEndEl.textContent += msg + "\n";
    }
}

function logText(msg, box, obj_id, url) {

    console.log(msg)
    outputEl.textContent += decodeUnicode(msg.replaceAll("\"", "")) + "\n";
    outputEl.scrollTop = outputEl.scrollHeight;
    ajaxGet(url, {"obj_id": obj_id, "value":outputEl.textContent});
    /*if (msg != ""){
        //outputEl.textContent = outputEl.textContent.replace(msg, "");
        console.log(msg)
        outputEl.textContent += " " + msg.replace("\"", "");
        outputEl.scrollTop = outputEl.scrollHeight;
        ajaxGet(url, {"obj_id": obj_id, "value":outputEl.textContent});
    } else {
        if (!outputEl.textContent.endsWith("\n"))
            outputEl.textContent += "\n";
    }*/
}

function logTextVosk(msg, box, obj_id, url) {
    if (msg != ""){
        //console.log(msg)
        //outputEl.textContent = outputEl.textContent.replace(msg, "");
        //console.log(outputEl.textContent);
        outputEl.textContent = msg + "\n";
        outputEl.scrollTop = outputEl.scrollHeight;
        ajaxGet(url, {"obj_id": obj_id, "value":outputEl.textContent});
    } else {
        //if (!outputEl.textContent.endsWith("\n"))
        //    outputEl.textContent += "\n";
    }
}



function downsampleBuffer(buffer, inputRate, outputRate) {
    if (outputRate === inputRate) return buffer;
    const sampleRateRatio = inputRate / outputRate;
    const newLength = Math.round(buffer.length / sampleRateRatio);
    const result = new Float32Array(newLength);
    let offsetResult = 0, offsetBuffer = 0;
    while (offsetResult < result.length) {
        const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio);
        let accum = 0, count = 0;
        for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
            accum += buffer[i]; count++;
        }
        result[offsetResult] = count ? accum / count : 0;
        offsetResult++; offsetBuffer = nextOffsetBuffer;
    }
    return result;
}

function floatTo16BitPCM(float32Array) {
    const int16 = new Int16Array(float32Array.length);
    for (let i = 0; i < float32Array.length; i++) {
        let s = Math.max(-1, Math.min(1, float32Array[i]));
        int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return int16;
}

async function startRecording(ws_url, save_url, obj_id) {
    try {
        //socket = new WebSocket(WS_URL);
        //console.log(ws_url);
        socket = new WebSocket(ws_url);
        socket.binaryType = "arraybuffer";
        //socket.onopen = () => log("[ws] Conectado a " + WS_URL, "start");
        //socket.onopen = () => log("[ws] Conectado a " + ws_url, "start");
        
        //socket.onmessage = (ev) => logText(ev.data, "", obj_id, save_url);
        socket.onmessage = (ev) => logTextVosk(ev.data, "", obj_id, save_url);

        //socket.onclose = () => log("[ws] Conexión cerrada", "end");
        //socket.onerror = (e) => log("[ws error] " + e, "end");

        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        inputSampleRate = audioCtx.sampleRate;
        //log("🎛️ SampleRate de entrada: " + inputSampleRate + " Hz", "start");

        const bufferSize = 4096;
        processor = audioCtx.createScriptProcessor(bufferSize, 1, 1);
        source = audioCtx.createMediaStreamSource(stream);
        source.connect(processor);
        processor.connect(audioCtx.destination);

        processor.onaudioprocess = (e) => {
            const inputData = e.inputBuffer.getChannelData(0);
            const downsampled = downsampleBuffer(inputData, inputSampleRate, targetSampleRate);
            const int16Data = floatTo16BitPCM(downsampled);
            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(int16Data.buffer);
            }
        };

        //btnStart.disabled = true;
        //btnStop.disabled = false;
        $("#btnStartStream").prop("disabled", true);
        $("#btnStopStream").prop("disabled", false);
        stateEl.textContent = "grabando";
        stateEl.className = "font-semibold text-green-600";
        //log("▶️ Grabación iniciada (PCM 16-bit @" + targetSampleRate + " Hz)", "start");
    } catch (err) {
        console.error(err);
        log("Error: " + err.message, "end");
    }
}

function stopRecording() {
    if (processor) { processor.disconnect(); processor.onaudioprocess = null; }
    if (source) source.disconnect();
    if (audioCtx) audioCtx.close();
    if (stream) stream.getTracks().forEach(t => t.stop());
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ event: "EOS" }));
        socket.close();
    }
    //btnStart.disabled = false;
    //btnStop.disabled = true;
    $("#btnStartStream").prop("disabled", false);
    $("#btnStopStream").prop("disabled", true);
    stateEl.textContent = "detenido";
    stateEl.className = "font-semibold text-gray-700";
    //log("⏹️ Grabación detenida", "end");
}

//btnStart.addEventListener("click", startRecording);
//btnStop.addEventListener("click", stopRecording);

$(document).ready(()=>{
    $("body").on("click", "#btnStartStream", function(e){
        console.log("--0--");
        let url = $(this).data("url");
        let url_save = $(this).data("url_save");
        let obj_id = $(this).data("obj_id");
        startRecording(url, url_save, obj_id);
    });
    $("body").on("click", "#btnStopStream", function(e){
        stopRecording();
    });
});

