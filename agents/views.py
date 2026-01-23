from django.shortcuts import render, redirect
from django.template.loader import render_to_string as render_string
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from datetime import datetime
from django.conf import settings

from policia.settings import IA_SPEECH_TO_TEXT_URL, IA_SERVICES_URL, IA_LLM_URL
from .llmendpoints import IA_LLM_ENDPOINTS
from policia.decorators import group_required
from policia.commons import user_in_group, get_or_none, get_param, show_exc
from gestion.models import Employee, Report, ReportAudio

import subprocess
import threading
import requests
import random, time


def log2file(msg: str, path: str = "/code/logs/rag_app.log"):
    """Log simple a file."""
    try:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except Exception as e:
        print(f"Logging error: {e}")


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
        log2file(f"Error: {e}")

@group_required("employees")
def agents_report_new(request):
    obj = Report.objects.create(employee=request.user.employee)
    return redirect(reverse('agents-report', kwargs={"obj_id": obj.id}))

@group_required("employees")
def agents_audio_save(request):
    report = get_or_none(Report, get_param(request.POST, "report"))
    #log2file(report)
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
                #log2file(response.json())
                datas = response.json()
                #return response.json()['texto']
            else:
                raise Exception(f"Error en microservicio: {response.text}")
        except Exception as e:
            log2file(e)
    #log2file(datas)
    return render(request, "agents/print.html", {"obj": obj, "datas": datas})

@group_required("employees")
def chat_with_llm(request):
    log2file("Chat with LLM request received")
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
        log2file(f"Chat with LLM for report {report.uuid} and message: {message}")

        if report is None:
            return JsonResponse({'error': 'Informe no encontrado'}, status=404)
        datas = ""
        audios = report.audios.all()
        transcriptions = []
        audios_to_upoload = []
        for audio in audios:
            log2file(f"Audio ID: {audio.id}, processed: {audio.processed}, upload_id: {audio.upload_id}, text length: {len(audio.text)}")
            if audio.processed and len(audio.upload_id) < 5:
                transcriptions.append(audio.text)
                audios_to_upoload.append(audio)
        transcriptions = list(reversed(transcriptions))
        headers = {
            "Authorization": f"Bearer aaaa-bbbb-cccc-dddd"  # Replace with actual token if needed
        }
        vector_store_id = report.vector_id
        if transcriptions != []:
            tmp_file_path = f"/tmp/{report.uuid}_{audios.first().id}_transcriptions.txt"
            with open(tmp_file_path, "w") as f:
                f.writelines(transcriptions)
            with open(tmp_file_path, "rb") as f:
                # upload_url = IA_LLM_URL + IA_LLM_ENDPOINTS["upload_expte"].format(uuid=report.uuid)
                upload_url = IA_LLM_URL + IA_LLM_ENDPOINTS["openai-upload-expte"].format(uuid=report.uuid)
                # requests with Bearer token if needed


                response = requests.post(upload_url, files={'file': f}, data={'name':report.uuid}, headers=headers, verify=False, timeout=120)
                vector_store_id = response.json().get("vector_store_id", None)
                report.vector_id = vector_store_id
                # report.file_id = response.json().get("file_id", None)
                upload_id = response.json().get("file_id", "")
                for audio in audios_to_upoload:
                    audio.upload_id = upload_id
                    audio.save()
                report.save()

                if response.status_code != 200:
                    return JsonResponse({'error': f"Error uploading data to microservicio: {response.text}"}, status=response.status_code)
        
            if response.status_code != 200:
                return JsonResponse({'error': f"Error uploading data to microservicio: {response.text}"}, status=response.status_code)

        collection_name = f"{report.uuid}:{report.conversation_id}"
        vector_store_id = report.vector_id or "NONE"
        chat_url = IA_LLM_URL + IA_LLM_ENDPOINTS["openai-chat"].format(uuid=collection_name, vs_id=vector_store_id)
        log2file(f"Chat URL: {chat_url}")
        # URS is get, wieth q and top_k as params
        params = {
            "q": message,
            "top_k": 5
        }
        response = requests.get(chat_url, params=params, headers=headers, verify=False, timeout=1200)
        if response.status_code != 200:
            log2file("Error in LLM chat:" + response.text)
            return JsonResponse({'message': random.choice(errors_answer), 'status':'success'}, status=200)
        datas = response.json()
        message = datas.get("answer", random.choice(errors_answer))
        conversation_id = datas.get("conversation_id", "")
        report.conversation_id = conversation_id
        report.save()
        return JsonResponse({'message': message, 'status': 'success'})
    except Exception as e:
        log2file (show_exc(e))
        return JsonResponse({'error': show_exc(e)}, status=500)
    
def get_interpretation(collection_uuid:str):
    try :
        tries = 0
        t0 = time.time()
        while ((time.time()) - t0 < 3.0): # Pause in order to allow previous summarization to complete
            time.sleep(0.1)

        obj = get_or_none(Report, collection_uuid, field="uuid")
        if obj is None:
            return JsonResponse({'error': 'Informe no encontrado'}, status=404)
        headers = {
            "Authorization": f"Bearer aaaa-bbbb-cccc-dddd"  # Replace with actual token if needed
        }
        log2file("Asking for interpretation to LLM microservice")
        interpretation_url = IA_LLM_URL + IA_LLM_ENDPOINTS["openai-interpretation"].format(vs_id=f"{obj.uuid}:{obj.vector_id}")
        response = JsonResponse({}, status=500)
        while tries < 3 and response.status_code != 200:
            response = requests.get(interpretation_url, headers=headers, verify=False, timeout=1200)
            tries += 1
        if response.status_code == 200:
            datas = response.json()
        else:
            log2file(f"Error interpreting report in microservicio: {response.text}")
            return JsonResponse({'error': f"Error interpreting report in microservicio: {response.text}"}, status=response.status_code)
        log2file("Interpretation completed")
        return datas

    except Exception as e:
        log2file(f"Error in interpretation_report_with_ia: {show_exc(e)}")
        return None
    
@group_required("employees")
def extract_personal_data(request):
    log2file("Extracting data request received")
    if request.method != "POST":
        log2file("Método no permitido")
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    try:
        log2file("Extracting personal data with IA")
        obj_id = get_param(request.POST, "obj_id")
        obj = get_or_none(Report, obj_id)
        if obj is None:
            return JsonResponse({'error': 'Informe no encontrado'}, status=404)
        log2file(f"Extracting personal data for report {obj.uuid}")
        datas = ""
        audios = obj.audios.all()
        transcriptions = []
        for audio in audios: 
            if audio.processed and audio.text != '' and len(audio.upload_id) < 5:
                transcriptions.append(audio.text)
        if transcriptions != []:
            transcriptions = list(reversed(transcriptions))
            tmp_file_path = f"/tmp/{obj.uuid}_{audios.first().id}_transcriptions.txt"
            with open(tmp_file_path, "w", encoding="utf-8", newline="") as f:
                f.writelines(transcriptions)
            with open(tmp_file_path, "rb") as f:
                upload_url = IA_LLM_URL + IA_LLM_ENDPOINTS["openai-upload-expte"].format(uuid=obj.uuid)
                headers = {
                    "Authorization": f"Bearer aaaa-bbbb-cccc-dddd"  # Replace with actual token if needed
                }
                log2file("Uploading report data to LLM microservice")
                response = requests.post(upload_url, files={'file': f}, data={'name':obj.uuid}, headers=headers, verify=False, timeout=1200)
                if response.status_code == 200:
                    upload_id = response.json().get("file_id", "")
                    for audio in audios:
                        audio.upload_id = upload_id
                        audio.save()
                else:
                    log2file(f"Error uploading data to microservicio: {response.text}")
                log2file("Uploaded report data to LLM microservice")
        personal_data = IA_LLM_URL + IA_LLM_ENDPOINTS["openai-personal-data"].format(vs_id=f"{obj.uuid}:{obj.vector_id}:{obj.conversation_id}")
        response = requests.get(personal_data, verify=False, timeout=1200)

        if response.status_code == 200:
            datas = response.json()
            try:
                import json
                datas = json.loads(datas)
            except:
                pass
        else:
            return JsonResponse({'error': f"Error extracting personal data in microservicio: {response.text}"}, status=response.status_code)
        return JsonResponse({'data': datas})
    except Exception as e:
        log2file(f"Error: {show_exc(e)}")
        return JsonResponse({'error': show_exc(e)}, status=500)

@group_required("employees")
def summarize_report_with_ia(request):
    log2file("Summarizing report with IA")
    return JsonResponse({'message': 'Endpoint deshabilitado temporalmente.'}, status=200)
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
            reset_url = IA_LLM_URL + IA_LLM_ENDPOINTS["reset-expte"].format(uuid=obj.uuid)
            load_context_url = IA_LLM_URL + IA_LLM_ENDPOINTS["load-context"].format(uuid=obj.uuid) + "?force=true"
            upload_url = IA_LLM_URL + IA_LLM_ENDPOINTS["upload_expte"].format(uuid=obj.uuid)
            headers = {
                "Authorization": f"Bearer aaaa-bbbb-cccc-dddd"  # Replace with actual token if needed
            }
            log2file("\tClearing previous report data in LLM microservice")
            # response = requests.delete(remove_url, headers=headers, verify=False, timeout=1200)
            response = requests.delete(reset_url, headers=headers, verify=False, timeout=1200)
            log2file("\tLoading context in LLM microservice")
            response = requests.get(load_context_url, headers=headers, verify=False, timeout=1200)
            log2file("\tUploading report data to LLM microservice")
            response = requests.post(upload_url, files={'file': f}, data={'name':obj.uuid}, headers=headers, verify=False, timeout=1200)

            if response.status_code != 200:
                return JsonResponse({'error': f"Error uploading data to microservicio: {response.text}"}, status=response.status_code)
        log2file("Uploaded report data to LLM microservice")
        personal_data = IA_LLM_URL + IA_LLM_ENDPOINTS["personal-data"].format(uuid=obj.uuid)
        response = requests.get(personal_data, verify=False, timeout=1200)
        if response.status_code == 200:
            datas = response.json()
        else:
            return JsonResponse({'error': f"Error summarizing report in microservicio: {response.text}"}, status=response.status_code)

        return JsonResponse({'data': datas})
    except Exception as e:
        return JsonResponse({'error': show_exc(e)}, status=500)
    
@group_required("employees")
def interpretation_report_with_ia(request):
    try:
        log2file("Interpreting report with IA")
        if request.method != "POST":
            return JsonResponse({'error': 'Método no permitido'}, status=405)
        try :
            tries = 0
            t0 = time.time()
            while ((time.time()) - t0 < 3.0): # Pause in order to allow previous summarization to complete
                time.sleep(0.1)

            obj_id = get_param(request.POST, "obj_id")
            obj = get_or_none(Report, obj_id)
            obj.save()
            if obj is None:
                return JsonResponse({'error': 'Informe no encontrado'}, status=404)
            headers = {
                "Authorization": f"Bearer aaaa-bbbb-cccc-dddd"  # Replace with actual token if needed
            }
            log2file("Asking for interpretation to LLM microservice")
            interpretation_url = IA_LLM_URL + IA_LLM_ENDPOINTS["openai-interpretation"].format(vs_id=f"{obj.uuid}:{obj.vector_id}")
            response = JsonResponse({}, status=500)
            while tries < 3 and response.status_code != 200:
                response = requests.get(interpretation_url, headers=headers, verify=False, timeout=1200)
                tries += 1
            if response.status_code == 200:
                datas = response.json()
            else:
                log2file(f"Error interpreting report in microservicio: {response.text}")
                return JsonResponse({'error': f"Error interpreting report in microservicio: {response.text}"}, status=response.status_code)
            log2file("Interpretation completed")
            return JsonResponse({'data': datas})
        except Exception as e:
            log2file(f"Error in interpretation_report_with_ia: {show_exc(e)}")
            return JsonResponse({'error': show_exc(e)}, status=500)
    except Exception as e:
        log2file(f"Error in interpretation_report_with_ia outer: {show_exc(e)}")
        return JsonResponse({'error': show_exc(e)}, status=500)


def transcribe_audio_old(audio_file, obj):
    response = requests.post(IA_SPEECH_TO_TEXT_URL, files={'audio': audio_file}, verify=False)
    if response.status_code == 200:
        #log2file(response.json())
        obj.text = response.json()['texto']
        obj.processed = True
        obj.save()

        return JsonResponse({'texto': obj.text, 'status': 'ok'})
    else:
        raise Exception(f"Error en microservicio: {response.text}")
    
def transcribe_audio(audio_file, obj):
    response = requests.post(IA_SPEECH_TO_TEXT_URL, files={'audio': audio_file.file}, verify=False)

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

        obj.text = texto
        obj.processed = True
        obj.save()

        return JsonResponse({'texto': obj.text, 'status': 'ok'})
    else:
        log2file(f"Error transcribing audio: {response.text}")
        raise Exception(f"Error en microservicio: {response.text}")
    
    
def retranscribe_audio(request):
    if request.method != "POST":
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    obj_id = get_param(request.POST, "obj_id")
    obj = get_or_none(ReportAudio, obj_id)
    if obj is None:
        return JsonResponse({'error': 'Audio no encontrado'}, status=404)
    try:
        log2file(f"Retranscribing audio ID {obj.audio.file.name}")
        response = transcribe_audio(obj.audio, obj)
        return response
    except Exception as e:
        return JsonResponse({'error': show_exc(e)}, status=500)
    

def assistant_start_voice_turn(request):
    try:
        log2file("Starting voice turn for assistant")
        if request.method != "POST":
            return JsonResponse({'error': 'Método no permitido'}, status=405)
        # Lógica para iniciar el turno de voz del asistente

        audio = request.FILES.get("audio", None)
        if audio is None:
            return JsonResponse({'error': 'No se ha proporcionado audio'}, status=400)
        # Aquí puedes procesar el archivo de audio como desees
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
            return JsonResponse({'texto': texto, 'status': 'ok', 'conversation_id': '12345', 'transcript': texto, 'answer': f'{texto}'})
        else:
            return JsonResponse({'error': 'Error al transcribir audio'}, status=500)    
    except Exception as e:
        log2file(f"Error: {show_exc(e)}")
        return JsonResponse({'error': 'Error al procesar la solicitud'}, status=500)
    
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
        log2file(f"Error: {show_exc(e)}")
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
        log2file(f"Error: {show_exc(e)}")
    return JsonResponse({'error': 'Error al cargar el formulario'}, status=500)
    
def health_check(request):
    """Endpoint de salud para verificar que la vista funciona"""
    return JsonResponse({'status': 'ok', 'service': 'audio_stream'})

def agents_assistant(request, report_id=None):
    return render(request, "agents/assistant.html", {"report_id": report_id})