from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse, JsonResponse

from policia.settings import IA_SPEECH_TO_TEXT_URL, IA_SERVICES_URL, IA_LLM_URL, API_TOKEN
from policia.decorators import group_required
from policia.commons import get_or_none, get_param, show_exc, user_in_group
from gestion.models import Employee, Report, ReportAudio, ReportMsg, ReportTokens, Submode
from .llmendpoints import IA_LLM_ENDPOINTS
from .common_lib import *
from .assistant_lib import *

from datetime import datetime

import requests, random


MODE_INTERVENTION = 'intervention'
MODE_CONSULTATION = 'consultation'

'''
    Landing
'''
def landing(request):
    return render(request, "assistant/landing.html", {})


'''
    REGISTER
'''
def register(request, plan):
    return render(request, "assistant/register.html", {"plan": plan,})


@group_required("admins", "agents")
def assistant(request):
    if user_in_group(request.user, "admins"):
         return redirect("stats")
    return redirect("agents-assistant")

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
def assistant_chat(request, mode="intervention"):
    #mode = "intervention"
    report = get_current_report(request.user, mode)
    msg_list = get_report_messages(report)
    if len(msg_list) > 0:
        submode = Submode.objects.filter(code=msg_list[-1]['submode']).first()
    else:
        submode = Submode.objects.filter(mode=mode).first()
    submode_list = Submode.objects.filter(mode=mode)
    col_span = 12 // len(submode_list) if mode == "consultation" else 6
    context = {
        "report_id": report.id, 
        "msg_init": get_config("MSG_INIT"), 
        "msg_list": msg_list, 
        "submode_list": submode_list,
        "submode": submode,
        "col_span": col_span,
        "mode": mode
    }
    return render(request, "assistant/assistant-chat.html", context)

#@group_required("agents")
#def consultation(request):
#    mode = "consultation"
#    report = get_current_report(request.user, mode)
#    msg_list = get_report_messages(report)
#    code = msg_list[-1]['submode'] if len(msg_list) > 0 else "F1"
#    submode = Submode.objects.filter(code=code).first()
#    context = {
#        "report_id": report.id, 
#        "msg_init": get_config("MSG_INIT"), 
#        "msg_list": msg_list, 
#        "submode_list": Submode.objects.filter(mode=mode),
#        "submode": submode,
#        "mode": mode
#    }
#    return render(request, "assistant/assistant-chat.html", context)

@group_required("agents")
def chat_list(request):
    return render(request, "assistant/chat-list.html", {"item_list": Report.objects.filter(employee=request.user.employee)})

@group_required("agents")
def chat_close(request, obj_id):
    report = get_or_none(Report, obj_id)
    report.close = True
    report.save()
    return redirect(reverse('assistant-chat', kwargs={"mode": report.mode}))
    #return redirect("assistant")

@group_required("agents")
def chat_open(request, obj_id):
    report = get_or_none(Report, obj_id)
    if report != None:
        Report.objects.filter(employee=report.employee, mode=report.mode, close=False).update(close=True)
        report.close = False
        report.save()
    return redirect("assistant")

@group_required("agents")
def chat_report_count(request):
    mode = get_param(request.GET, "mode")
    kwargs = {"employee": request.user.employee}
    if mode != "":
        kwargs["mode"] = mode
    count = Report.objects.filter(**kwargs).count()
    return HttpResponse(count)

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
        ReportMsg.objects.create(report=report, text=message, submode=submode)

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
            ReportMsg.objects.create(report=report, text=err_msg["message"], submode=submode)
            return JsonResponse(err_msg, status=200)

        datas = response.json()
        report.conversation_id = datas.get("conversation_id", "")
        report.last_interaction = datetime.now()
        report.save()
        ReportMsg.objects.create(report=report, text=datas, submode=submode)
        return JsonResponse(response_to_context(datas))
    except Exception as e:
        log2file (show_exc(e))
        return JsonResponse({'error': show_exc(e)}, status=500)
 
@group_required("agents")
def chat_upload_file(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método inválido"}, status=405)

    file = request.FILES.get("file")
    report = get_or_none(Report, get_param(request.POST, "report"))

    if report == None:
        return JsonResponse({"error": "No report"}, status=400)

    if not file:
        return JsonResponse({"error": "No file"}, status=400)

    # Validar PDF
    if file.content_type != "application/pdf":
        return JsonResponse({"error": "Solo PDF"}, status=400)

    # Validar tamaño
    if file.size > 2 * 1024 * 1024:
        return JsonResponse({"error": "Máximo 2MB"}, status=400)

    with open(f"/tmp/{file.name}", "wb+") as f:
        upload_url = IA_LLM_URL + IA_LLM_ENDPOINTS["openai-upload-expte"].format(uuid=report.uuid)
        #print(upload_url)

        headers = { "Authorization": f"Bearer aaaa-bbbb-cccc-dddd" } 
        response = requests.post(upload_url,files={'file':f},data={'name':report.uuid},headers=headers,verify=False,timeout=120)
        vector_store_id = response.json().get("vector_store_id", None)
        #print(vector_store_id)

        if response.status_code != 200:
            err = response.json().get("detail", "")
            return JsonResponse({"error": f"Error uploading data to microservicio: {err}"}, status=400)

    return JsonResponse({ "success": True, "filename": file.name })


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
 
'''
    ADMIN
'''
from django.db.models import Count, Q, Sum, IntegerField
from django.db.models.functions import Cast

def stats_employees(start_date, end_date, search):
    employees = Employee.objects.filter(user__groups__name="agents")
    if search:
        employees = employees.filter(name__icontains=search)

    employees = employees.annotate(
        # --- EXPEDIENTES ---
        total_expedientes_int=Count(
            'reports',
            filter=Q( reports__date__date__gte=start_date, reports__date__date__lte=end_date, reports__mode=MODE_INTERVENTION),
            distinct=True
        ),
        total_expedientes_con=Count(
            'reports',
            filter=Q( reports__date__date__gte=start_date, reports__date__date__lte=end_date, reports__mode=MODE_CONSULTATION),
            distinct=True
        ),

        # --- INTERACCIONES ---
        total_interacciones_int=Count(
            'reports__messages',
            filter=Q(
                reports__messages__date__date__gte=start_date,
                reports__messages__date__date__lte=end_date,
                reports__mode=MODE_INTERVENTION
            ),
            distinct=True
        ),
        total_interacciones_con=Count(
            'reports__messages',
            filter=Q(
                reports__messages__date__date__gte=start_date,
                reports__messages__date__date__lte=end_date,
                reports__mode=MODE_CONSULTATION
            ),
            distinct=True
        ),
            
        # INPUT TOKENS
        input_tokens_int=Sum(
            Cast('reports__tokens__input_tokens', IntegerField()),
            filter=Q( reports__date__date__gte=start_date, reports__date__date__lte=end_date, reports__mode=MODE_INTERVENTION)
        ),
        input_tokens_con=Sum(
            Cast('reports__tokens__input_tokens', IntegerField()),
            filter=Q( reports__date__date__gte=start_date, reports__date__date__lte=end_date, reports__mode=MODE_CONSULTATION)
        ),

        # OUTPUT TOKENS
        output_tokens_int=Sum(
            Cast('reports__tokens__output_tokens', IntegerField()),
            filter=Q( reports__date__date__gte=start_date, reports__date__date__lte=end_date, reports__mode=MODE_INTERVENTION)
        ),
        output_tokens_con=Sum(
            Cast('reports__tokens__output_tokens', IntegerField()),
            filter=Q( reports__date__date__gte=start_date, reports__date__date__lte=end_date, reports__mode=MODE_CONSULTATION)
        ),
    )
    return employees

def stats_employees_tokens(start_date, end_date, search):
    employees = Employee.objects.filter(user__groups__name="agents")
    if search:
        employees = employees.filter(name__icontains=search)

    employees = employees.annotate(
        # INPUT TOKENS
        input_tokens_int=Sum(
            Cast('reports__tokens__input_tokens', IntegerField()),
            filter=Q( reports__date__date__gte=start_date, reports__date__date__lte=end_date, reports__mode=MODE_INTERVENTION)
        ),
        input_tokens_con=Sum(
            Cast('reports__tokens__input_tokens', IntegerField()),
            filter=Q( reports__date__date__gte=start_date, reports__date__date__lte=end_date, reports__mode=MODE_CONSULTATION)
        ),

        # OUTPUT TOKENS
        output_tokens_int=Sum(
            Cast('reports__tokens__output_tokens', IntegerField()),
            filter=Q( reports__date__date__gte=start_date, reports__date__date__lte=end_date, reports__mode=MODE_INTERVENTION)
        ),
        output_tokens_con=Sum(
            Cast('reports__tokens__output_tokens', IntegerField()),
            filter=Q( reports__date__date__gte=start_date, reports__date__date__lte=end_date, reports__mode=MODE_CONSULTATION)
        ),
    )
    return employees


@group_required("admins")
def stats(request):
    from datetime import date
    import calendar

    search = request.POST.get("searchInput", "")
    start_date = request.POST.get("startDate", "")
    end_date = request.POST.get("endDate", "")

    if not start_date or not end_date:
        today = date.today()
        start_default = today.replace(day=1)

        last_day = calendar.monthrange(today.year, today.month)[1]
        end_default = today.replace(day=last_day)

        if not start_date:
            start_date = start_default.strftime("%Y-%m-%d")
        if not end_date:
            end_date = end_default.strftime("%Y-%m-%d")


    total_expedientes = Report.objects.filter(date__date__gte=start_date, date__date__lte=end_date).count()
    total_interacciones = ReportMsg.objects.filter(date__date__gte=start_date, date__date__lte=end_date).count()

    qs = ReportTokens.objects.filter( date__date__gte=start_date, date__date__lte=end_date)
    total_tokens = qs.aggregate(total_in=Sum(Cast('input_tokens',IntegerField())),total_out=Sum(Cast('output_tokens',IntegerField())))
    
    employees = stats_employees(start_date, end_date, search)
    employees2 = stats_employees_tokens(start_date, end_date, search)

    context = {
        "employees": employees,
        "employees2": employees2,
        "total_expedientes": total_expedientes,
        "total_interacciones": total_interacciones,
        "total_tokens_inp": total_tokens['total_in'] or 0,
        "total_tokens_out": total_tokens['total_out'] or 0,
        "search": search,
        "startDate": start_date,
        "endDate": end_date,
    }
    return render(request, "assistant/stats.html", context)

'''
    ENDPOINTS
'''
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def set_tokens_info(request):
    # Solo permitir POST
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    # Validar token
    token = request.headers.get("Authorization")

    if token != f"Bearer {API_TOKEN}":
        return JsonResponse( {"error": "Unauthorized"}, status=401)

    # Leer JSON
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    #print(data)
    conversation_id = get_param(data, "conversation_id")
    if conversation_id != "":
        report = Report.objects.filter(conversation_id = conversation_id).first()
        if report != None:
            rt = ReportTokens.objects.create(
                report = report,
                input_tokens = get_param(data, "input_tokens"),
                output_tokens = get_param(data, "output_tokens"),
                total_tokens = get_param(data, "total_tokens"),
                cached_tokens = get_param(data, "cached_tokens"),
                reasoning_tokens = get_param(data, "reasoning_tokens"),
                conversation_id = get_param(data, "conversation_id")
            )
    return JsonResponse({ "success": True, "received": data })

'''
    AUX
'''
def health_check(request):
    """Endpoint de salud para verificar que la vista funciona"""
    return JsonResponse({'status': 'ok', 'service': 'audio_stream'})




