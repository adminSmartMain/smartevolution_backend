# Generated by Django 4.1 on 2022-10-04 21:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('misc', '0014_add_accounting_accounts'),
        ('administration', '0004_emitterdeposit_beneficiary'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountingControl',
            fields=[
                ('id', models.CharField(editable=False, max_length=255, primary_key=True, serialize=False, unique=True)),
                ('state', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(default=None, null=True)),
                ('observations', models.TextField(blank=True, null=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='misc.accountingaccount')),
                ('type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='misc.typeexpenditure')),
                ('user_created_at', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_created_at', to=settings.AUTH_USER_MODEL)),
                ('user_updated_at', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_updated_at', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'accountingControl',
                'verbose_name_plural': 'accountingControls',
                'db_table': 'accountingControls',
                'ordering': ['created_at'],
            },
        ),
    ]
