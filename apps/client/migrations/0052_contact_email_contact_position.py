# Generated by Django 4.1 on 2022-12-21 15:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0051_client_birth_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='email',
            field=models.EmailField(default=None, max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='contact',
            name='position',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
