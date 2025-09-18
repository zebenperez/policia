from django.conf import settings
from django.contrib.auth.models import User, Group
from django.db import models
from django.utils.translation import gettext_lazy as _ 

import datetime


'''
    STATION
'''
class Station(models.Model):
    code = models.CharField(max_length=20, verbose_name = _('Codigo'), default="")
    name = models.CharField(max_length=200, verbose_name = _('Nombre'), default="")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Comisaría')
        verbose_name_plural = _('Comisarías')

'''
    EMPLOYEE
'''
class Employee(models.Model):
    pin = models.CharField(max_length=20, verbose_name = _('PIN'), default="")
    dni = models.CharField(max_length=20, verbose_name = _('DNI'), default="")
    name = models.CharField(max_length=200, verbose_name = _('Razón Social'), default="")
    phone = models.CharField(max_length=20, verbose_name = _('Teléfono de contacto'), null=True, default = '0000000000')
    email = models.EmailField(verbose_name = _('Email de contacto'), default="", null=True)
    station = models.ForeignKey(Station,verbose_name='Comisaría',on_delete=models.SET_NULL,null=True,blank=True,related_name='polices')
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

    class Meta:
        verbose_name = _('Empleado')
        verbose_name_plural = _('Empleados')

'''
    Report
'''
def upload_audio(instance, filename):
    ascii_filename = str(filename.encode('ascii', 'ignore'))
    instance.filename = ascii_filename
    folder = "audios"
    return '/'.join(['%s' % (folder), datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ascii_filename])

class Report(models.Model):
    date = models.DateTimeField(default=datetime.datetime.now(), null=True, verbose_name=_('Fecha'), blank=True)
    #text = models.TextField(verbose_name = _('Texto transcrito'), default="")
    #audio = models.FileField(upload_to=upload_audio, blank=True, verbose_name="Audio", help_text="Select file to upload")
    employee = models.ForeignKey(Employee,verbose_name=_('Empleado'),on_delete=models.SET_NULL,null=True,related_name="reports")

    #def __str__(self):
    #    return self.date

    @property
    def code(self):
        return "EXP-{}-{}".format(datetime.datetime.now().year, str(self.id).zfill(6))

    @property
    def text(self):
        text = ""
        for t in self.audios.all():
            text += f"{t.text}\r"
        return text 

    class Meta:
        verbose_name = _('Report')
        verbose_name_plural = _('Reports')
        ordering = ["-date"]

class ReportAudio(models.Model):
    text = models.TextField(verbose_name = _('Texto transcrito'), default="")
    audio = models.FileField(upload_to=upload_audio, blank=True, verbose_name="Audio", help_text="Select file to upload")
    report = models.ForeignKey(Report, verbose_name=_('Informe'), on_delete=models.SET_NULL, null=True, related_name="audios")

    class Meta:
        verbose_name = _('Report Audio')
        verbose_name_plural = _('Reports Audios')


