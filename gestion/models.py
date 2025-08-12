from django.conf import settings
from django.contrib.auth.models import User, Group
from django.db import models
from django.utils.translation import gettext_lazy as _ 

import datetime


'''
    EMPLOYEE
'''
class Employee(models.Model):
    pin = models.CharField(max_length=20, verbose_name = _('PIN'), default="")
    dni = models.CharField(max_length=20, verbose_name = _('DNI'), default="")
    name = models.CharField(max_length=200, verbose_name = _('Razón Social'), default="")
    phone = models.CharField(max_length=20, verbose_name = _('Teléfono de contacto'), null=True, default = '0000000000')
    email = models.EmailField(verbose_name = _('Email de contacto'), default="", null=True)
    user = models.OneToOneField(User, verbose_name='Usuario', on_delete=models.CASCADE, null=True, blank=True, related_name='employee')

    def __str__(self):
        return self.name

    def save_user(self):
        if self.user == None:
            self.user = User.objects.create_user(username=self.email, email=self.email)
            self.save()
            group = Group.objects.get(name='employees') 
            group.user_set.add(self.user)
        else:
            self.user.username = self.email
            self.user.save()

    def worked_time(self, ini_date, end_date):
        idate = "{} 00:00".format(ini_date)
        edate = "{} 23:59".format(end_date)
        item_list = self.assistances.filter(ini_date__gte=idate, end_date__lte=edate)
        #item_list = self.assistances.filter(ini_date__gte=ini_date, end_date__lte=end_date)
        hours = 0
        minutes = 0
        for item in item_list:
            if item.finish:
                diff = item.end_date - item.ini_date
                days, seconds = diff.days, diff.seconds
                hours += seconds // 3600
                minutes += (seconds % 3600) // 60
                #hours = days * 24 + seconds // 3600
                #seconds = seconds % 60
        if minutes > 59:
            hours += minutes // 60
            minutes = minutes % 60
        return hours, minutes
        #return "{}:{}".format(hours, minutes) 
        #return "{} horas y {}  minutos".format(hours, minutes) 

    class Meta:
        verbose_name = _('Empleado')
        verbose_name_plural = _('Empleados')

'''
    CLIENTS
'''
def upload_form_qr(instance, filename):
    ascii_filename = str(filename.encode('ascii', 'ignore'))
    instance.filename = ascii_filename
    folder = "clients/qr/%s" % (instance.id)
    return '/'.join(['%s' % (folder), datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ascii_filename])

class Client(models.Model):
    inactive = models.BooleanField(default=False, verbose_name=_('Desactivado'));
    code = models.CharField(max_length=200, verbose_name = _('Code'), default="")
    name = models.CharField(max_length=200, verbose_name = _('Razón Social'), default="")
    phone = models.CharField(max_length=12, verbose_name = _('Teléfono de contacto'), null=True, default='0000000000')
    email = models.EmailField(verbose_name = _('Email de contacto'), default="", null=True)
    address = models.TextField(verbose_name = _('Dirección'), null=True, default='')
    observations = models.TextField(verbose_name = _('Observaciones'), null=True, default='')
    qr = models.ImageField(upload_to=upload_form_qr, blank=True, verbose_name="QR", help_text="Select file to upload")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Empleado')
        verbose_name_plural = _('Empleados')

'''
    ASSISTANCE
'''
class Assistance(models.Model):
    finish = models.BooleanField(default=False, verbose_name=_('Terminada'));
    ini_date = models.DateTimeField(default=datetime.datetime.now(), null=True, verbose_name=_('Inicio'))
    end_date = models.DateTimeField(default=datetime.datetime.now(), null=True, verbose_name=_('Fin'))
    client = models.ForeignKey(Client, verbose_name=_('Client'), on_delete=models.SET_NULL, null=True, related_name="assistances")
    employee = models.ForeignKey(Employee,verbose_name=_('Empleado'),on_delete=models.SET_NULL,null=True,related_name="assistances")

    @property
    def duration(self):
        edate = self.end_date.replace(second=0, microsecond=0) 
        idate = self.ini_date.replace(second=0, microsecond=0)
        diff = edate - idate
        days, seconds = diff.days, diff.seconds
        return (seconds // 60)
        #hours += seconds // 3600
        #minutes += (seconds % 3600) // 60
        #if minutes > 59:
        #    hours += minutes // 60
        #    minutes = minutes % 60
        #return hours, minutes
 
    class Meta:
        verbose_name = _('Asistencia')
        verbose_name_plural = _('Asistencias')


