# Generated by Django 4.1.2 on 2023-07-24 03:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0088_alter_financialcentral_rating'),
        ('operation', '0022_receipt_presentvalueinvestor'),
    ]

    operations = [
        migrations.AlterField(
            model_name='receipt',
            name='account',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='client.account'),
        ),
    ]
