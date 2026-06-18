# Generated for controlled receipt void/adjust flow

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('operation', '0031_preoperation_idx_operation_emitter_created_and_more'),
        ('misc', '0035_typeevent_diandescription'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ReceiptImportSession',
            fields=[
                ('id', models.CharField(editable=False, max_length=255, primary_key=True, serialize=False, unique=True)),
                ('state', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(default=None, null=True)),
                ('source', models.CharField(choices=[('manual', 'Manual'), ('excel', 'Excel'), ('massive', 'Masivo')], default='excel', max_length=30)),
                ('fileName', models.CharField(blank=True, max_length=255, null=True)),
                ('applicationDate', models.DateField(blank=True, null=True)),
                ('totalRows', models.IntegerField(default=0)),
                ('processedRows', models.IntegerField(default=0)),
                ('createdCount', models.IntegerField(default=0)),
                ('errorCount', models.IntegerField(default=0)),
                ('notes', models.TextField(blank=True, null=True)),
                ('createdBy', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='receipt_import_sessions', to=settings.AUTH_USER_MODEL)),
                ('receiptStatus', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='misc.receiptstatus')),
                ('user_created_at', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_created_at', to=settings.AUTH_USER_MODEL)),
                ('user_updated_at', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_updated_at', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Receipt Import Session',
                'verbose_name_plural': 'Receipt Import Sessions',
                'db_table': 'receipt_import_sessions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='receipt',
            name='controlStatus',
            field=models.CharField(choices=[('ACTIVE', 'Activo'), ('VOIDED', 'Anulado'), ('ADJUSTED', 'Ajustado')], default='ACTIVE', max_length=30),
        ),
        migrations.AddField(
            model_name='receipt',
            name='voidReason',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='receipt',
            name='voidedAt',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='receipt',
            name='adjustmentReason',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='receipt',
            name='originalReceipt',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='corrections', to='operation.receipt'),
        ),
        migrations.AddField(
            model_name='receipt',
            name='replacedBy',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='replaces', to='operation.receipt'),
        ),
        migrations.AddField(
            model_name='receipt',
            name='voidedBy',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='voided_receipts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='receipt',
            name='importSession',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='receipts', to='operation.receiptimportsession'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='operation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receipts', to='operation.preoperation'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='account',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='receipts', to='client.account'),
        ),
        migrations.CreateModel(
            name='ReceiptSnapshot',
            fields=[
                ('id', models.CharField(editable=False, max_length=255, primary_key=True, serialize=False, unique=True)),
                ('state', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(default=None, null=True)),
                ('operationStatusBefore', models.IntegerField(blank=True, null=True)),
                ('operationPendingBefore', models.FloatField(blank=True, null=True)),
                ('operationAmountBefore', models.FloatField(blank=True, null=True)),
                ('operationPayedAmountBefore', models.FloatField(blank=True, null=True)),
                ('accountBalanceBefore', models.FloatField(blank=True, null=True)),
                ('billCurrentBalanceBefore', models.FloatField(blank=True, null=True)),
                ('billReBuyAvailableBefore', models.BooleanField(blank=True, null=True)),
                ('operationStatusAfter', models.IntegerField(blank=True, null=True)),
                ('operationPendingAfter', models.FloatField(blank=True, null=True)),
                ('operationAmountAfter', models.FloatField(blank=True, null=True)),
                ('operationPayedAmountAfter', models.FloatField(blank=True, null=True)),
                ('accountBalanceAfter', models.FloatField(blank=True, null=True)),
                ('billCurrentBalanceAfter', models.FloatField(blank=True, null=True)),
                ('billReBuyAvailableAfter', models.BooleanField(blank=True, null=True)),
                ('receipt', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='snapshot', to='operation.receipt')),
                ('user_created_at', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_created_at', to=settings.AUTH_USER_MODEL)),
                ('user_updated_at', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_updated_at', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Receipt Snapshot',
                'verbose_name_plural': 'Receipt Snapshots',
                'db_table': 'receipt_snapshots',
            },
        ),
        migrations.AddIndex(
            model_name='receipt',
            index=models.Index(fields=['operation', 'state'], name='idx_receipt_operation_state'),
        ),
        migrations.AddIndex(
            model_name='receipt',
            index=models.Index(fields=['operation', 'date', 'created_at'], name='idx_receipt_operation_order'),
        ),
        migrations.AddIndex(
            model_name='receipt',
            index=models.Index(fields=['controlStatus'], name='idx_receipt_control_status'),
        ),
        migrations.AddIndex(
            model_name='receipt',
            index=models.Index(fields=['date'], name='idx_receipt_date'),
        ),
        migrations.AddIndex(
            model_name='receiptsnapshot',
            index=models.Index(fields=['receipt'], name='idx_snapshot_receipt'),
        ),
    ]
