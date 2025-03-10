# Generated by Django 4.1.2 on 2023-06-21 15:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('misc', '0032_typeidentity_abbreviation'),
        ('client', '0085_alter_naturalclient_documentnumber'),
    ]

    operations = [
        migrations.AlterField(
            model_name='naturalclient',
            name='activityType',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='natural_client_activity_type', to='misc.ciiu'),
        ),
    ]
