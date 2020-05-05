import os

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models


class FileType(models.Model):
    file_type = models.CharField(max_length=400, unique=True)
    file_type_human = models.CharField(max_length=400, unique=True)
    image_path = models.CharField(max_length=1000)


def file_directory_path(instance, filename):
    return os.path.join(f'file_type_{instance.file_type.file_type}', filename)


class File(models.Model):
    file = models.FileField(verbose_name='data_file', upload_to=file_directory_path, blank=False, null=False)
    filename = models.CharField(max_length=400, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='files')
    file_type = models.ForeignKey('FileType', on_delete=models.SET_NULL, null=True, related_name='files')

    def get_path(self):
        media_path = f'media/file_type_{self.file_type.file_type}/{self.filename}'
        return os.path.join(settings.BASE_DIR, media_path)
