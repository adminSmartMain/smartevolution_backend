# Generated by Django 4.1 on 2022-10-19 18:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('operation', '0007_buyorder_idsignature'),
        ('administration', '0008_refund'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emitterdeposit',
            name='operation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='operation.preoperation'),
        ),
    ]
