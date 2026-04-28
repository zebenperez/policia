from django.contrib import admin
from .models import *


class BaseDocAdmin(admin.ModelAdmin):
    list_display = ('id', 'uuid', 'vuuid', 'doc')

class ConfigAdmin(admin.ModelAdmin):
    list_display = ('key', 'value')

class ReportAdmin(admin.ModelAdmin):
    list_display = ('code', 'conversation_id', 'date', 'employee')

class ReportAudioAdmin(admin.ModelAdmin):
    list_display = ('report', 'text')

class SubmodeAdmin(admin.ModelAdmin):
    list_display = ('mode', 'code', 'name', 'title', 'block', 'color', 'order')

admin.site.register(BaseDoc, BaseDocAdmin)
admin.site.register(Config, ConfigAdmin)
admin.site.register(Employee)
admin.site.register(Report, ReportAdmin)
admin.site.register(ReportAudio, ReportAudioAdmin)
admin.site.register(Station)
admin.site.register(Submode, SubmodeAdmin)

#class FacilityTypeAdmin(admin.ModelAdmin):
#    list_display = ('code', 'name', 'order', 'operation_time', 'dashboard')
#
#class TruckTypeAdmin(admin.ModelAdmin):
#    list_display = ('brand', 'model', 'year')
#
#
#class WasteInFacilityAdmin(admin.ModelAdmin):
#    list_display = ('code', 'facility', 'waste', 'filling_degree', 'toRoute')
#    list_filter = ('facility',)
#
#admin.site.register(FacilityType, FacilityTypeAdmin)
##admin.site.register(Priority, PriorityAdmin)
#admin.site.register(TruckType, TruckTypeAdmin)
#admin.site.register(WasteInFacility, WasteInFacilityAdmin)
#
