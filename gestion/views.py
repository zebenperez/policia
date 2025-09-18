from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import os, csv, requests

from policia.settings import IA_SERVICES_URL
from policia.decorators import group_required
from policia.commons import get_float, get_int, get_or_none, get_param, get_session, set_session, show_exc, generate_qr, csv_export
from .models import Employee, Report, ReportAudio, Station
#from .report_lib import get_complainant_datas

ACCESS_PATH="{}/gestion/assistances/client/".format(settings.MAIN_URL)


@group_required("admins",)
def index(request):
    return redirect(reports)

'''
    REPORTS
'''
def get_reports(request):
    #search_value = get_session(request, "s_emp_name")
    #filters_to_search = ["name__icontains",]
    #full_query = Q()
    #if search_value != "":
    #    for myfilter in filters_to_search:
    #        full_query |= Q(**{myfilter: search_value})
    #return Employee.objects.filter(full_query)
    return Report.objects.all()

@group_required("admins",)
def reports(request):
    return render(request, "reports/reports.html", {"items": get_reports(request)})

@group_required("admins",)
def reports_list(request):
    return render(request, "reports/reports-list.html", {"items": get_reports(request)})

@group_required("admins",)
def reports_search(request):
    #set_session(request, "s_emp_name", get_param(request.GET, "s_emp_name"))
    #set_session(request, "s_emp_idate", get_param(request.GET, "s_emp_idate"))
    #set_session(request, "s_emp_edate", get_param(request.GET, "s_emp_edate"))
    return render(request, "reports/reports-list.html", {"items": get_reports(request)})

@group_required("admins",)
def reports_form(request):
    obj_id = get_param(request.GET, "obj_id")
    obj = get_or_none(Report, obj_id)
    #if obj == None:
    #    obj = Report.objects.create()
    return render(request, "reports/reports-form.html", {'obj': obj})

@group_required("admins",)
def reports_remove(request):
    obj = get_or_none(Report, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        for audio in obj.audios.all():
            audio.audio.delete(save=True)
        obj.delete()
    return render(request, "reports/reports-list.html", {"items": get_reports(request)})

@group_required("admins",)
def reports_audios(request):
    obj_id = get_param(request.GET, "obj_id")
    obj = get_or_none(Report, obj_id)
    return render(request, "reports/reports-audios.html", {'obj': obj})

@group_required("admins",)
def reports_print(request, obj_id):
    obj = get_or_none(Report, obj_id)
    #datas = get_complainant_datas(obj.text)
    #response = requests.post('http://localhost:8001/get_datas', params={'texto': obj.text})
    datas = ""
    audio = obj.audios.all().first()
    if audio != None:
        response = requests.post(IA_SERVICES_URL, params={'texto': audio.text})
        datas = ""
        if response.status_code == 200:
            #print(response.json())
            datas = response.json()
            #return response.json()['texto']
        else:
            raise Exception(f"Error en microservicio: {response.text}")

    print(datas)
    return render(request, "reports/print.html", {"obj": obj, "datas": datas})


'''
    EMPLOYEES
'''
def get_employees(request):
    search_value = get_session(request, "s_emp_name")
    filters_to_search = ["name__icontains",]
    full_query = Q()
    if search_value != "":
        for myfilter in filters_to_search:
            full_query |= Q(**{myfilter: search_value})
    return Employee.objects.filter(full_query)

@group_required("admins",)
def employees(request):
    #init_session_date(request, "s_emp_idate")
    #init_session_date(request, "s_emp_edate")
    return render(request, "employees/employees.html", {"items": get_employees(request)})

@group_required("admins",)
def employees_list(request):
    return render(request, "employees/employees-list.html", {"items": get_employees(request)})

@group_required("admins",)
def employees_search(request):
    set_session(request, "s_emp_name", get_param(request.GET, "s_emp_name"))
    set_session(request, "s_emp_idate", get_param(request.GET, "s_emp_idate"))
    set_session(request, "s_emp_edate", get_param(request.GET, "s_emp_edate"))
    return render(request, "employees/employees-list.html", {"items": get_employees(request)})

@group_required("admins",)
def employees_form(request):
    obj_id = get_param(request.GET, "obj_id")
    obj = get_or_none(Employee, obj_id)
    if obj == None:
        obj = Employee.objects.create()
    return render(request, "employees/employees-form.html", {'obj': obj})

@group_required("admins",)
def employees_remove(request):
    obj = get_or_none(Employee, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        if obj.user != None:
            obj.user.delete()
        obj.delete()
    return render(request, "employees/employees-list.html", {"items": get_employees(request)})

@group_required("admins",)
def employees_save_email(request):
    try:
        obj = get_or_none(Employee, get_param(request.GET, "obj_id"))
        obj.email = get_param(request.GET, "value")
        obj.save()
        obj.save_user()
        return HttpResponse("Saved!")
    except Exception as e:
        return HttpResponse("Error: {}".format(e))

@group_required("admins",)
def employees_export(request):
    header = ['Nombre', 'Teléfono', 'Email', 'PIN', 'DNI', 'Horas trabajadas', 'Minutos trabajados']
    values = []
    items = get_employees(request)
    for item in items:
        hours, minutes = item.worked_time(request.session["s_emp_idate"], request.session["s_emp_edate"])
        row = [item.name, item.phone, item.email, item.pin, item.dni, hours, minutes]
        values.append(row)
    return csv_export(header, values, "empleados")

@group_required("admins",)
def employees_import(request):
    f = request.FILES["file"]
    lines = f.read().decode('latin-1').splitlines()
    i = 0
    for line in lines:
        if i > 0:
            l = line.split(";")
            #print(l)
            name = "{} {}".format(l[1], l[0])
            phone = l[2]
            email = l[7]
            dni = l[6]
            obj, created = Employee.objects.get_or_create(pin=dni, dni=dni, name=name, phone=phone, email=email)
            obj.save_user()
        i += 1
    return redirect("employees")

'''
    STATIONS
'''
def get_stations(request):
    search_value = get_session(request, "s_sta_name")
    filters_to_search = ["name__icontains",]
    full_query = Q()
    if search_value != "":
        for myfilter in filters_to_search:
            full_query |= Q(**{myfilter: search_value})
    return Station.objects.filter(full_query)

@group_required("admins",)
def stations(request):
    return render(request, "stations/stations.html", {"items": get_stations(request)})

@group_required("admins",)
def stations_list(request):
    return render(request, "stations/stations-list.html", {"items": get_stations(request)})

@group_required("admins",)
def stations_search(request):
    set_session(request, "s_sta_name", get_param(request.GET, "s_sta_name"))
    return render(request, "stations/stations-list.html", {"items": get_stations(request)})

@group_required("admins",)
def stations_form(request):
    obj_id = get_param(request.GET, "obj_id")
    obj = get_or_none(Station, obj_id)
    if obj == None:
        obj = Station.objects.create()
    return render(request, "stations/stations-form.html", {'obj': obj})

@group_required("admins",)
def stations_remove(request):
    obj = get_or_none(Station, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.delete()
    return render(request, "stations/stations-list.html", {"items": get_stations(request)})

'''
    Speech to text
'''
@csrf_exempt
def set_audio_report(request):
    #print("--1--")
    #print(request.POST)
    token = get_param(request.POST, "token")
    text = get_param(request.POST, "text")
    report = get_or_none(Report, get_param(request.POST, "report"))
    if token == "1234":
        #print("--2--")
        #print(text)
        report.text = text
        report.save()
    return HttpResponse("")

