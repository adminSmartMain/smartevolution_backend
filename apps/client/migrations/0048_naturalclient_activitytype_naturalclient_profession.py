# Generated by Django 4.1 on 2022-12-16 14:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0047_naturalclient'),
    ]

    operations = [
        migrations.AddField(
            model_name='naturalclient',
            name='activityType',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='naturalclient',
            name='profession',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
