# Generated by Django 4.1 on 2022-10-07 15:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0022_rename_cityclient_legalclientselfmanagement_citylc_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='legalclientselfmanagement',
            old_name='CityLC',
            new_name='cityLC',
        ),
        migrations.RenameField(
            model_name='legalclientselfmanagement',
            old_name='DepartmentLC',
            new_name='departmentLC',
        ),
        migrations.RenameField(
            model_name='legalclientselfmanagement',
            old_name='TypeCLient',
            new_name='typeCLient',
        ),
        migrations.RenameField(
            model_name='legalclientselfmanagement',
            old_name='TypeDocument',
            new_name='typeDocument',
        ),
        migrations.AddField(
            model_name='legalclientselfmanagement',
            name='status',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='naturalclientselfmanagement',
            name='status',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]
