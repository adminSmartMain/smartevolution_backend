# Generated by Django 4.1 on 2022-12-27 21:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('misc', '0023_alter_accountingaccount_options_and_more'),
        ('client', '0055_alter_client_citizenship'),
    ]

    operations = [
        migrations.AlterField(
            model_name='legalrepresentative',
            name='citizenship',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='misc.country'),
        ),
    ]
