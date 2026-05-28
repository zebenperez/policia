from django.urls import path, re_path
from assistant import views


urlpatterns = [
    path('', views.assistant, name="assistant"),
    path('agents', views.agents_assistant, name="agents-assistant"),
    path('landing', views.landing, name="landing"),
    path('stats', views.stats, name="stats"),
    path('assistant/chat/<slug:mode>', views.assistant_chat, name="assistant-chat"),
    #path('assistant/intervention', views.intervention, name="assistant-intervention"),
    #path('assistant/consultation', views.consultation, name="assistant-consultation"),
    #path('<int:report_id>', views.agents_assistant, name="assistant"),

    path('register/<int:plan>', views.register, name="register"),

    path('chat-list/', views.chat_list, name="chat-list"),
    path('chat-close/<int:obj_id>', views.chat_close, name="chat-close"),
    path('chat-open/<int:obj_id>', views.chat_open, name="chat-open"),
    path('chat-report-count/', views.chat_report_count, name="chat-report-count"),
    path('chat-with-llm', views.chat_with_llm, name="chat-with-llm"),
    path('start-voice-turn', views.assistant_start_voice_turn, name="api-assistant-start-voice-turn"),

    path('set-tokens-info', views.set_tokens_info, name="set-tokens-info"),

    path('api/health/', views.health_check, name='health_check'),
]

