#!/bin/sh

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
crontab -l

# Ejecutar el servidor Django
echo "Starting Django server..."
exec python manage.py runserver 0.0.0.0:8000
