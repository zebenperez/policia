from django.urls import path, re_path
from training import views


urlpatterns = [
    # TRAINING
    path('', views.training_home, name="training-home"),
    path('<int:obj_id>', views.training_home, name="training-home"),
    path('new/', views.training_new, name='training-new'),
    path('docs-upload/', views.docs_upload, name='training-docs-upload'),
    path('docs-remove/', views.docs_remove, name='training-docs-remove'),
    path('send-prompt/', views.send_prompt, name='training-send-prompt'),
]

