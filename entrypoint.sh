#!/bin/sh

# Configurar crontab
python manage.py crontab add

# Iniciar cron
service cron start

# Verificar si los crontabs están configurados
echo "Crontabs configurados:"
crontab -l

# Iniciar servidor Django
exec "$@"
