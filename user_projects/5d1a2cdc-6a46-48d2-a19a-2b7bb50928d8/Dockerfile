FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

COPY requirements.txt ./
RUN echo "Installing Python packages from requirements.txt..." &&     cat requirements.txt &&     pip install --no-cache-dir --verbose -r requirements.txt &&     echo "Python packages installed successfully" &&     pip list
COPY . .

EXPOSE 8000

ENV DJANGO_SETTINGS_MODULE=team_task_tracker.settings

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

