# Generated by Django 5.2 on 2025-05-07 10:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photos', '0002_imagerecord_delete_photo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='imagerecord',
            name='file_name',
            field=models.TextField(),
        ),
    ]
