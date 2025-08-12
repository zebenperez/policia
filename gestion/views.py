from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from datetime import datetime
import os, csv

from asm.decorators import group_required
from asm.commons import get_float, get_int, get_or_none, get_param, get_session, set_session, show_exc, generate_qr, csv_export
from .models import Employee, Client, Assistance

ACCESS_PATH="{}/gestion/assistances/client/".format(settings.MAIN_URL)


def init_session_date(request, key):
    #if not key in request.session:
    set_session(request, key, datetime.now().strftime("%Y-%m-%d"))

def get_assistances(request):
    value = get_session(request, "s_name")
    i_date = datetime.strptime("{} 00:00".format(get_session(request, "s_idate")), "%Y-%m-%d %H:%M")
    e_date = datetime.strptime("{} 23:59".format(get_session(request, "s_edate")), "%Y-%m-%d %H:%M")

    kwargs = {"ini_date__gte": i_date, "ini_date__lte": e_date}
    if value != "":
        kwargs["employee__name__icontains"] = value

    return Assistance.objects.filter(**kwargs).order_by("-ini_date")

@group_required("Administradores",)
def index(request):
    init_session_date(request, "s_idate")
    init_session_date(request, "s_edate")
    return render(request, "index.html", {"item_list": get_assistances(request)})

@group_required("Administradores",)
def assistances_list(request):
    return render(request, "assistances-list.html", {"item_list": get_assistances(request)})

@group_required("Administradores",)
def assistances_search(request):
    set_session(request, "s_name", get_param(request.GET, "s_name"))
    set_session(request, "s_idate", get_param(request.GET, "s_idate"))
    set_session(request, "s_edate", get_param(request.GET, "s_edate"))
    return render(request, "assistances-list.html", {"item_list": get_assistances(request)})

@group_required("Administradores",)
def assistances_form(request):
    obj = get_or_none(Assistance, get_param(request.GET, "obj_id"))
    context = {'obj': obj, 'client_list': Client.objects.all(), 'emp_list': Employee.objects.all()}
    return render(request, "assistances-form.html", context)

@group_required("Administradores",)
def assistances_form_save(request):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    obj = get_or_none(Assistance, get_param(request.GET, "obj_id"))
    if obj == None:
        obj = Assistance.objects.create()
    obj.client = get_or_none(Client, get_param(request.GET, "client"))
    obj.employee = get_or_none(Employee, get_param(request.GET, "employee"))
    ini_date = get_param(request.GET, "ini_date")
    end_date = get_param(request.GET, "end_date")
    ini_time = get_param(request.GET, "ini_time")
    end_time = get_param(request.GET, "end_time")
    finish = get_param(request.GET, "finish")
    idate = datetime.strptime("{} {}".format(ini_date, ini_time), "%Y-%m-%d %H:%M")
    edate = datetime.strptime("{} {}".format(end_date, end_time), "%Y-%m-%d %H:%M")
    idate = idate.replace(tzinfo=ZoneInfo("Atlantic/Canary"))
    edate = edate.replace(tzinfo=ZoneInfo("Atlantic/Canary"))
    idate = idate.astimezone(ZoneInfo("UTC"))
    edate = edate.astimezone(ZoneInfo("UTC"))

    obj.ini_date = idate
    obj.end_date = edate
    obj.finish = True if finish != "" else False
    obj.save()
    return render(request, "assistances-list.html", {"item_list": get_assistances(request)})

@group_required("Administradores",)
def assistances_remove(request):
    obj = get_or_none(Assistance, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.delete()
    return render(request, "assistances-list.html", {"item_list": get_assistances(request)})

def assistances_client(request, client_id):
    return render(request, "assistances-client-error.html", {})

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

@group_required("Administradores",)
def employees(request):
    init_session_date(request, "s_emp_idate")
    init_session_date(request, "s_emp_edate")
    return render(request, "employees/employees.html", {"items": get_employees(request)})

@group_required("Administradores",)
def employees_list(request):
    return render(request, "employees/employees-list.html", {"items": get_employees(request)})

@group_required("Administradores",)
def employees_search(request):
    set_session(request, "s_emp_name", get_param(request.GET, "s_emp_name"))
    set_session(request, "s_emp_idate", get_param(request.GET, "s_emp_idate"))
    set_session(request, "s_emp_edate", get_param(request.GET, "s_emp_edate"))
    return render(request, "employees/employees-list.html", {"items": get_employees(request)})

@group_required("Administradores",)
def employees_form(request):
    obj_id = get_param(request.GET, "obj_id")
    obj = get_or_none(Employee, obj_id)
    if obj == None:
        obj = Employee.objects.create()
    return render(request, "employees/employees-form.html", {'obj': obj})

@group_required("Administradores",)
def employees_remove(request):
    obj = get_or_none(Employee, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        if obj.user != None:
            obj.user.delete()
        obj.delete()
    return render(request, "employees/employees-list.html", {"items": get_employees(request)})

@group_required("Administradores",)
def employees_save_email(request):
    try:
        obj = get_or_none(Employee, get_param(request.GET, "obj_id"))
        obj.email = get_param(request.GET, "value")
        obj.save()
        obj.save_user()
        return HttpResponse("Saved!")
    except Exception as e:
        return HttpResponse("Error: {}".format(e))

@group_required("Administradores",)
def employees_export(request):
    header = ['Nombre', 'Teléfono', 'Email', 'PIN', 'DNI', 'Horas trabajadas', 'Minutos trabajados']
    values = []
    items = get_employees(request)
    for item in items:
        hours, minutes = item.worked_time(request.session["s_emp_idate"], request.session["s_emp_edate"])
        row = [item.name, item.phone, item.email, item.pin, item.dni, hours, minutes]
        values.append(row)
    return csv_export(header, values, "empleados")

@group_required("Administradores",)
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
    CLIENTS
'''
def get_clients(request):
    search_value = get_session(request, "s_cli_name")
    filters_to_search = ["name__icontains",]
    full_query = Q()
    if search_value != "":
        for myfilter in filters_to_search:
            full_query |= Q(**{myfilter: search_value})
    return Client.objects.filter(full_query).order_by("-id")[:50]

@group_required("Administradores",)
def clients(request):
    return render(request, "clients/clients.html", {"items": get_clients(request)})

@group_required("Administradores",)
def clients_list(request):
    return render(request, "clients/clients-list.html", {"items": get_clients(request)})

@group_required("Administradores",)
def clients_search(request):
    set_session(request, "s_cli_name", get_param(request.GET, "s_cli_name"))
    return render(request, "clients/clients-list.html", {"items": get_clients(request)})

@group_required("Administradores",)
def clients_form(request):
    obj_id = get_param(request.GET, "obj_id")
    obj = get_or_none(Client, obj_id)
    new = False
    if obj == None:
        obj = Client.objects.create()
        url = "{}{}".format(ACCESS_PATH, obj.id)
        path = os.path.join(settings.BASE_DIR, "static", "images", "logo-asistencia-canaria.jpg")
        img_data = ContentFile(generate_qr(url, path))
        obj.qr.save('qr_{}.png'.format(obj.id), img_data, save=True)
        new = True
    return render(request, "clients/clients-form.html", {'obj': obj, 'new': new})

@group_required("Administradores",)
def clients_remove(request):
    obj = get_or_none(Client, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.qr.delete(save=True)
        obj.delete()
    return render(request, "clients/clients-list.html", {"items": get_clients(request)})

@group_required("Administradores",)
def clients_print_all_qr(request):
    return render(request, "clients/clients-print-all-qr.html", {"item_list": Client.objects.filter(inactive=False)})

@group_required("Administradores",)
def clients_print_qr(request, obj_id):
    return render(request, "clients/clients-print-qr.html", {"obj": get_or_none(Client, obj_id)})

@group_required("Administradores",)
def clients_assistances(request, obj_id):
    return render(request, "clients/clients-assistances.html", {"obj": get_or_none(Client, obj_id)})

'''
    REPORT
'''
def get_total_duration(item_list):
    total = 0
    for item in item_list:
        total += get_int(item.duration)
    return total

def get_report(request):
    cli = get_session(request, "s_rep_cli")
    emp = get_session(request, "s_rep_emp")
    i_date = datetime.strptime("{} 00:00".format(get_session(request, "s_rep_idate")), "%Y-%m-%d %H:%M")
    e_date = datetime.strptime("{} 23:59".format(get_session(request, "s_rep_edate")), "%Y-%m-%d %H:%M")

    kwargs = {"ini_date__range": (i_date, e_date)}
    if cli != "":
        kwargs["client__name__icontains"] = cli
    if emp != "":
        kwargs["employee__name__icontains"] = emp

    return Assistance.objects.filter(**kwargs)

@group_required("Administradores",)
def report(request):
    init_session_date(request, "s_rep_idate")
    init_session_date(request, "s_rep_edate")
    return render(request, "report/report.html", {"items": []})
    #return render(request, "report/report.html", {"items": get_report(request)})

@group_required("Administradores",)
def report_list(request):
    item_list = get_report(request)
    return render(request, "report/report-list.html", {"items": item_list, "duration": get_total_duration(item_list)})

@group_required("Administradores",)
def report_search(request):
    set_session(request, "s_rep_emp", get_param(request.GET, "s_rep_emp"))
    set_session(request, "s_rep_cli", get_param(request.GET, "s_rep_cli"))
    set_session(request, "s_rep_idate", get_param(request.GET, "s_rep_idate"))
    set_session(request, "s_rep_edate", get_param(request.GET, "s_rep_edate"))
    item_list = get_report(request)
    return render(request, "report/report-list.html", {"items": item_list, "duration": get_total_duration(item_list)})

@group_required("Administradores",)
def report_export(request):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    header = ['Cliente', 'Empleado', 'Fecha de inicio', 'Fecha de fin', 'Duración del servicio', 'Finalizada']
    values = []
    items = get_report(request)
    for item in items:
        ini_date = item.ini_date.astimezone(ZoneInfo("Atlantic/Canary"))
        idate = ini_date.strftime("%d-%m-%Y %H:%M")
        end_date = item.end_date.astimezone(ZoneInfo("Atlantic/Canary"))
        edate = end_date.strftime("%d-%m-%Y %H:%M")
        finish = "Si" if item.finish else "No"
        client = item.client.name if item.client != None else ""
        emp = item.employee.name if item.employee != None else ""
        row = [client, emp, idate, edate, item.duration, finish]
        values.append(row)
    return csv_export(header, values, "empleados")


