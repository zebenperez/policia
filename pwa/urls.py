from django.urls import path, re_path
from pwa import views


urlpatterns = [
    path('', views.index, name="pwa-home"),
    path('home/', views.index, name="pwa-home"),
    path('login/', views.pin_login, name="pwa-login"),
    path('logoff/', views.pin_logout, name="pwa-logout"),

    # EMPLOYEES
    path('employee/home/', views.employee_home, name="pwa-employee"),
    path('employee/reports/', views.employee_reports, name="pwa-employee-reports"),
    path('employee/reports/new/', views.employee_reports_new, name="pwa-employee-reports-new"),
    path('employee/report/<int:obj_id>', views.employee_report, name="pwa-employee-report"),
    path('employee/report/print/<int:obj_id>', views.employee_report_print, name="pwa-employee-report-print"),
    path('employee/audio/save', views.employee_audio_save, name="pwa-employee-audio-save"),
    path('employee/audio/stream/<int:obj_id>', views.employee_audio_stream, name="pwa-employee-audio-stream"),
    path('employee/audio/stream-save', views.employee_audio_stream_save, name="pwa-employee-audio-stream-save"),
    path('employee/chatbot/', views.employee_chatbot, name="pwa-employee-chatbot"),

    # STREAM
    path('audio-stream/', views.audio_stream_view, name='audio_stream'),
    path('api/process-audio/', views.process_audio_chunk, name='process_audio'),
    path('api/health/', views.health_check, name='health_check'),
]

