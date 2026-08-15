from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[('authentication','0008_full_platform_permissions')]
    operations=[
      migrations.CreateModel(name='AccessAudit',fields=[('id',models.CharField(editable=False,max_length=255,primary_key=True,serialize=False)),('action',models.CharField(max_length=80)),('target_type',models.CharField(max_length=80)),('target_id',models.CharField(blank=True,max_length=255,null=True)),('details',models.JSONField(blank=True,default=dict)),('ip_address',models.GenericIPAddressField(blank=True,null=True)),('created_at',models.DateTimeField(auto_now_add=True)),('actor',models.ForeignKey(null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='access_audits',to=settings.AUTH_USER_MODEL))],options={'db_table':'access_audit','ordering':['-created_at']}),
      migrations.AddIndex(model_name='accessaudit',index=models.Index(fields=['target_type','target_id'],name='idx_audit_target')),
      migrations.AddIndex(model_name='accessaudit',index=models.Index(fields=['created_at'],name='idx_audit_created')),
    ]
