# chatbot/templatetags/chatbot_tags.py
from django import template

register = template.Library()

@register.inclusion_tag('chatbot/partials/chatbot_widget.html')
def chatbot_widget():
    return {}
