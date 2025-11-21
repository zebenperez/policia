from django.db import models
from django.utils.translation import gettext_lazy as _ 
from django.utils import timezone


class Training(models.Model):
    date = models.DateTimeField(default=timezone.now(), null=True, verbose_name=_('Fecha'), blank=True)

    def __str__(self):
        return self.date.strftime("%d-%m-%Y")

class TrainingPrompt(models.Model):
    date = models.DateTimeField(default=timezone.now(), null=True, verbose_name=_('Fecha'), blank=True)
    text = models.TextField(default="", null=True, verbose_name=_('Texto'), blank=True)
    response = models.TextField(default="", null=True, verbose_name=_('Response'), blank=True)
    training = models.ForeignKey(Training, verbose_name='Entrenamiento', on_delete=models.CASCADE, null=True, blank=True, related_name='prompts')

    def __str__(self):
        return self.date.strftime("%d-%m-%Y")

def upload_doc(instance, filename):
    ascii_filename = str(filename.encode('ascii', 'ignore'))
    instance.filename = ascii_filename
    folder = "training"
    return '/'.join(['%s' % (folder), timezone.now().strftime("%Y%m%d%H%M%S") + "__" + ascii_filename])

class TrainingDoc(models.Model):
    doc = models.FileField(upload_to=upload_doc, blank=True, verbose_name="Document", help_text="Select file to upload")
    training = models.ForeignKey(Training, verbose_name='Entrenamiento', on_delete=models.CASCADE, null=True, blank=True, related_name='docs')

    class Meta:
        verbose_name = _('Documento')
        verbose_name_plural = _('Documentos')
        ordering = ["-id"]



