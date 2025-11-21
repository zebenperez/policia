from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from datetime import datetime

from policia.decorators import group_required
from policia.commons import get_param, get_or_none
from .models import Training, TrainingDoc, TrainingPrompt
from .claude import procesar_pdf_y_pregunta


api_key = "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"

'''
    TRAINING
'''
@group_required("admins")
def training_home(request, obj_id=0):
    #obj = Training.objects.all().order_by("-date").first()
    t_list = Training.objects.all().order_by("-date")
    obj = get_or_none(Training, obj_id) if obj_id > 0 else t_list[0]
    return render(request, "training/home.html", {"obj": obj, "t_list": t_list})

@group_required("admins")
def training_new(request):
    Training.objects.create()
    return redirect("training-home")

@group_required("admins")
def docs_upload(request):
    obj = get_or_none(Training, get_param(request.POST, "obj_id"))
    if obj != None:
        file_list = request.FILES.getlist('file')
        for f in file_list:
            td = TrainingDoc.objects.create(training=obj, doc=f)
            #print(f)
    return render(request, "training/doc-list.html", {"obj": obj})

@group_required("admins")
def docs_remove(request):
    obj = get_or_none(TrainingDoc, get_param(request.GET, "obj_id"))
    if obj != None:
        obj.doc.delete(save=True)
        training = obj.training
        obj.delete()
    return render(request, "training/doc-list.html", {"obj": training})

@group_required("admins")
def send_prompt(request):
    obj = get_or_none(Training, get_param(request.GET, "obj_id"))
    value = get_param(request.GET, "value")
    tp = TrainingPrompt.objects.create(training=obj, text=value)
    #doc = obj.docs.all().first()
    docs = [item.doc.url for item in obj.docs.all()]
    resp = procesar_pdf_y_pregunta(f"/var/www/django/policia", docs, value, api_key)
    #resp = procesar_pdf_y_pregunta(f"/var/www/django/policia{doc.doc.url}", value, api_key)
    tp.response = resp
    tp.save()
    return render(request, "training/chat.html", {"obj": obj})


