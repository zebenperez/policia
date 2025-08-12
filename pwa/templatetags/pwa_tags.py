from django import template
from asm.commons import show_exc
import datetime

register = template.Library()

@register.filter
def verified(date_str):
    try:
        date = datetime.datetime.strptime(date_str[:10], '%d-%m-%Y')
        return (date.date() <= datetime.date.today())
    except Exception as e:
        print (show_exc(e))
        return False

@register.filter
def local_time(mydate):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    utc_now = mydate.replace(tzinfo=ZoneInfo("UTC"))
    canary_time = utc_now.astimezone(ZoneInfo("Atlantic/Canary"))
    canary_time = canary_time.replace(tzinfo=ZoneInfo("UTC"))

    return canary_time
