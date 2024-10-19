FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    ca-certificates \
    chromium \
    cron \
    curl \
    default-libmysqlclient-dev \
    default-mysql-client \
    fonts-liberation \
    gcc \
    gnupg \
    libcups2 \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxss1 \
    lsb-release \
    wget \
    xdg-utils \
    && apt-get clean

# Descarga y configuración de Node.js
ADD https://raw.githubusercontent.com/tj/n/master/bin/n /n
RUN bash n lts \
    && ln -sf /usr/local/n/versions/node/$(n --latest)/bin/node /usr/bin/node \
    && ln -sf /usr/local/n/versions/node/$(n --latest)/bin/npm /usr/bin/npm \
    && ln -sf /usr/local/n/versions/node/$(n --latest)/bin/npx /usr/bin/npx
RUN node -v
RUN npm -v

WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pymysql

# Copiar el código de la aplicación
COPY . .

# Copiar el script de entrada y hacerlo ejecutable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]