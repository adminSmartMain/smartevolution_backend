from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("client", "0095_account_idx_account_client_created_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="ClientAccess",
                    fields=[
                        ("id", models.CharField(editable=False, max_length=255, primary_key=True, serialize=False, unique=True)),
                        ("state", models.BooleanField(default=True)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(default=None, null=True)),
                        ("status", models.CharField(choices=[("PENDING", "Pending"), ("ACTIVE", "Active"), ("BLOCKED", "Blocked"), ("DISABLED", "Disabled")], default="PENDING", max_length=20)),
                        ("activated_at", models.DateTimeField(blank=True, null=True)),
                        ("blocked_at", models.DateTimeField(blank=True, null=True)),
                        ("blocked_reason", models.TextField(blank=True, null=True)),
                        ("client", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="access_account", to="client.client")),
                        ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="client_access", to=settings.AUTH_USER_MODEL)),
                        ("user_created_at", models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="clientaccess_created_at", to=settings.AUTH_USER_MODEL)),
                        ("user_updated_at", models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="clientaccess_updated_at", to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        "verbose_name": "client_access",
                        "verbose_name_plural": "client_access",
                        "db_table": "client_access",
                        "ordering": ["-created_at"],
                        "indexes": [
                            models.Index(fields=["status", "state"], name="idx_client_access_status"),
                            models.Index(fields=["created_at"], name="idx_client_access_created"),
                        ],
                    },
                ),
            ],
        ),
    ]
