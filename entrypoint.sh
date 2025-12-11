#!/bin/sh
set -e
cd apps/base/scripts/pdf_parser/
rm -rf node_modules
npm install puppeteer --save
cd && cd /app
mkdir -p /app/logs
# Configurar crontab
python manage.py migrate
python manage.py crontab add
# Iniciar cron
service cron start
# Verificar si los crontabs están configurados
echo "Crontabs configurados:"
crontab -l || echo "No hay crontab configurados"
# Ejecutar el servidor Django
echo "Starting Django server with Gunicorn..."
exec gunicorn -c gunicorn.conf.py core.wsgi:application