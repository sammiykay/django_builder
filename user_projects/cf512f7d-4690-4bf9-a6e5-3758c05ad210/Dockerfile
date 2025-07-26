    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip wheel setuptools && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# Final stage
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=social_pulse_dashboard.settings

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    nginx \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -s /bin/bash app_user \
    && chown -R app_user:app_user /app

COPY --from=builder /build/wheels /wheels
COPY --chown=app_user:app_user . .

RUN pip install --upgrade pip && \
    (pip install --retries 5 --timeout 300 /wheels/* || \
    pip install --retries 10 --timeout 600 --resume-retries /wheels/* || \
    pip install --no-cache-dir --retries 5 --timeout 300 /wheels/* || \
    (cd /wheels && ls *.whl | xargs -n 1 pip install --retries 3 --timeout 120)) && \
    rm -rf /wheels

RUN mkdir -p /app/media /app/static /app/logs && \
    chown -R app_user:app_user /app/media /app/static /app/logs && \
    chmod -R 755 /app/media /app/static /app/logs

USER app_user

RUN python manage.py collectstatic --noinput

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "4", \
     "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", \
     "--worker-class", "uvicorn.workers.UvicornWorker", "social_pulse_dashboard.asgi:application"]