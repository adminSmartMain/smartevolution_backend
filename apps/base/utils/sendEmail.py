from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def sendEmail(subject, message, email):
    email = EmailMessage(subject, message, to=[email])
    email.send()
    return email

def sendEmailWithTemplate(subject, template, context, email):
    htmlMessage = render_to_string(template, context)
    
    plainMessage = strip_tags(htmlMessage)
    
    email = send_mail(subject, plainMessage, None, email, html_message=htmlMessage)

    return email