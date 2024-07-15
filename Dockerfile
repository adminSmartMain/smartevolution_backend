FROM python:3.11-slim
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
    && apt-get clean
RUN which chromium || which chromium-browser
RUN curl -fsSL https://deb.nodesource.com/setup_14.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean
RUN node -v
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN cd apps/base/scripts/pdf_parser/ && npm install
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]