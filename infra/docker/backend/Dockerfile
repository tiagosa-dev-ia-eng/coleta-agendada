# Backend Django + DRF (doc 03)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements*.txt ./
RUN pip install -r requirements-dev.txt

COPY backend/ ./

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
