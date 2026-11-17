FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 10001 app
WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt gunicorn==27.0.1

COPY . .
RUN mkdir -p /app/data /app/media /app/staticfiles \
    && chown app:app /app /app/data /app/media /app/staticfiles

USER app
EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application"]