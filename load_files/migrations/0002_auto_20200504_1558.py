# Generated by Django 2.2.12 on 2020-05-04 12:58

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('load_files', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='filetype',
            name='file_type_human',
            field=models.CharField(default=None, max_length=400, unique=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='filetype',
            name='image_path',
            field=models.CharField(default=datetime.datetime(2020, 5, 4, 12, 58, 6, 752373, tzinfo=utc), max_length=1000, unique=True),
            preserve_default=False,
        ),
    ]