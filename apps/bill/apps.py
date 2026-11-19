import logging
import os

from django.apps import AppConfig


logger = logging.getLogger(__name__)


class BillsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.bill'

    def ready(self):
        # La carga estándar usa SMART_TOKEN. No registramos su valor, solo
        # hacemos visible una configuración incompleta desde el arranque.
        if not os.environ.get('SMART_TOKEN'):
            logger.error(
                'Billy configuration missing setting=SMART_TOKEN; '
                'Billy requests will be rejected locally'
            )
