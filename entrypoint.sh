#!/bin/sh
set -e

cd /app
mkdir -p /app/logs /run/dbus /tmp
chmod 1777 /tmp || true

# Chrome puede intentar hablar con D-Bus. Si no arranca, no detenemos Django.
if command -v dbus-daemon >/dev/null 2>&1; then
  dbus-daemon --system --fork 2>/dev/null || true
fi

cd /app/apps/base/scripts/pdf_parser
echo "Verificando generador PDF..."
node -e "const p=require('puppeteer'); console.log('Puppeteer:', require('./node_modules/puppeteer/package.json').version); console.log('Chrome:', p.executablePath())"
cd /app

python manage.py migrate
python manage.py crontab add

service cron start

echo "Crontabs configurados:"
crontab -l || echo "No hay crontab configurados"

echo "Starting Django server with Gunicorn..."
exec gunicorn -c gunicorn.conf.py core.wsgi:application
