# Generated by Django 4.1 on 2023-01-04 21:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('report', '0009_alter_negotiationsummary_observations'),
    ]

    operations = [
        migrations.AddField(
            model_name='negotiationsummary',
            name='totalDeposits',
            field=models.FloatField(default=0),
        ),
    ]
