# Use official Python image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create a volume mount point for SQLite DB file
VOLUME ["/therapieland/db.sqlite3"]

# Collect static files (if any)
RUN python manage.py collectstatic --noinput

# Run database migrations
RUN python manage.py migrate

# Run Django app with gunicorn
CMD ["gunicorn", "therapieland.wsgi:application", "--bind", "0.0.0.0:8000"]