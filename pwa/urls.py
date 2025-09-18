from django.urls import path
from pwa import views


urlpatterns = [
    path('', views.index, name="pwa-home"),
    path('home/', views.index, name="pwa-home"),
    path('login/', views.pin_login, name="pwa-login"),
    path('logoff/', views.pin_logout, name="pwa-logout"),

    # EMPLOYEES
    path('employee/home/', views.employee_home, name="pwa-employee"),
    path('employee/reports/', views.employee_reports, name="pwa-employee-reports"),
    path('employee/report/<int:obj_id>', views.employee_report, name="pwa-employee-report"),
    path('employee/audio/save', views.employee_audio_save, name="pwa-employee-audio-save"),
]

