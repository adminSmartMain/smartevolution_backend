# Generated by Django 4.1 on 2022-09-23 15:45

from django.db import migrations


class Migration(migrations.Migration):
    def load_initial_data(apps, schema_editor):
        modelRole = apps.get_model('authentication', 'role')
        modelRole.objects.create(id='5da6b88d-c248-4840-815a-bed2dce6af50', description='admin')
        modelRole.objects.create(id='7c668ceb-665e-42f0-b67a-f3c5781abd0f', description='client')
        modelRole.objects.create(id='2f4aadaa-df75-408b-9d07-111c7ab4a042', description='third')


    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_initial_data)
    ]
