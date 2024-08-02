FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    gcc \
    curl \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libcups2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxss1 \
    lsb-release \
    xdg-utils \
    chromium \
    cron \
    && apt-get clean

RUN which chromium || which chromium-browser
RUN curl -L https://raw.githubusercontent.com/tj/n/master/bin/n -o n \
    && bash n lts \
    && ln -sf /usr/local/n/versions/node/$(n --latest)/bin/node /usr/bin/node \
    && ln -sf /usr/local/n/versions/node/$(n --latest)/bin/npm /usr/bin/npm \
    && ln -sf /usr/local/n/versions/node/$(n --latest)/bin/npx /usr/bin/npx
RUN node -v
RUN npm -v

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

RUN mkdir -p /app/logs
#RUN cd apps/base/scripts/pdf_parser/ && npm install puppeteer --save

# Copiar el script de entrada y hacerlo ejecutable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
