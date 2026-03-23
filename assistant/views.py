from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse, JsonResponse

from policia.settings import IA_SPEECH_TO_TEXT_URL, IA_SERVICES_URL, IA_LLM_URL, BASE_DIR
from .llmendpoints import IA_LLM_ENDPOINTS
from policia.decorators import group_required
from policia.commons import get_or_none, get_param, show_exc
from gestion.models import Employee, Report, ReportAudio, Config, ReportMsg

from datetime import datetime

import requests, random, time

ERRORS_ANSWER = ["Lo siento, no puedo ayudarte con eso en este momento.",
                "No tengo suficiente información para responder a tu pregunta.",
                "Por favor, proporciona más detalles para que pueda asistirte mejor.",
                "Ha ocurrido un error al procesar tu solicitud. ¿Podrías intentarlo de nuevo?"]

def get_config(key):
    cfg = Config.objects.filter(key=key).first()
    return cfg.value if cfg != None else ""

#def log2file(msg: str, path: str = "logs/rag_app.log"):
def log2file(msg: str, path: str = None):
    from pathlib import Path
    """Log simple a file."""
    if path is None:
        path = Path(BASE_DIR) / "logs" / "rag_app.log"
    try:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except Exception as e:
        print(f"Logging error: {e}")

'''
    REGISTER
'''
def register(request, plan):
    return render(request, "assistant/register.html", {"plan": plan,})

'''
    ASSISTANT METHOD
'''
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

def response_to_context(datas): 
    #try:
    return {
        'message': datas.get("answer", random.choice(ERRORS_ANSWER)), 
        'priority': datas.get("priority", "low"), 
        'advice': datas.get("summary", ""), 
        'citations': datas.get("citations", ""), 
        'intensity': datas.get("intensity", ""), 
        'critical_state': datas.get("critical_state", ""), 
        'structural_framework': datas.get("structural_framework", ""), 
        'structural_question': datas.get("structural_question", ""), 
        'decision': datas.get("decision", ""), 
        'posible_action': datas.get("posible_action", ""), 
        'basis_for_action': datas.get("basis_for_action", ""), 
        'factual_reason': datas.get("factual_reason", ""), 
        'facts_list': datas.get("facts_list", ""), 
        'code': datas.get("code", ""), 
        'status': 'success'
    }
    #except Exception as e:
    #    log2file(f"Error in response_to_context: {show_exc(e)}")
    #    return {'message': random.choice(ERRORS_ANSWER), 'status': 'success'}

def get_report_messages_ia(report):
    import json 

    msg_list = []
    if report.conversation_id != "":
        chat_url = IA_LLM_URL + IA_LLM_ENDPOINTS["openai-chat-conversation"].format(uuid=report.conversation_id)
        params = {}
        headers = { "Authorization": f"Bearer aaaa-bbbb-cccc-dddd" }
        response = requests.get(chat_url, params=params, headers=headers, verify=False, timeout=1200)

        datas = json.loads(response.json())
        for msg in datas:
            for item in msg['content']:
                text = item['text']
                try:
                    parsed = json.loads(text)
                    m = response_to_context(parsed)
                    msg_list.append({'type': "system", 'msg':m})
                except json.JSONDecodeError:
                    msg_list.append({'type': "user", 'msg':text})
    #print(msg_list)
    return msg_list

def get_report_messages(report):
    import json 

    msg_list = []
    for msg in report.messages.all():
        try:
            parsed = json.loads(msg.text.replace("'", "\""))
            m = response_to_context(parsed)
            msg_list.append({'type': "system", 'msg':m})
        except json.JSONDecodeError as e:
            #print(e)
            msg_list.append({'type': "user", 'msg':msg.text})
    return msg_list
 
@group_required("agents")
def agents_assistant(request, report_id=None):
    report = get_or_none(Report, report_id)
    if report is None:
        current_report = Report.get_today_by_emp(request.user.employee)
        report = Report.objects.create(employee=request.user.employee) if current_report == None else current_report
    msg_list = get_report_messages(report)
    context = {"report_id": report.id, "msg_init": get_config("MSG_INIT"), "msg_list": msg_list}
    return render(request, "assistant/assistant.html", context)

@group_required("agents")
def chat_list(request):
    return render(request, "assistant/chat-list.html", {"item_list": Report.objects.filter(employee=request.user.employee)})

@group_required("agents")
def chat_close(request, obj_id):
    report = get_or_none(Report, obj_id)
    report.close = True
    report.save()
    return redirect("assistant")

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
        ReportMsg.objects.create(report=report, text=message)

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
            err_msg = {'message': random.choice(ERRORS_ANSWER), 'status':'success'}
            ReportMsg.objects.create(report=report, text=err_msg["message"])
            return JsonResponse(response_to_context(err_msg), status=200)
            #return JsonResponse({'message': random.choice(ERRORS_ANSWER), 'status':'success'}, status=200)

        datas = response.json()
        #message = datas.get("answer", random.choice(ERRORS_ANSWER))
        #priority = datas.get("priority", "low")
        #summary = datas.get("summary", "")
        report.conversation_id = datas.get("conversation_id", "")
        report.last_interaction = datetime.now()
        report.save()
        ReportMsg.objects.create(report=report, text=datas)
        #print("--2--")
        #print(report.id)
        #print(report.conversation_id)
        #priority = ["high", "medium", "low"]
        #print("--1--")
        #print(datas)
        return JsonResponse(response_to_context(datas))
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




