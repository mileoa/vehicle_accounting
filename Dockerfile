# pull official base image
FROM python:3.11

# Установка зависимостей для GeoDjango
RUN apt-get update && apt-get install -y \
    binutils \
    libproj-dev \
    gdal-bin \
    libgdal-dev \
    postgis \
    postgresql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка зависимостей проекта
RUN pip install --no-cache-dir -r requirements.txt

# Копирование проекта в рабочую директорию
COPY . .
COPY .env.docker .env

# Установка переменных окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
