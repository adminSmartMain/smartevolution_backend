FROM python:3.11-slim
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    gcc \
    curl \
    && apt-get clean

RUN curl -fsSL https://deb.nodesource.com/setup_14.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]