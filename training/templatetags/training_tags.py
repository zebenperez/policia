from django import template
import markdown

register = template.Library()

@register.filter
def md(value):
    try:
        return markdown.markdown(str(value))
    except:
        return value
