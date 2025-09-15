from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from datetime import datetime

from policia.decorators import group_required_pwa
from policia.commons import user_in_group, get_or_none, get_param
from gestion.models import Employee, Report

import subprocess
import threading
import requests


@group_required_pwa("employees")
def index(request):
    try:
        return redirect(reverse('pwa-employee'))
    except:
        return redirect(reverse('pwa-login'))

def pin_login(request):
    CONTROL_KEY = "SZRf2QMpIfZHPEh0ib7YoDlnnDp5HtjDqbAw"
    msg = ""  
    if request.method == "POST":
        context =  {}
        msg = "Operación no permitida"
        pin = request.POST.get('pin', None)
        control_key = request.POST.get('control_key', None)
        if pin != None and control_key != None:
            if control_key == CONTROL_KEY:
                try:
                    emp = get_or_none(Employee, pin, "pin")
                    login(request, emp.user)
                    request.session['pwa_app_session'] = True
                    return redirect(reverse('pwa-employee'))
                except Exception as e:
                    msg = "Pin no válido"
                    print(e)
            else:
                msg = "Bad control"
    return render(request, "pwa-login.html", {'msg': msg})

def pin_logout(request):
    logout(request)
    return redirect(reverse('pwa-login'))

'''
    EMPLOYEES
'''
@group_required_pwa("employees")
def employee_home(request):
    return render(request, "pwa/employees/home.html", {})

#def transcribe_audio(file, obj_id):
def transcribe_audio(audio_file, obj):
    #model = whisper.load_model("base")
    #result = model.transcribe(audio_file, language="es")
    #obj.text = result
    #obj.save()
    #subprocess.run(["python3", "/var/www/django/policia/transcribir.py", file, str(obj_id)])
    response = requests.post('http://localhost:8001/transcribir', files={'audio': audio_file})
    if response.status_code == 200:
        #print(response.json())
        obj.text = response.json()['texto']
        obj.save()
        return ""
        #return response.json()['texto']
    else:
        raise Exception(f"Error en microservicio: {response.text}")

@group_required_pwa("employees")
def employee_audio_save(request):
    #concept = get_param(request.POST, "concept")
    concept = ""
    audio = None
    if "audio" in request.FILES and request.FILES["audio"] != "":
        audio = request.FILES["audio"]
        concept = "Esperando traducción de audio..."
    if concept != "" or audio != None:
        report = Report.objects.create(text=concept, audio=audio, employee=request.user.employee)
        if "audio" in request.FILES and request.FILES["audio"] != "":
            t = threading.Thread(target=transcribe_audio, args=[report.audio, report], daemon=True)
            #t = threading.Thread(target=transcribe_audio, args=[report.audio.url, report.id], daemon=True)
            t.start()
    return render(request, "pwa/employees/audio_sended.html", {})
    #return redirect(reverse('pwa-employee'))

