# Generated by Django 4.1 on 2023-01-12 19:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('operation', '0012_alter_preoperation_datebill_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='receipt',
            name='futureValueRecalculation',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='receipt',
            name='tableRemaining',
            field=models.FloatField(default=0),
        ),
    ]
