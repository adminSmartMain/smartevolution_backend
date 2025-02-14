# Generated by Django 4.1 on 2022-09-23 16:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('misc', '0006_add_type_operation'),
    ]

    operations = [
        migrations.CreateModel(
            name='Broker',
            fields=[
                ('id', models.CharField(editable=False, max_length=255, primary_key=True, serialize=False, unique=True)),
                ('state', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(default=None, null=True)),
                ('document_number', models.CharField(max_length=255, unique=True)),
                ('first_name', models.CharField(max_length=255)),
                ('last_name', models.CharField(max_length=255)),
                ('address', models.CharField(max_length=255)),
                ('email', models.CharField(max_length=255, unique=True)),
                ('phone_number', models.CharField(max_length=255, unique=True)),
                ('city', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='misc.city')),
                ('type_identity', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='misc.typeidentity')),
                ('user_created_at', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_created_at', to=settings.AUTH_USER_MODEL)),
                ('user_updated_at', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_updated_at', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'brokers',
                'verbose_name_plural': 'brokers',
                'db_table': 'brokers',
                'ordering': ['created_at'],
            },
        ),
    ]
