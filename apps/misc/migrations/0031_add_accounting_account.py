# Generated by Django 4.1.7 on 2023-02-16 16:39

from django.db import migrations


class Migration(migrations.Migration):
    def load_initial_data(apps, schema_editor):
        model = apps.get_model('misc', 'AccountingAccount')
        model.objects.create(id='6e3b9251-33bc-460c-8c94-59c8eb473923',code="11050501",description='CAJA GENERAL',accountNumber="11050501")

    dependencies = [
        ('misc', '0030_add_new_receiptStatus'),
    ]

    operations = [
        migrations.RunPython(load_initial_data),
    ]
