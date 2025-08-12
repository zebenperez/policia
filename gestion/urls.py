from django.urls import path
from . import views, auto_views

urlpatterns = [ 
    path('home', views.index, name='index'),
    path('assistances/list', views.assistances_list, name='assistances-list'),
    path('assistances/search', views.assistances_search, name='assistances-search'),
    path('assistances/form', views.assistances_form, name='assistances-form'),
    path('assistances/form-save', views.assistances_form_save, name='assistances-form-save'),
    path('assistances/remove', views.assistances_remove, name='assistances-remove'),
    path('assistances/client/<int:client_id>/', views.assistances_client, name='assistances-client'),

    #---------------------- EMPLOYEES -----------------------
    path('employees', views.employees, name='employees'),
    path('employees/list', views.employees_list, name='employees-list'),
    path('employees/search', views.employees_search, name='employees-search'),
    path('employees/form', views.employees_form, name='employees-form'),
    path('employees/remove', views.employees_remove, name='employees-remove'),
    path('employees/save-email', views.employees_save_email, name='employees-save-email'),
    path('employees/export', views.employees_export, name='employees-export'),
    path('employees/import', views.employees_import, name='employees-import'),

    #------------------------- CLIENTS -----------------------
    path('clients', views.clients, name='clients'),
    path('clients/list', views.clients_list, name='clients-list'),
    path('clients/search', views.clients_search, name='clients-search'),
    path('clients/form', views.clients_form, name='clients-form'),
    path('clients/remove', views.clients_remove, name='clients-remove'),
    path('clients/print-all-qr', views.clients_print_all_qr, name='clients-print-all-qr'),
    path('clients/print-qr/<int:obj_id>', views.clients_print_qr, name='clients-print-qr'),
    path('clients/assistances/<int:obj_id>', views.clients_assistances, name='clients-assistances'),

    #---------------------- ASSISTANCES -----------------------
    path('report', views.report, name='report'),
    path('report/list', views.report_list, name='report-list'),
    path('report/search', views.report_search, name='report-search'),
    path('report/export', views.report_export, name='report-export'),

    #---------------------- AUTO -----------------------
    path('autosave_field/', auto_views.autosave_field, name='autosave_field'),
    path('autoremove_obj/', auto_views.autoremove_obj, name='autoremove_obj'),
]

