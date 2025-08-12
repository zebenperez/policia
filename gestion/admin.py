from django.contrib import admin
from .models import *


admin.site.register(Assistance)

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
