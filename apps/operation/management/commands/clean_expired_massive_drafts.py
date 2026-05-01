from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.operation.api.models.index import MassiveOperationDraft


class Command(BaseCommand):
    help = "Elimina borradores masivos expirados"

    def handle(self, *args, **options):
        now = timezone.now()

        expired_drafts = MassiveOperationDraft.objects.filter(
            state=True,
            status=MassiveOperationDraft.STATUS_DRAFT,
            expiresAt__lt=now,
        )

        count = expired_drafts.count()

        expired_drafts.update(
            state=False,
            status=MassiveOperationDraft.STATUS_CANCELLED,
            updated_at=now,
        )

        self.stdout.write(
            self.style.SUCCESS(f"{count} borradores expirados fueron cancelados.")
        )