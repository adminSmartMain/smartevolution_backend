# Generated by Django 4.1.7 on 2023-02-16 19:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('report', '0015_sellorder_client'),
    ]

    operations = [
        migrations.AddField(
            model_name='sellorderoperation',
            name='status',
            field=models.IntegerField(default=0),
        ),
    ]
