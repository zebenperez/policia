from django.urls import path, re_path
from assistant import views, z_views


urlpatterns = [
    path('', views.agents_assistant, name="assistant"),
    path('chat-with-llm', views.chat_with_llm, name="chat-with-llm"),
    path('<int:report_id>', views.agents_assistant, name="assistant"),
    path('start-voice-turn', views.assistant_start_voice_turn, name="api-assistant-start-voice-turn"),

    path('api/health/', views.health_check, name='health_check'),
]

