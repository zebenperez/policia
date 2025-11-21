from django.shortcuts import render, redirect
from django.template.loader import render_to_string as render_string
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from datetime import datetime

from policia.settings import IA_SPEECH_TO_TEXT_URL, IA_SERVICES_URL, IA_LLM_URL
from .llmendpoints import IA_LLM_ENDPOINTS
from policia.decorators import group_required
from policia.commons import user_in_group, get_or_none, get_param, show_exc
from gestion.models import Employee, Report, ReportAudio

import subprocess
import threading
import requests
import random, time


'''
    AGENTS
'''
@group_required("employees")
def agents_home(request):
    item_list = Report.objects.filter(employee=request.user.employee)
    return render(request, "agents/home.html", {"item_list": item_list})

@group_required("employees")
def agents_report(request, obj_id):
    try:
        report = Report.objects.get(pk=obj_id)
        return render(request, "agents/report.html", {"report": report})
    except Exception as e:
        print(f"Error: {e}")

@group_required("employees")
def agents_report_new(request):
    obj = Report.objects.create(employee=request.user.employee)
    return redirect(reverse('agents-report', kwargs={"obj_id": obj.id}))

@group_required("employees")
def agents_audio_save(request):
    report = get_or_none(Report, get_param(request.POST, "report"))
    #print(report)
    if report != None:
        if "audio" in request.FILES and request.FILES["audio"] != "":
            concept = "Esperando traducción de audio..."
            audio = request.FILES["audio"]
            report_audio = ReportAudio.objects.create(text=concept, audio=audio, report=report)
            transcribe_audio(report_audio.audio, report_audio)
            #t = threading.Thread(target=transcribe_audio, args=[report_audio.audio, report_audio], daemon=True)
            #t.start()
    return HttpResponse(report.id)

@group_required("employees")
def agents_report_print(request, obj_id):
    obj = get_or_none(Report, obj_id)
    datas = ""
    audio = obj.audios.all().first()
    if audio != None:
        try:
            response = requests.post(IA_SERVICES_URL, params={'texto': audio.text})
            datas = ""
            if response.status_code == 200:
                #print(response.json())
                datas = response.json()
                #return response.json()['texto']
            else:
                raise Exception(f"Error en microservicio: {response.text}")
        except Exception as e:
            print(e)
    #print(datas)
    return render(request, "agents/print.html", {"obj": obj, "datas": datas})

@group_required("employees")
def chat_with_llm(request):
    if request.method != "POST":
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    try:
        errors_answer = ["Lo siento, no puedo ayudarte con eso en este momento.",
                         "No tengo suficiente información para responder a tu pregunta.",
                         "Por favor, proporciona más detalles para que pueda asistirte mejor.",
                         "Ha ocurrido un error al procesar tu solicitud. ¿Podrías intentarlo de nuevo?"]
        report_id = get_param(request.POST, "report_id")
        report = get_or_none(Report, report_id)
        message = get_param(request.POST, "message")
        report.save()

        if report is None:
            return JsonResponse({'error': 'Informe no encontrado'}, status=404)
        datas = ""
        audios = report.audios.all()
        transcriptions = []
        for audio in audios:
            if audio.processed:
                transcriptions.append(audio.text)
        transcriptions = list(reversed(transcriptions))
        tmp_file_path = f"/tmp/{report.uuid}_{audios.first().id}_transcriptions.txt"
        with open(tmp_file_path, "w") as f:
            f.writelines(transcriptions)
        with open(tmp_file_path, "rb") as f:
            upload_url = IA_LLM_URL + IA_LLM_ENDPOINTS["upload_expte"].format(uuid=report.uuid)
            # requests with Bearer token if needed
            headers = {
                "Authorization": f"Bearer aaaa-bbbb-cccc-dddd"  # Replace with actual token if needed
            }

            response = requests.post(upload_url, files={'file': f}, data={'name':report.uuid}, headers=headers, verify=False, timeout=120)

            if response.status_code != 200:
                return JsonResponse({'error': f"Error uploading data to microservicio: {response.text}"}, status=response.status_code)
    
        if response.status_code != 200:
            return JsonResponse({'error': f"Error uploading data to microservicio: {response.text}"}, status=response.status_code)

        chat_url = IA_LLM_URL + IA_LLM_ENDPOINTS["chat"].format(uuid=report.uuid)
        # URS is get, wieth q and top_k as params
        params = {
            "q": message,
            "top_k": 5
        }
        response = requests.get(chat_url, params=params, headers=headers, verify=False, timeout=120)
        if response.status_code != 200:
            print ("Error in LLM chat:", response.text)
            return JsonResponse({'message': random.choice(errors_answer), 'status':'success'}, status=200)
        datas = response.json()
        message = datas.get("answer", random.choice(errors_answer))
        return JsonResponse({'message': message, 'status': 'success'})
    except Exception as e:
        return JsonResponse({'error': show_exc(e)}, status=500)

@group_required("employees")
def summarize_report_with_ia(request):
    print("Summarizing report with IA")
    if request.method != "POST":
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    try :
    
        obj_id = get_param(request.POST, "obj_id")
        obj = get_or_none(Report, obj_id)
        obj.save()
        if obj is None:
            return JsonResponse({'error': 'Informe no encontrado'}, status=404)
        datas = ""
        audios = obj.audios.all()
        transcriptions = []
        for audio in audios: 
            if audio.processed and audio.text != '':
                transcriptions.append(audio.text)
        if transcriptions == []:
            return JsonResponse({'error': f"No hay transcripciones válidas"}, status=422)
        transcriptions = list(reversed(transcriptions))
        tmp_file_path = f"/tmp/{obj.uuid}_{audios.first().id}_transcriptions.txt"
        with open(tmp_file_path, "w", encoding="utf-8", newline="") as f:
            f.writelines(transcriptions)
        with open(tmp_file_path, "rb") as f:
            remove_url = IA_LLM_URL + IA_LLM_ENDPOINTS["clear-expte"].format(uuid=obj.uuid)
            upload_url = IA_LLM_URL + IA_LLM_ENDPOINTS["upload_expte"].format(uuid=obj.uuid)
            headers = {
                "Authorization": f"Bearer aaaa-bbbb-cccc-dddd"  # Replace with actual token if needed
            }
            response = requests.delete(remove_url, headers=headers, verify=False)
            response = requests.post(upload_url, files={'file': f}, data={'name':obj.uuid}, headers=headers, verify=False, timeout=120)

            if response.status_code != 200:
                return JsonResponse({'error': f"Error uploading data to microservicio: {response.text}"}, status=response.status_code)
        print ("Uploaded report data to LLM microservice")
        personal_data = IA_LLM_URL + IA_LLM_ENDPOINTS["personal-data"].format(uuid=obj.uuid)
        response = requests.get(personal_data, verify=False, timeout=1200)
        print ("Summarization response:", response.text)
        if response.status_code == 200:
            datas = response.json()
            print (datas)
        else:
            return JsonResponse({'error': f"Error summarizing report in microservicio: {response.text}"}, status=response.status_code)

        return JsonResponse({'data': datas})
    except Exception as e:
        return JsonResponse({'error': show_exc(e)}, status=500)
    
@group_required("employees")
def interpretation_report_with_ia(request):
    print("Interpreting report with IA")
    if request.method != "POST":
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    try :
        t0 = time.time()
        while ((time.time()) - t0 < 3.0): # Pause in order to allow previous summarization to complete
            time.sleep(0.1)

        obj_id = get_param(request.POST, "obj_id")
        obj = get_or_none(Report, obj_id)
        obj.save()
        if obj is None:
            return JsonResponse({'error': 'Informe no encontrado'}, status=404)
        # datas = ""
        # audios = obj.audios.all()
        # transcriptions = []
        # for audio in audios: 
        #     if audio.processed and audio.text != '':
        #         transcriptions.append(audio.text)
        # if transcriptions == []:
        #     return JsonResponse({'error': f"No hay transcripciones válidas"}, status=422)
        # transcriptions = list(reversed(transcriptions))
        # tmp_file_path = f"/tmp/{obj.uuid}_{audios.first().id}_transcriptions.txt"
        # with open(tmp_file_path, "w", encoding="utf-8", newline="") as f:
        #     f.writelines(transcriptions)
        # with open(tmp_file_path, "rb") as f:
        #     remove_url = IA_LLM_URL + IA_LLM_ENDPOINTS["clear-expte"].format(uuid=obj.uuid)
        #     upload_url = IA_LLM_URL + IA_LLM_ENDPOINTS["upload_expte"].format(uuid=obj.uuid)
        #     headers = {
        #         "Authorization": f"Bearer aaaa-bbbb-cccc-dddd"  # Replace with actual token if needed
        #     }
        #     response = requests.delete(remove_url, headers=headers, verify=False)
        #     response = requests.post(upload_url, files={'file': f}, data={'name':obj.uuid}, headers=headers, verify=False, timeout=120)

        #     if response.status_code != 200:
        #         return JsonResponse({'error': f"Error uploading data to microservicio: {response.text}"}, status=response.status_code)
        print ("Uploaded report data to LLM microservice")
        interpretation_url = IA_LLM_URL + IA_LLM_ENDPOINTS["interpretation"].format(uuid=obj.uuid)
        response = requests.get(interpretation_url, headers=headers, verify=False, timeout=1200)
        print ("Interpretation response:", response.text)
        if response.status_code == 200:
            datas = response.json()
            print (datas)
        else:
            return JsonResponse({'error': f"Error interpreting report in microservicio: {response.text}"}, status=response.status_code)
        return JsonResponse({'data': datas})
    except Exception as e:
        return JsonResponse({'error': show_exc(e)}, status=500)

#def fix_text(orig):
#    import anthropic
#
#    api_key = "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"
#    client = anthropic.Anthropic(api_key=api_key)
#    response = client.messages.create(
#        model="claude-3-haiku-20240307",
#        max_tokens=2048,
#        messages=[
#            {
#                "role": "user",
#                "content": f"""Corrige la ortografía y gramática del siguiente texto en español:
#
#                {orig}
#
#                Proporciona:
#                    1. El texto corregido
#                    2. Lista de correcciones realizadas con explicación breve"""
#            }
#        ]
#    )
#    return response.content[0].text

def transcribe_audio(audio_file, obj):
    #response = requests.post('http://localhost:8001/transcribir', files={'audio': audio_file})
    response = requests.post(IA_SPEECH_TO_TEXT_URL, files={'audio': audio_file}, verify=False)
    if response.status_code == 200:
        #print(response.json())
        obj.text = response.json()['texto']
        obj.processed = True
        obj.save()

        #t = fix_text(obj.text)
        #obj.text += "<br/>---------------------------------------"
        #obj.text += f'<br/>{t}'
        #obj.save()
        return JsonResponse({'texto': obj.text, 'status': 'ok'})
    else:
        raise Exception(f"Error en microservicio: {response.text}")
    
def retranscribe_audio(request):
    if request.method != "POST":
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    obj_id = get_param(request.POST, "obj_id")
    obj = get_or_none(ReportAudio, obj_id)
    if obj is None:
        return JsonResponse({'error': 'Audio no encontrado'}, status=404)
    try:
        response = transcribe_audio(obj.audio, obj)
        return response
    except Exception as e:
        return JsonResponse({'error': show_exc(e)}, status=500)
    
@csrf_exempt
def audio_form_save(request):
    try:
        if request.method != "POST":
            return JsonResponse({'error': 'Método no permitido'}, status=405)
        obj_id = get_param(request.POST, "id")
        report_audio = ReportAudio.objects.get(pk=obj_id)
        report_audio.text = get_param(request.POST, "text")
        report_audio.processed = True
        report_audio.save()
        return JsonResponse({'status': 'ok', 'obj_id': report_audio.id, 'texto': report_audio.text})
    except Exception as e:
        print(f"Error: {show_exc(e)}")
    return JsonResponse({'error': 'Error al guardar el formulario'}, status=500)

def audio_form(request):
    try:
        if request.method != "POST":
            return JsonResponse({'error': 'Método no permitido'}, status=405)
        obj_id = get_param(request.POST, "obj_id")
        report_audio = ReportAudio.objects.get(pk=obj_id)
        template = render_string("agents/audio-form.html", {"item": report_audio})
        return JsonResponse({'html': template})
    except Exception as e:
        print(f"Error: {show_exc(e)}")
    return JsonResponse({'error': 'Error al cargar el formulario'}, status=500)
    
def health_check(request):
    """Endpoint de salud para verificar que la vista funciona"""
    return JsonResponse({'status': 'ok', 'service': 'audio_stream'})

# def reassign_uuids(request):
#     reports = Report.objects.all()
#     for report in reports:
#         if report.uuid is None or len(report.uuid) < 5:
#             reoport.uuid = Report.new_uuid()
#             report.save()
#     return HttpResponse("OK")
# 
# 
