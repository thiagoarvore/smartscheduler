# Sprint 01 — Base Inicial: Django + Docker + Poetry

> **Branch**: `sprint-01/base-inicial`  
> **Objetivo**: ter o projeto Django rodando com PostgreSQL e Redis, containerizado, gerenciado por Poetry.

## 1. Stack

| Componente | Versão / Fonte | Justificativa |
|---|---|---|
| Python | 3.13 (alpine) | Mesma do Thinkflow, alinhado com o Django 6.0 |
| Django | 6.0+ | Framework web |
| PostgreSQL | 18.1-trixie | Banco principal (mesmo do Thinkflow) |
| Redis | 7-alpine | Broker Celery + cache |
| Poetry | latest | Substitui `requirements.txt` do Thinkflow |
| django-base-kit | 0.1.4+ | Base reusável (auth, layout, forms) |
| django-htmx | latest | HTMX como dependência Django (sem CDN manual) |
| django-auditlog | 3.4+ | Trilha de auditoria |
| python-decouple | 3.8+ | Leitura de `.env` (mesmo padrão Thinkflow) |

> **Decisão**: Poetry em vez de `requirements.txt` do Thinkflow. Resto segue o mais próximo possível do padrão Thinkflow (mesma imagem Python, mesmo Postgres, mesmo Redis, mesma estrutura de compose, mesmos healthchecks).

## 2. Estrutura de diretórios

```
smartscheduler/
├─ .dockerignore
├─ .env                  # NÃO commitado
├─ .env.example          # commitado
├─ .gitignore
├─ .ruff_cache/          # ignorado
├─ docker-compose.yml
├─ Dockerfile
├─ manage.py
├─ poetry.lock           # gerado pelo Poetry
├─ pyproject.toml        # deps + config Poetry
├─ config/               # Django settings (era "app" no Thinkflow, mas aqui será "config")
│  ├─ __init__.py
│  ├─ asgi.py
│  ├─ settings.py
│  ├─ urls.py
│  └─ wsgi.py
├─ apps/                 # apps de domínio (accounts, schools, etc)
│  └─ __init__.py
├─ static/
├─ templates/
├─ staticfiles/          # coletado pelo collectstatic
└─ media/                # uploads
```

> **Mudança em relação ao Thinkflow**: o projeto Django do Thinkflow chama o app raiz de `app/` (celery e settings vivem lá). Vamos usar `config/` (padrão Django moderno, mais explícito) e separar `apps/` pros apps de domínio.

## 3. Arquivos

### 3.1 `pyproject.toml`

```toml
[project]
name = "smartscheduler"
version = "0.1.0"
description = "Grade Certa — sistema de grade horária escolar"
requires-python = ">=3.13"
dependencies = [
    "Django>=6.0,<7.0",
    "psycopg[binary]>=3.2",
    "celery[redis]>=5.5",
    "redis>=5.0",
    "django-base-kit>=0.1.4",
    "django-htmx>=1.23",
    "django-auditlog>=3.4",
    "python-decouple>=3.8",
    "whitenoise>=6.12",
    "gunicorn>=23.0",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.8",
    "pytest>=8.0",
    "pytest-django>=4.8",
    "ipython>=8.0",
]

[tool.poetry.group.dev.dependencies]
ruff = "^0.8"
pytest = "^8.0"
pytest-django = "^4.8"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "W", "UP", "B", "DJ"]

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
python_files = ["test_*.py", "*_test.py"]
```

### 3.2 `Dockerfile`

Idêntico ao Thinkflow, exceto a instalação via Poetry:

```dockerfile
FROM python:3.13-alpine

WORKDIR /smartscheduler

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.8.4 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# System deps (iguais ao Thinkflow + curl pro healthcheck)
RUN apk add --no-cache \
        curl \
        libffi \
        libpq \
        cairo \
        pango \
        gdk-pixbuf \
        jpeg \
        zlib \
        build-base

# Poetry
RUN pip install --no-cache-dir poetry==${POETRY_VERSION}

# Deps — instaladas em camadas pra cache
COPY pyproject.toml poetry.lock* ./
RUN poetry install --only=main --no-root

# Código
RUN mkdir -p /smartscheduler/staticfiles /smartscheduler/static /smartscheduler/media
COPY . .

EXPOSE 8000
```

> **Nota**: copiamos `poetry.lock*` (com `*`) pra permitir primeira build sem lock. Após `poetry lock`, rebuild usa lock travado.

### 3.3 `docker-compose.yml`

Baseado no Thinkflow, com `app` renomeado pra `web` (mais semântico) e sem Celery/Beat ainda (entram em sprint futura):

```yaml
services:
  web:
    image: smartscheduler_web:local
    build: .
    restart: always
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             python manage.py runserver 0.0.0.0:8000"
    env_file:
      - .env
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    volumes:
      - .:/smartscheduler
      - static_volume:/smartscheduler/staticfiles
      - media_data:/smartscheduler/media

  db:
    image: postgres:18.1-trixie
    ports:
      - "5433:5432"
    volumes:
      - postgres_data_smartscheduler:/var/lib/postgresql
    environment:
      - POSTGRES_USER=${DB_USER:-postgres}
      - POSTGRES_PASSWORD=${DB_PASSWORD:-postgres}
      - POSTGRES_DB=${DB_NAME:-smartscheduler}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: redis_smartscheduler
    command: redis-server --port 6379 --appendonly yes
    volumes:
      - redis:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 10

volumes:
  postgres_data_smartscheduler:
    name: postgres_data_smartscheduler
  static_volume:
  redis:
  media_data:
```

### 3.4 `.env.example`

```ini
# Django
SECRET_KEY=change-me-in-prod-please-do-not-use-this-default
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=smartscheduler
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Celery (placeholder, sprint futura)
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### 3.5 `config/settings.py` (esqueleto mínimo)

```python
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost", cast=Csv())

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "auditlog",
    "django_htmx",
    "base_kit",  # django-base-kit

    # Local
    # "apps.accounts",
    # "apps.schools",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST", default="db"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://redis:6379/0"),
    }
}

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
```

### 3.6 `.dockerignore`

```
.venv
__pycache__
**/__pycache__
*.pyc
.pytest_cache
.ruff_cache
.git
.gitignore
.env
.env.*
!.env.example
*.sqlite3
media
staticfiles
.idea
.vscode
*.log
.coverage
htmlcov
.codex
```

### 3.7 `.gitignore`

Adicionar à base já commitada:

```
poetry.lock

# Django
db.sqlite3
*.sqlite3-journal
media/
staticfiles/

# IDE
.idea/
.vscode/
*.swp
*.swo
*~
```

## 4. Comandos de execução

```bash
# 1. Instalar Poetry localmente (caso não tenha)
curl -sSL https://install.python-poetry.org | python3 -

# 2. Gerar lockfile
poetry lock

# 3. Subir containers
cp .env.example .env
docker compose up --build

# 4. Verificar
docker compose ps
curl http://localhost:8000/health/

# 5. Criar superuser
docker compose exec web python manage.py createsuperuser
```

## 5. Endpoint de healthcheck

Adicionar em `config/urls.py`:

```python
from django.http import JsonResponse
from django.urls import path

def health(_request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path("health/", health, name="health"),
    path("admin/", admin.site.urls),
]
```

## 6. Critérios de aceite

- [ ] `docker compose up --build` sobe sem erros
- [ ] `curl http://localhost:8000/health/` retorna `{"status": "ok"}`
- [ ] `python manage.py migrate` roda limpo (cria tabelas do Django + auditlog + base-kit)
- [ ] `/admin/` carrega (Django admin funcional)
- [ ] `docker compose logs web` não mostra erros fatais
- [ ] PostgreSQL recebe conexão do container `web` (testado via `docker compose exec db psql`)
- [ ] Redis recebe conexão (testado via `docker compose exec redis redis-cli ping`)
- [ ] `ruff check .` passa
- [ ] `.env.example` documenta todas as variáveis

## 7. Fora de escopo desta sprint

- Celery worker/beat (entram na Sprint 02 ou posterior)
- Apps de domínio (`apps.accounts`, `apps.schools`...) — sprints futuras
- Modelagem de School, User, Unit — sprints futuras
- Testes de integração (entram quando houver models)
- CI/CD