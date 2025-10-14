from django.urls import path, re_path
from agents import views


urlpatterns = [
    # AGENTS
    path('', views.agents_home, name="agents-home"),
    path('report/<int:obj_id>', views.agents_report, name="agents-report"),
    path('report/new/', views.agents_report_new, name="agents-report-new"),
    path('audio/save', views.agents_audio_save, name="agents-audio-save"),
    #path('reports/', views.agents_reports, name="agents-reports"),
#    path('employee/report/print/<int:obj_id>', views.employee_report_print, name="pwa-employee-report-print"),
#    path('employee/audio/stream/<int:obj_id>', views.employee_audio_stream, name="pwa-employee-audio-stream"),
#    path('employee/audio/stream-save', views.employee_audio_stream_save, name="pwa-employee-audio-stream-save"),
#    path('employee/chatbot/', views.employee_chatbot, name="pwa-employee-chatbot"),
#
    # STREAM
#    path('audio-stream/', views.audio_stream_view, name='audio_stream'),
#    path('api/process-audio/', views.process_audio_chunk, name='process_audio'),
    path('api/health/', views.health_check, name='health_check'),
]

