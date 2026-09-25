from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from apps.notifications.tasks import (
    is_upcoming_expiration,
    send_notification_email,
)


class BillExpiringRuleTests(SimpleTestCase):
    def test_upcoming_expiration_includes_next_seven_days_but_not_today(self):
        today = date(2026, 9, 25)
        self.assertFalse(is_upcoming_expiration(date(2026, 9, 25), today, 7))
        self.assertTrue(is_upcoming_expiration(date(2026, 9, 26), today, 7))
        self.assertTrue(is_upcoming_expiration(date(2026, 10, 2), today, 7))
        self.assertFalse(is_upcoming_expiration(date(2026, 10, 3), today, 7))


class NotificationEmailTaskTests(SimpleTestCase):
    @patch("apps.notifications.tasks.sendEmail")
    @patch("apps.notifications.tasks.NotificationRule.objects")
    @patch("apps.notifications.tasks.Notification.objects")
    def test_email_is_sent_only_when_rule_enables_it(self, notification_objects, rule_objects, send_email):
        notification = SimpleNamespace(
            id="notif-1",
            event_type="BILL_EXPIRING",
            title="Factura próxima a vencer",
            message="La factura FV-1 vence pronto.",
            entity_label="FV-1",
            recipient=SimpleNamespace(email="person@example.com"),
        )
        notification_objects.select_related.return_value.get.return_value = notification
        rule_objects.filter.return_value.only.return_value.first.return_value = SimpleNamespace(
            enabled=True,
            send_email=True,
        )
        send_email.return_value = 1

        result = send_notification_email("notif-1")

        self.assertTrue(result["sent"])
        send_email.assert_called_once()

    @patch("apps.notifications.tasks.sendEmail")
    @patch("apps.notifications.tasks.NotificationRule.objects")
    @patch("apps.notifications.tasks.Notification.objects")
    def test_email_is_not_sent_when_rule_disables_channel(self, notification_objects, rule_objects, send_email):
        notification_objects.select_related.return_value.get.return_value = SimpleNamespace(
            id="notif-2",
            event_type="BILL_EXPIRED",
            recipient=SimpleNamespace(email="person@example.com"),
        )
        rule_objects.filter.return_value.only.return_value.first.return_value = SimpleNamespace(
            enabled=True,
            send_email=False,
        )

        result = send_notification_email("notif-2")

        self.assertEqual(result, {"sent": False, "reason": "email_disabled"})
        send_email.assert_not_called()


class BillExpiringRealtimeTests(SimpleTestCase):
    @patch("apps.notifications.services.bill_expiration.NotificationService.create_notification")
    @patch("apps.notifications.services.bill_expiration.Notification.objects")
    @patch("apps.notifications.services.bill_expiration.NotificationRecipientService.recipients_for_event")
    def test_single_bill_processor_creates_notification_inside_window(
        self,
        recipients_for_event,
        notification_objects,
        create_notification,
    ):
        from apps.notifications.services.bill_expiration import process_expiring_bill

        recipient = SimpleNamespace(id="user-1")
        recipients = Mock()
        recipients.exists.return_value = True
        recipients.iterator.return_value = iter([recipient])
        recipients_for_event.return_value = recipients
        notification_objects.filter.return_value.exists.return_value = False

        bill = SimpleNamespace(
            id="bill-1",
            billId="FV-REALTIME-1",
            expirationDate="2026-09-26",
            endorsed=False,
            typeBill=SimpleNamespace(description="FV"),
            user_created_at=SimpleNamespace(id="creator-1"),
        )

        result = process_expiring_bill(
            bill,
            reference_date=date(2026, 9, 25),
        )

        self.assertEqual(result["notified"], 1)
        create_notification.assert_called_once()

    @patch("apps.notifications.services.bill_expiration.NotificationService.create_notification")
    @patch("apps.notifications.services.bill_expiration.Notification.objects")
    @patch("apps.notifications.services.bill_expiration.NotificationRecipientService.recipients_for_event")
    def test_single_bill_processor_is_idempotent_per_recipient(
        self,
        recipients_for_event,
        notification_objects,
        create_notification,
    ):
        from apps.notifications.services.bill_expiration import process_expiring_bill

        recipient = SimpleNamespace(id="user-1")
        recipients = Mock()
        recipients.exists.return_value = True
        recipients.iterator.return_value = iter([recipient])
        recipients_for_event.return_value = recipients
        notification_objects.filter.return_value.exists.return_value = True

        bill = SimpleNamespace(
            id="bill-1",
            billId="FV-REALTIME-1",
            expirationDate="2026-09-26",
            endorsed=False,
            typeBill=SimpleNamespace(description="FV"),
            user_created_at=SimpleNamespace(id="creator-1"),
        )

        result = process_expiring_bill(
            bill,
            reference_date=date(2026, 9, 25),
        )

        self.assertEqual(result["already_notified"], 1)
        create_notification.assert_not_called()
