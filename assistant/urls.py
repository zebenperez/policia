from django.urls import path, re_path
from assistant import views


urlpatterns = [
    path('', views.agents_assistant, name="assistant"),
    path('<int:report_id>', views.agents_assistant, name="assistant"),

    path('register/<int:plan>', views.register, name="register"),

    path('chat-list/', views.chat_list, name="chat-list"),
    path('chat-close/<int:obj_id>', views.chat_close, name="chat-close"),
    path('chat-with-llm', views.chat_with_llm, name="chat-with-llm"),
    path('start-voice-turn', views.assistant_start_voice_turn, name="api-assistant-start-voice-turn"),

    path('api/health/', views.health_check, name='health_check'),
]

