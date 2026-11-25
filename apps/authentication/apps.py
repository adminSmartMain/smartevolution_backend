from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.authentication'

    def ready(self):
        from apps.authentication.services.login_security import report_captcha_configuration
        report_captcha_configuration()
