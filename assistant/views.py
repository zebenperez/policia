from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse, JsonResponse

from policia.settings import IA_SPEECH_TO_TEXT_URL, IA_SERVICES_URL, IA_LLM_URL
from .llmendpoints import IA_LLM_ENDPOINTS
from policia.decorators import group_required
from policia.commons import get_or_none, get_param, show_exc
from gestion.models import Employee, Report, ReportAudio, Config

import requests, random, time

ERRORS_ANSWER = ["Lo siento, no puedo ayudarte con eso en este momento.",
                "No tengo suficiente información para responder a tu pregunta.",
                "Por favor, proporciona más detalles para que pueda asistirte mejor.",
                "Ha ocurrido un error al procesar tu solicitud. ¿Podrías intentarlo de nuevo?"]

#def log2file(msg: str, path: str = "/var/www/django/policia/logs/rag_app.log"):
def log2file(msg: str, path: str = "logs/rag_app.log"):
    """Log simple a file."""
    try:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except Exception as e:
        print(f"Logging error: {e}")

def manage_audios(report, headers):
    audios = report.audios.all()
    transcriptions = []
    audios_to_upoload = []
    for audio in audios:
        log2file(f"Audio ID: {audio.id}, processed: {audio.processed}, upload_id: {audio.upload_id}, text length: {len(audio.text)}")
        if audio.processed and len(audio.upload_id) < 5:
            transcriptions.append(audio.text)
            audios_to_upoload.append(audio)

    transcriptions = list(reversed(transcriptions))
    vector_store_id = report.vector_id
    if transcriptions != []:
        tmp_file_path = f"/tmp/{report.uuid}_{audios.first().id}_transcriptions.txt"
        with open(tmp_file_path, "w") as f:
            f.writelines(transcriptions)
        with open(tmp_file_path, "rb") as f:
            # upload_url = IA_LLM_URL + IA_LLM_ENDPOINTS["upload_expte"].format(uuid=report.uuid)
            upload_url = IA_LLM_URL + IA_LLM_ENDPOINTS["openai-upload-expte"].format(uuid=report.uuid)
            # requests with Bearer token if needed

            response = requests.post(upload_url,files={'file':f},data={'name':report.uuid},headers=headers,verify=False,timeout=120)
            vector_store_id = response.json().get("vector_store_id", None)
            report.vector_id = vector_store_id
            # report.file_id = response.json().get("file_id", None)
            upload_id = response.json().get("file_id", "")
            for audio in audios_to_upoload:
                audio.upload_id = upload_id
                audio.save()
            report.save()

            if response.status_code != 200:
                return f"Error uploading data to microservicio: {response.text}"
                #return JsonResponse({'error': f"Error uploading data to microservicio: {response.text}"}, status=response.status_code)
        
        if response.status_code != 200:
            return f"Error uploading data to microservicio: {response.text}"
            #return JsonResponse({'error': f"Error uploading data to microservicio: {response.text}"}, status=response.status_code)
    return ""


@group_required("agents")
def agents_assistant(request, report_id=None):
    #group = request.user.groups.first()
    #context = {"report_id": report_id, "group": group.name, "msg_num": get_msg_num(group)}
    return render(request, "assistant/assistant.html", {"report_id": report_id})

@group_required("agents")
def chat_with_llm(request):
    log2file("Chat with LLM request received")
    if request.method != "POST":
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    try:
        report_id = get_param(request.POST, "report_id")
        report = get_or_none(Report, report_id)
        message = get_param(request.POST, "message")
        mode = get_param(request.POST, "mode")

        if report is None:
            current_report = Report.get_today_by_emp(request.user.employee)
            report = Report.objects.create(employee=request.user.employee) if current_report == None else current_report
            #return JsonResponse({'error': 'Informe no encontrado'}, status=404)

        log2file(f"Chat with LLM for report {report.uuid} and message: {message}")

        headers = { "Authorization": f"Bearer aaaa-bbbb-cccc-dddd" } # Replace with actual token if needed 
        msg = manage_audios(report, headers)
        if msg != "":
            return JsonResponse({'error': msg}, status=response.status_code)

        collection_name = f"{report.uuid}:{report.conversation_id}"
        vector_store_id = report.vector_id or "NONE"
        chat_url = IA_LLM_URL + IA_LLM_ENDPOINTS["openai-chat"].format(uuid=collection_name, vs_id=vector_store_id)
        log2file(f"Chat URL: {chat_url}")
        # URS is get, wieth q and top_k as params
        params = {
            "q": message,
            "mode": mode,
            "top_k": 5
        }

        response = requests.get(chat_url, params=params, headers=headers, verify=False, timeout=1200)
        if response.status_code != 200:
            log2file("Error in LLM chat:" + response.text)
            return JsonResponse({'message': random.choice(ERRORS_ANSWER), 'status':'success'}, status=200)

        datas = response.json()
        message = datas.get("answer", random.choice(ERRORS_ANSWER))
        priority = datas.get("priority", "low")
        summary = datas.get("summary", "")
        report.conversation_id = datas.get("conversation_id", "")
        report.save()
        #priority = ["high", "medium", "low"]
        return JsonResponse({'message': message, 'priority': priority, 'advice': summary, 'status': 'success'})
    except Exception as e:
        log2file (show_exc(e))
        return JsonResponse({'error': show_exc(e)}, status=500)
 
def assistant_start_voice_turn(request):
    try:
        log2file("Starting voice turn for assistant")
        if request.method != "POST":
            log2file("Método no permitido")
            return JsonResponse({'error': 'Método no permitido'}, status=405)
        # Lógica para iniciar el turno de voz del asistente

        audio = request.FILES.get("audio", None)
        log2file(f"Received audio file: {audio.name if audio else 'None'}, size: {audio.size if audio else 'N/A'} bytes")
        if audio is None:
            return JsonResponse({'error': 'No se ha proporcionado audio'}, status=400)

        # Aquí puedes procesar el archivo de audio como desees
        log2file(f"Sending audio to IA_SPEECH_TO_TEXT_URL: {IA_SPEECH_TO_TEXT_URL}")
        response = requests.post(IA_SPEECH_TO_TEXT_URL, files={'audio': audio}, verify=False)
        if response.status_code == 200:
            data = response.json()
            speakers = data.get('speakers', [])
            segments = data.get('segments', [])
            full_text = ""
            for speaker in speakers:
                speaker_text = ""
                for segment in segments:
                    if segment.get('speaker', '') == speaker:
                        speaker_text += segment.get('text', '') + " "
                full_text += speaker_text.strip() + "\n"
            log2file(f"Transcribed text: {full_text.strip()}")
            
            log2file(f"{response.json()}")
            texto = full_text.strip()
            return JsonResponse({'texto':texto, 'status':'ok', 'conversation_id':'12345', 'transcript':texto, 'answer':f'{texto}'})
        else:
            return JsonResponse({'error': 'Error al transcribir audio'}, status=500)    
    except Exception as e:
        log2file(f"Error: {show_exc(e)}")
        return JsonResponse({'error': 'Error al procesar la solicitud'}, status=500)
 
def health_check(request):
    """Endpoint de salud para verificar que la vista funciona"""
    return JsonResponse({'status': 'ok', 'service': 'audio_stream'})




