# Generated by Django 4.1 on 2022-10-10 22:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0029_naturalclientselfmanagement_phonenumber'),
    ]

    operations = [
        migrations.AddField(
            model_name='naturalclientselfmanagement',
            name='email',
            field=models.EmailField(default=None, max_length=255),
            preserve_default=False,
        ),
    ]
