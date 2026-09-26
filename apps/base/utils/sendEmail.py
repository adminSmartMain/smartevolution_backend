from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def sendEmail(subject, message, email, html_message=None):
    """Send one email and return Django's delivery count (0 or 1)."""
    email_message = EmailMessage(
        subject=subject,
        body=html_message if html_message else message,
        from_email=settings.DEFAULT_FROM_EMAIL or None,
        to=[email],
    )
    if html_message:
        email_message.content_subtype = "html"
    return email_message.send(fail_silently=False)


def sendEmailWithTemplate(subject, template, context, email):
    htmlMessage = render_to_string(template, context)
    plainMessage = strip_tags(htmlMessage)
    return send_mail(
        subject,
        plainMessage,
        settings.DEFAULT_FROM_EMAIL or None,
        email,
        html_message=htmlMessage,
        fail_silently=False,
    )
