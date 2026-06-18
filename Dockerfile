FROM python:3.13-alpine

WORKDIR /smartscheduler

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=2.4.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Runtime deps
RUN apk add --no-cache \
        curl \
        libffi \
        libpq \
        cairo \
        pango \
        gdk-pixbuf \
        jpeg \
        zlib

# Build deps (removidas após instalar pacotes Python)
RUN apk add --no-cache --virtual .build-deps \
        gcc \
        musl-dev \
        libffi-dev \
        postgresql-dev \
        cairo-dev \
        pango-dev \
        gdk-pixbuf-dev \
        jpeg-dev \
        zlib-dev \
        build-base

# Poetry
RUN pip install --no-cache-dir poetry==${POETRY_VERSION}

# Deps — instaladas em camadas pra cache
COPY pyproject.toml poetry.lock* ./
RUN poetry install --only=main --no-root && apk del .build-deps

# Código
RUN mkdir -p /smartscheduler/staticfiles /smartscheduler/static /smartscheduler/media
COPY . .

EXPOSE 8000
