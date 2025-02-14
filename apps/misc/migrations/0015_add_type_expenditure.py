# Generated by Django 4.1 on 2022-10-04 22:13

from django.db import migrations


class Migration(migrations.Migration):
    def load_initial_data(apps, schema_editor):
        model = apps.get_model('misc', 'TypeExpenditure')
        model.objects.create(id='f6d29b11-ecfe-417e-887f-75ddc43b0017',description='transferencia')
        model.objects.create(id='0799fc62-fd65-4bef-af56-6747fbcadac4',description='compensación')
        model.objects.create(id='5d6524f0-521b-43b2-bf85-ea4c02e2a901',description='recompra')
        model.objects.create(id='39e0b709-cff5-42e2-b729-6a1e0a09ae07',description='otro')
    dependencies = [
        ('misc', '0014_add_accounting_accounts'),
    ]

    operations = [
        migrations.RunPython(load_initial_data),
    ]
