# Use official Python image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

WORKDIR /app/therapieland

RUN python manage.py collectstatic --noinput
RUN python manage.py migrate

CMD ["gunicorn", "therapieland.wsgi:application", "--bind", "0.0.0.0:8000"]