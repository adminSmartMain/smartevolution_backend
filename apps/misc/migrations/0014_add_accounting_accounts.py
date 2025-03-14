# Generated by Django 4.1 on 2022-10-04 21:49

from django.db import migrations


class Migration(migrations.Migration):
    def load_initial_data(apps, schema_editor):
        model = apps.get_model('misc', 'AccountingAccount')
        model.objects.create(id='b319487a-cbf8-440a-a7ed-ab0f83c174be',code="11100501",description='Bancolombia Cta Cte',accountNumber="37202503274")
        model.objects.create(id='c8ed80c0-d761-4010-954c-baf38bf02337',code="11100502",description='BBVA Cta Cte', accountNumber="0382016368")
        model.objects.create(id='e12e227a-aa84-405b-be7f-60060e90bf52',code="131020",description='Particulares', accountNumber="131020")
        model.objects.create(id='3cfdc215-060d-468e-9b6f-ac16d4086584',code="280505",description='De clientes', accountNumber="280505")
    dependencies = [
        ('misc', '0013_rename_number_accountingaccount_accountnumber_and_more'),
    ]

    operations = [
        migrations.RunPython(load_initial_data),
    ]
