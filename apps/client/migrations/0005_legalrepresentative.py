# Generated by Django 4.1 on 2022-09-23 20:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('misc', '0006_add_type_operation'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('client', '0004_contact'),
    ]

    operations = [
        migrations.CreateModel(
            name='LegalRepresentative',
            fields=[
                ('id', models.CharField(editable=False, max_length=255, primary_key=True, serialize=False, unique=True)),
                ('state', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(default=None, null=True)),
                ('document_number', models.CharField(max_length=255)),
                ('first_name', models.CharField(max_length=255, null=True)),
                ('last_name', models.CharField(max_length=255, null=True)),
                ('social_reason', models.CharField(max_length=255, null=True)),
                ('birth_date', models.DateField()),
                ('address', models.CharField(max_length=255)),
                ('phone_number', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=255)),
                ('position', models.CharField(max_length=255)),
                ('citizenship', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='misc.country')),
                ('city', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='misc.city')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client.client')),
                ('type_identity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='misc.typeidentity')),
                ('user_created_at', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_created_at', to=settings.AUTH_USER_MODEL)),
                ('user_updated_at', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_updated_at', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'legalRepresentatives',
                'verbose_name_plural': 'legalRepresentatives',
                'db_table': 'legalRepresentatives',
                'ordering': ['created_at'],
            },
        ),
    ]
