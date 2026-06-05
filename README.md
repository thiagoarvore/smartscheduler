# SmartSchedule

Projeto do produto **Grade Certa**.

Sistema SaaS multi-tenant para criacao, validacao e otimizacao de grades horarias escolares complexas.

## Stack

- **Backend:** Django 6.0
- **Banco de dados:** PostgreSQL 18.1
- **Multi-tenancy:** django-tenants (schema-based)
- **Autenticacao:** Custom User model (email-based login)
- **Containerizacao:** Docker + Docker Compose
- **Gerenciamento de dependencias:** Poetry
- **Verificacao dev:** Ruff
- **Testes:** pytest + pytest-django
- **Base estrutural:** django-base-kit
- **Auditoria:** django-auditlog

## Sprint 1 — Entregaveis

- [x] Projeto sobe localmente via Docker
- [x] Banco PostgreSQL funcionando
- [x] Tenant criado e resolvido por dominio
- [x] Autenticacao inicial operacional (login por email)
- [x] Estrutura base dos apps pronta
- [x] Lint e testes basicos passando

## Estrutura do projeto

```text
smartschedule/
├─ config/                    # Settings, URLs, WSGI, ASGI
├─ apps/
│  ├─ tenants/                # Schema publico: Tenant e Domain (django-tenants)
│  └─ accounts/               # Autenticacao, User customizado, login
├─ templates/                 # Templates base (login, home)
├─ static/                    # Arquivos estaticos
├─ tests/                     # Testes gerais do projeto
├─ manage.py
├─ pyproject.toml
├─ Dockerfile
├─ docker-compose.yml
└─ docs/                      # Documentacao de sprints e SDD
```

## Como rodar

### Com Docker (recomendado)

```bash
cp .env.example .env
# Edite o .env com suas configuracoes
docker compose up --build
```

### Para testes locais (SQLite)

```bash
poetry install
DJANGO_SETTINGS_MODULE=config.settings_test poetry run pytest -v
```

### Lint

```bash
poetry run ruff check .
```

## Documentacao

- [Regras de negocio](docs/regras-negocio.md)
- [PRD](docs/PRD-grade-certa.md)
- [SDD Conceitual](docs/SDD-conceitual-grade-certa.md)
- [SDD Arquitetura](docs/SDD-arquitetura-sistema-grade-certa.md)
- [Modelagem de entidades](docs/modelagem-entidades-grade-certa.md)
- [Planejamento geral](docs/planejamento-geral-grade-certa.md)