# Generated by Django 4.1.2 on 2023-11-03 19:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bill', '0014_bill_currentowner_bill_endorsed_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bill',
            name='file',
            field=models.TextField(blank=True, null=True),
        ),
    ]
