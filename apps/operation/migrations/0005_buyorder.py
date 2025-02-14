# Generated by Django 4.1 on 2022-10-11 15:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('operation', '0004_preoperation_additionalinterests_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='BuyOrder',
            fields=[
                ('id', models.CharField(editable=False, max_length=255, primary_key=True, serialize=False, unique=True)),
                ('state', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(default=None, null=True)),
                ('url', models.CharField(max_length=255)),
                ('date', models.DateField()),
                ('idRequest', models.CharField(max_length=255)),
                ('status', models.IntegerField(default=0)),
                ('signStatus', models.IntegerField(default=0)),
                ('operation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='operation.preoperation')),
                ('user_created_at', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_created_at', to=settings.AUTH_USER_MODEL)),
                ('user_updated_at', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_updated_at', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'BuyOrder',
                'verbose_name_plural': 'BuyOrders',
                'db_table': 'buyOrder',
            },
        ),
    ]
