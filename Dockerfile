FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    XDG_RUNTIME_DIR=/tmp \
    PUPPETEER_CACHE_DIR=/root/.cache/puppeteer

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    dbus \
    default-libmysqlclient-dev \
    default-mysql-client \
    fonts-liberation \
    gcc \
    g++ \
    make \
    pkg-config \
    python3-dev \
    gnupg \
    libcups2 \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcairo2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libvulkan1 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxkbcommon0 \
    libxrandr2 \
    libxrender1 \
    libxshmfence1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    wget \
    xdg-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ADD https://raw.githubusercontent.com/tj/n/master/bin/n /n
RUN bash /n 20.20.2 \
    && ln -sf /usr/local/bin/node /usr/bin/node \
    && ln -sf /usr/local/bin/npm /usr/bin/npm \
    && ln -sf /usr/local/bin/npx /usr/bin/npx

RUN node -v
RUN npm -v

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir pymysql

COPY . .

# IMPORTANTE:
# No usamos /usr/bin/chromium porque fue el binario que hizo core dump.
# Instalamos y usamos el Chrome administrado por Puppeteer.
RUN cd /app/apps/base/scripts/pdf_parser \
    && rm -rf node_modules package-lock.json \
    && npm install --omit=dev --no-audit --no-fund \
    && npx puppeteer browsers install chrome \
    && node -e "const p=require('puppeteer'); console.log('Puppeteer:', require('./node_modules/puppeteer/package.json').version); console.log('Chrome:', p.executablePath())"

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
