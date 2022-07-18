from distutils.command.upload import upload
from django.db import models
from subprocess import call

class Upload(models.Model):
    upload_file = models.FileField()    
    upload_date = models.DateTimeField(auto_now_add =True)


