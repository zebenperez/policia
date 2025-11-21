from django.urls import path
from . import views

urlpatterns = [
    path('api/', views.chatbot_api, name='chatbot_api'),
    path('upload/', views.upload_file, name='agents-upload-file-to-llm'),
    path('', views.chatbot_view, name='chatbot'),
]

