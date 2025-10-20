from django.urls import path
from . import views, auto_views

urlpatterns = [ 
    path('home', views.index, name='index'),

    #---------------------- REPORTS -----------------------
    path('reports', views.reports, name='reports'),
    path('reports/list', views.reports_list, name='reports-list'),
    path('reports/search', views.reports_search, name='reports-search'),
    path('reports/form', views.reports_form, name='reports-form'),
    path('reports/remove', views.reports_remove, name='reports-remove'),
    path('reports/audios', views.reports_audios, name='reports-audios'),
    path('reports/print/<int:obj_id>', views.reports_print, name='reports-print'),
 
    #---------------------- EMPLOYEES -----------------------
    path('employees', views.employees, name='employees'),
    path('employees/list', views.employees_list, name='employees-list'),
    path('employees/search', views.employees_search, name='employees-search'),
    path('employees/form', views.employees_form, name='employees-form'),
    path('employees/remove', views.employees_remove, name='employees-remove'),
    path('employees/save-email', views.employees_save_email, name='employees-save-email'),
    path('employees/export', views.employees_export, name='employees-export'),
    path('employees/import', views.employees_import, name='employees-import'),


    #------------------------- SPEECH TO TEXT -----------------------
    path('set-audio-report', views.set_audio_report, name='set-audio-report'),

    #---------------------- AUTO -----------------------
    path('autosave_field/', auto_views.autosave_field, name='autosave_field'),
    path('autoremove_obj/', auto_views.autoremove_obj, name='autoremove_obj'),
]

