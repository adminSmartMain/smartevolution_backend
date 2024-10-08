# Generated by Django 4.1 on 2022-10-04 19:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('misc', '0010_add_type_receipt'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('client', '0018_rename_emitter_balance_account_balance_and_more'),
        ('operation', '0004_preoperation_additionalinterests_and_more'),
        ('administration', '0002_alter_deposit_amount'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmitterDeposit',
            fields=[
                ('id', models.CharField(editable=False, max_length=255, primary_key=True, serialize=False, unique=True)),
                ('state', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(default=None, null=True)),
                ('date', models.DateField()),
                ('amount', models.FloatField()),
                ('accountNumber', models.CharField(max_length=20)),
                ('accountType', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='misc.accounttype')),
                ('bank', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='misc.bank')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client.client')),
                ('operation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='operation.preoperation')),
                ('user_created_at', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_created_at', to=settings.AUTH_USER_MODEL)),
                ('user_updated_at', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_updated_at', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
