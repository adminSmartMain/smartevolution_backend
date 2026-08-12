from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('bill', '0018_bill_idx_bill_emitter_id')]

    operations = [
        migrations.AddField(model_name='bill', name='billySyncStatus', field=models.CharField(default='synced', max_length=20)),
        migrations.AddField(model_name='bill', name='billyErrorCode', field=models.CharField(blank=True, max_length=20, null=True)),
        migrations.AddField(model_name='bill', name='billyErrorDetail', field=models.TextField(blank=True, null=True)),
        migrations.AddField(model_name='bill', name='billySyncAttempts', field=models.PositiveIntegerField(default=0)),
        migrations.AddField(model_name='bill', name='billyLastSyncAt', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='bill', name='billyTokenScope', field=models.CharField(default='smart', max_length=20)),
    ]
