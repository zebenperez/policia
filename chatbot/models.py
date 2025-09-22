from django.db import models
from django.contrib.auth.models import User

#class Conversation(models.Model):
#    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
#    session_key = models.CharField(max_length=100)
#    created_at = models.DateTimeField(auto_now_add=True)
#
#class Message(models.Model):
#    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
#    text = models.TextField()
#    is_user = models.BooleanField(default=True)
#    timestamp = models.DateTimeField(auto_now_add=True)
#
#    class Meta:
#        ordering = ['timestamp']
