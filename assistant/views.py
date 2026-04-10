from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse, JsonResponse

from policia.settings import IA_SPEECH_TO_TEXT_URL, IA_SERVICES_URL, IA_LLM_URL
from policia.decorators import group_required
from policia.commons import get_or_none, get_param, show_exc
from gestion.models import Employee, Report, ReportAudio, ReportMsg
from .llmendpoints import IA_LLM_ENDPOINTS
from .common_lib import *
from .assistant_lib import *

from datetime import datetime

import requests, random


'''
    REGISTER
'''
def register(request, plan):
    return render(request, "assistant/register.html", {"plan": plan,})


'''
    ASSISTANT
'''
@group_required("agents")
def agents_assistant(request):
#    report = get_current_report(request.user, report_id)
#    msg_list = get_report_messages(report)
#    context = {"report_id": report.id, "msg_init": get_config("MSG_INIT"), "msg_list": msg_list}
    return render(request, "assistant/assistant.html", {})

@group_required("agents")
##def agents_assistant(request, report_id=None):
def intervention(request):
    report = get_current_report(request.user, "intervention")
    msg_list = get_report_messages(report)
    context = {"report_id": report.id, "msg_init": get_config("MSG_INIT"), "msg_list": msg_list}
    return render(request, "assistant/intervention.html", context)

@group_required("agents")
def consultation(request):
    report = get_current_report(request.user, "consultation")
    msg_list = get_report_messages(report)
    context = {"report_id": report.id, "msg_init": get_config("MSG_INIT"), "msg_list": msg_list}
    return render(request, "assistant/consultation.html", context)

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
        report = get_or_none(Report, get_param(request.POST, "report_id"))
        #report = get_current_report(request.user, get_param(request.POST, "report_id"))
        message = get_param(request.POST, "message")
        mode = get_param(request.POST, "mode")
        submode = get_param(request.POST, "submode")

        #if report is None:
        #    current_report = Report.get_today_by_emp(request.user.employee)
        #    report = Report.objects.create(employee=request.user.employee) if current_report == None else current_report
            #return JsonResponse({'error': 'Informe no encontrado'}, status=404)

        # En modo urgencia solo se permiten dos preguntas y dos respuestas como mucho
        if mode == "urgencia" and len(report.messages.all()) > 4:
            err_msg = {'message':'Ha superado el límite de mensajes en modo URGENCIA!', 'mode':"error"}
            return JsonResponse(err_msg, status=200)

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
            "submode": submode,
            "top_k": 5
        }

        response = requests.get(chat_url, params=params, headers=headers, verify=False, timeout=1200)
        if response.status_code != 200:
            log2file("Error in LLM chat:" + response.text)
            err_msg = {'message': random.choice(ERRORS_ANSWER), 'mode':'error'}
            ReportMsg.objects.create(report=report, text=err_msg["message"])
            return JsonResponse(err_msg, status=200)

        datas = response.json()
        report.conversation_id = datas.get("conversation_id", "")
        report.last_interaction = datetime.now()
        report.save()
        ReportMsg.objects.create(report=report, text=datas)
        return JsonResponse(response_to_context(datas))
    except Exception as e:
        log2file (show_exc(e))
        return JsonResponse({'error': show_exc(e)}, status=500)
 
#def assistant_start_voice_turn(request):
#    try:
#        log2file("Starting voice turn for assistant")
#        if request.method != "POST":
#            log2file("Método no permitido")
#            return JsonResponse({'error': 'Método no permitido'}, status=405)
#        # Lógica para iniciar el turno de voz del asistente
#
#        audio = request.FILES.get("audio", None)
#        log2file(f"Received audio file: {audio.name if audio else 'None'}, size: {audio.size if audio else 'N/A'} bytes")
#        if audio is None:
#            return JsonResponse({'error': 'No se ha proporcionado audio'}, status=400)
#
#        # Aquí puedes procesar el archivo de audio como desees
#        log2file(f"Sending audio to IA_SPEECH_TO_TEXT_URL: {IA_SPEECH_TO_TEXT_URL}")
#        response = requests.post(IA_SPEECH_TO_TEXT_URL, files={'audio': audio}, verify=False)
#        if response.status_code == 200:
#            data = response.json()
#            speakers = data.get('speakers', [])
#            segments = data.get('segments', [])
#            full_text = ""
#            for speaker in speakers:
#                speaker_text = ""
#                for segment in segments:
#                    if segment.get('speaker', '') == speaker:
#                        speaker_text += segment.get('text', '') + " "
#                full_text += speaker_text.strip() + "\n"
#            log2file(f"Transcribed text: {full_text.strip()}")
#            
#            log2file(f"{response.json()}")
#            texto = full_text.strip()
#            return JsonResponse({'texto':texto, 'status':'ok', 'conversation_id':'12345', 'transcript':texto, 'answer':f'{texto}'})
#        else:
#            return JsonResponse({'error': 'Error al transcribir audio'}, status=500)    
#    except Exception as e:
#        log2file(f"Error: {show_exc(e)}")
#        return JsonResponse({'error': 'Error al procesar la solicitud'}, status=500)
 
def health_check(request):
    """Endpoint de salud para verificar que la vista funciona"""
    return JsonResponse({'status': 'ok', 'service': 'audio_stream'})




