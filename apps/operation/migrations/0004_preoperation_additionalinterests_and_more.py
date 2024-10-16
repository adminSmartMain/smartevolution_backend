# Generated by Django 4.1 on 2022-10-04 13:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('misc', '0010_add_type_receipt'),
        ('operation', '0003_receipt'),
    ]

    operations = [
        migrations.AddField(
            model_name='preoperation',
            name='additionalInterests',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='preoperation',
            name='investorInterests',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='preoperation',
            name='tableInterests',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='receipt',
            name='additionalInterests',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='receipt',
            name='gmvValue',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='typeReceipt',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='misc.typereceipt'),
        ),
    ]
