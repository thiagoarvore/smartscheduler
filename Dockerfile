FROM python:3.13-alpine

WORKDIR /smartschedule

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY pyproject.toml poetry.lock* ./

RUN apk add --no-cache \
    curl \
    libffi \
    libpq \
    && apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    libffi-dev \
    postgresql-dev \
    && pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi \
    && apk del .build-deps

RUN mkdir -p /smartschedule/staticfiles /smartschedule/static /smartschedule/media

COPY . .

EXPOSE 8000