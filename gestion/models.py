from django.conf import settings
from django.contrib.auth.models import User, Group
from django.db import models
from django.utils.translation import gettext_lazy as _ 
from django.utils import timezone

import uuid
import datetime


class Config(models.Model):
    key = models.CharField(max_length=20, verbose_name = _('Key'), default="")
    value = models.CharField(max_length=255, verbose_name = _('Value'), default="")

    def __str__(self):
        return self.key

    class Meta:
        verbose_name = _('Config')
        verbose_name_plural = _('Config')

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
    close = models.BooleanField(verbose_name = _('Cerrado'), default=False)
    uuid = models.CharField(max_length=100, verbose_name = _('UUID'), default="")
    date = models.DateTimeField(default=datetime.datetime.now(), null=True, verbose_name=_('Fecha'), blank=True)
    last_interaction = models.DateTimeField(default=timezone.now(),null=True,verbose_name=_('Última interacción'),blank=True)
    #text = models.TextField(verbose_name = _('Texto transcrito'), default="")
    #audio = models.FileField(upload_to=upload_audio, blank=True, verbose_name="Audio", help_text="Select file to upload")
    employee = models.ForeignKey(Employee,verbose_name=_('Empleado'),on_delete=models.SET_NULL,null=True,related_name="reports")
    vector_id = models.CharField(max_length=200, verbose_name = _('Vector ID'), default="", blank=True)
    conversation_id = models.CharField(max_length=200, verbose_name = _('Conversation ID'), default="", blank=True)

    def __str__(self):
        return self.code

    @property
    def code(self):
        return "EXP-{}-{}".format(datetime.datetime.now().year, str(self.id).zfill(6))

    @property
    def text(self):
        text = ""
        for t in self.audios.all():
            text += f"{t.text}\r"
        return text 
    
    def save(self, *args, **kwargs):
        # Check if it is new item
        if self.uuid == None or self.uuid == "" or len(self.uuid) < 5:
            self.uuid = Report.new_uuid()
        super().save(*args, **kwargs)
    
    @staticmethod
    def new_uuid():
        current = str(uuid.uuid4())
        while Report.objects.filter(uuid=current).exists():
            current = str(uuid.uuid4())
        return current

    @staticmethod
    def get_today_by_emp(emp):
        today = timezone.localdate()
        return Report.objects.filter(last_interaction__date=today, close=False).first()

    class Meta:
        verbose_name = _('Report')
        verbose_name_plural = _('Reports')
        ordering = ["-date"]

class ReportAudio(models.Model):
    text = models.TextField(verbose_name = _('Texto transcrito'), default="")
    text2 = models.TextField(verbose_name = _('Texto tratado'), default="")
    audio = models.FileField(upload_to=upload_audio, blank=True, verbose_name="Audio", help_text="Select file to upload")
    report = models.ForeignKey(Report, verbose_name=_('Informe'), on_delete=models.SET_NULL, null=True, related_name="audios")
    processed = models.BooleanField(verbose_name = _('Procesado'), default=False)
    upload_id = models.CharField(max_length=200, verbose_name = _('Upload ID'), default="", blank=True)

    class Meta:
        verbose_name = _('Report Audio')
        verbose_name_plural = _('Reports Audios')
        ordering = ["-id"]

class ReportMsg(models.Model):
    #ia = models.BooleanField(verbose_name = _('Recibido por IA'), default=False)
    date = models.DateTimeField(default=datetime.datetime.now(), null=True, verbose_name=_('Fecha'), blank=True)
    text = models.TextField(verbose_name = _('Texto'), default="")
    report = models.ForeignKey(Report, verbose_name=_('Informe'), on_delete=models.CASCADE, null=True, related_name="messages")

    class Meta:
        verbose_name = _('Report Message')
        verbose_name_plural = _('Reports Messages')
        ordering = ["id"]


'''
    Knowledge Docs
'''
def upload_doc(instance, filename):
    ascii_filename = str(filename.encode('ascii', 'ignore'))
    instance.filename = ascii_filename
    folder = "training"
    return '/'.join(['%s' % (folder), timezone.now().strftime("%Y%m%d%H%M%S") + "__" + ascii_filename])

class BaseDoc(models.Model):
    uuid = models.CharField(max_length=100, verbose_name = _('UUID'), default="")
    vuuid = models.CharField(max_length=100, verbose_name = _('Vector UUID'), default="")
    doc = models.FileField(upload_to=upload_doc, blank=True, verbose_name="Document", help_text="Select file to upload")

    class Meta:
        verbose_name = _('Documento')
        verbose_name_plural = _('Documentos')
        ordering = ["-id"]


