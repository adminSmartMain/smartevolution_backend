from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('authentication', '0014_user_administration_profile')]

    operations = [
        migrations.CreateModel(
            name='AuthenticationSecurityAudit',
            fields=[
                ('id', models.CharField(editable=False, max_length=255, primary_key=True, serialize=False)),
                ('event', models.CharField(max_length=80)),
                ('email_attempted', models.CharField(blank=True, default='', max_length=254)),
                ('identifier_hash', models.CharField(db_index=True, max_length=64)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.CharField(blank=True, default='', max_length=512)),
                ('reason', models.CharField(max_length=120)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='security_audits', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'authentication_security_audit', 'ordering': ['-created_at']},
        ),
        migrations.AddIndex(
            model_name='authenticationsecurityaudit',
            index=models.Index(fields=['event', 'created_at'], name='idx_security_event_at'),
        ),
        migrations.AddIndex(
            model_name='authenticationsecurityaudit',
            index=models.Index(fields=['ip_address', 'created_at'], name='idx_security_ip_at'),
        ),
    ]
