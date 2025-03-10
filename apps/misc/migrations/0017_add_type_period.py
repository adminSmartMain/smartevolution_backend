# Generated by Django 4.1 on 2022-10-05 21:23

from django.db import migrations


class Migration(migrations.Migration):
    def load_initial_data(apps, schema_editor):
        model = apps.get_model('misc', 'TypePeriod')
        model.objects.create(id='e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd',description='trimestral')
        model.objects.create(id='e635f0f1-b29c-45e5-b351-04725a489be3',description='semestral')
        model.objects.create(id='0835dcb5-d6f2-43d7-b7ca-8864119ea05f',description='anual')

    dependencies = [
        ('misc', '0016_typeperiod'),
    ]

    operations = [
        migrations.RunPython(load_initial_data),
    ]
