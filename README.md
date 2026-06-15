# SmartScheduler — Grade Certa

Sistema SaaS multi-tenant para criação, validação e otimização de grades horárias escolares.

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Django 6.0 |
| Banco de dados | PostgreSQL 18.1 (produção) · SQLite (testes) |
| Multi-tenancy | django-tenants (schema-based isolation) |
| Task queue | Celery + Redis |
| Autenticação | Custom User model (email-based login) |
| Auditoria | django-auditlog |
| Estilos utilitários | django-base-kit (BaseModel, BaseModelForm) |
| Containerização | Docker + Docker Compose |
| Dependências | Poetry |
| Lint | Ruff |
| Testes | pytest + pytest-django |
| Timezone | `America/Sao_Paulo` (BRT/AMT) |

## Estrutura do projeto

```
smartscheduler/
├── config/
│   ├── settings.py            # Settings principal (PostgreSQL + django-tenants)
│   ├── settings_test.py        # Settings de teste (SQLite, sem django-tenants)
│   ├── urls.py                 # URLs raiz
│   └── tests/
│       └── test_settings_grade_certa.py
├── apps/
│   ├── tenants/                # Schema público: Tenant, Domain, bootstrap demo
│   │   ├── models.py           # TenantMixin, DomainMixin
│   │   ├── forms.py            # BaseModelForm (request= kwarg)
│   │   └── management/commands/bootstrap_demo_tenant.py
│   ├── accounts/               # User, login/logout
│   ├── schools/                # Unit, Period, TeachingLevel, Series, ClassGroup
│   ├── curriculum/             # Subject, CurriculumMatrix, WorkloadItem, SubjectRule
│   ├── people/                 # Teacher, TeacherQualification, TeacherAvailability
│   └── scheduling/              # SchoolYear, SolverVariant, SolverRun, Timetable, tasks
│       ├── models.py
│       ├── services/
│       │   ├── solver.py        # SolverService (3 variantes, greedy, retry)
│       │   ├── cooldown.py      # Cooldown 1x/hora por SchoolYear
│       │   ├── report.py        # Relatórios .md (Thiago + visual)
│       │   └── __init__.py
│       ├── tasks.py             # Celery tasks (run_3_variants, run_variant)
│       └── tests/
│           ├── test_solver_service.py
│           ├── test_cooldown.py
│           ├── test_reports.py
│           └── test_models.py
├── templates/
│   ├── base.html                # Navbar + sidebar condicional + page_content
│   ├── home.html                # Dashboard pós-login
│   ├── landing.html             # Landing page (pública)
│   └── partials/_sidebar.html
├── static/                      # CSS, JS, imagens
├── docs/
│   ├── PRD-grade-certa.md
│   ├── SDD-arquitetura-sistema-grade-certa.md   # §22.2–22.5
│   ├── SDD-conceitual-grade-certa.md
│   ├── modelagem-entidades-grade-certa.md
│   ├── regras-negocio.md
│   ├── planejamento-geral-grade-certa.md
│   └── sprints/
│       ├── sprint-08-solver-3-variantes.md
│       ├── sprint-09-camada-sugestoes.md
│       └── sprint-10-importacao-excel-referencia.md
├── conftest.py                  # SetTenantMiddleware (simula django-tenants em SQLite)
├── manage.py
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Como rodar

### Docker (produção-like)

```bash
cp .env.example .env
# Edite o .env com suas configurações
docker compose up --build
```

O bootstrap do tenant demo roda por padrão em ambiente local. Para desabilitar em produção:

```env
DEMO_TENANT_ENABLED=False
```

### Desenvolvimento local (Poetry)

```bash
poetry install
DJANGO_SETTINGS_MODULE=config.settings poetry run python manage.py migrate_schemas --shared
DJANGO_SETTINGS_MODULE=config.settings poetry run python manage.py migrate
DJANGO_SETTINGS_MODULE=config.settings poetry run python manage.py bootstrap_demo_tenant
DJANGO_SETTINGS_MODULE=config.settings poetry run python manage.py runserver
```

> **Nota:** Desenvolvimento local requer PostgreSQL rodando (localhost:5432 ou Docker apenas para o db).

### Testes (SQLite, sem PostgreSQL)

```bash
DJANGO_SETTINGS_MODULE=config.settings_test poetry run pytest -v
```

### Lint

```bash
poetry run ruff check .
poetry run ruff format .
```

## Variáveis de ambiente

Ver [`.env.example`](.env.example) para referência completa.

| Variável | Default | Descrição |
|----------|---------|-----------|
| `ENVIRONMENT` | `local` | `local`, `dev`, `test`, `staging`, `production` |
| `DEBUG` | automático (True em `local`/`dev`) | Debug mode Django |
| `SECRET_KEY` | `django-insecure-smartschedule-dev-key-...` | Chave secreta Django |
| `DB_NAME` | `smartschedule` | Nome do banco PostgreSQL |
| `DB_USER` | `postgres` | Usuário do banco |
| `DB_PASSWORD` | `postgres` | Senha do banco |
| `DB_HOST` | `db` | Host do banco (Docker: `db`, local: `localhost`) |
| `DB_PORT` | `5432` | Porta do banco |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,.localhost` | Hosts permitidos (comma-separated) |
| `DEMO_TENANT_ENABLED` | automático (True em `local`/`dev`) | Cria tenant demo no bootstrap |
| `DEMO_TENANT_NAME` | `Colegio Objetivo` | Nome do tenant demo |
| `DEMO_TENANT_SCHEMA_NAME` | `colegioobjetivo` | Schema name do tenant demo |
| `DEMO_TENANT_DOMAIN` | `localhost` | Domínio do tenant demo |
| `GRADE_CERTA_COOLDOWN_DISABLED` | automático (True em `local`/`dev`/`test`) | Desabilita cooldown do solver em ambientes não-produção |

> **Importante:** `ENVIRONMENT` controla 3 comportamentos automáticos:
> - `DEBUG=True` quando `ENVIRONMENT` ∈ `{local, dev}`
> - `GRADE_CERTA_COOLDOWN_DISABLED=True` quando `ENVIRONMENT` ∈ `{local, dev, test}`
> - `DEMO_TENANT_ENABLED=True` quando `ENVIRONMENT` ∈ `{local, dev}`

## Arquitetura multi-tenant

O sistema usa **django-tenants** com isolamento por schema PostgreSQL:

- **Schema `public`**: `Tenant`, `Domain`, `User` — tabelas compartilhadas
- **Schema por tenant**: `Unit`, `Period`, `Teacher`, `Subject`, `Timetable`, etc. — dados isolados por escola

O middleware `DefaultTenantMiddleware` resolve o tenant pelo domínio da requisão e injeta `request.tenant`.

## Solver (Grade Certa)

O solver gera grades horárias com 3 variantes concorrentes:

| Variante | Estratégia |
|----------|-----------|
| A — Restart | Construtor greedy + múltiplos restarts |
| B — Hill Climbing | Construtor greedy + hill climbing local |
| C — Hybrid | Construtor greedy + restarts + hill climbing |

- Resultado: a variante com menos buracos vence (desempate: menor tempo total)
- Cooldown: 1 execução por hora por SchoolYear (`GRADE_CERTA_COOLDOWN_DISABLED` desabilita em dev)
- Relatórios: `relatorio-solver-{SY}-{TS}.md` (enxuto) + `grade-{SY}-{TS}.md` (visual)

## Testes

- **132 testes** (1 falha restante em `test_unit_create_persists_object` — `SetTenantMiddleware` não injeta `request.tenant` corretamente no Django test Client POST)
- Settings de teste: `config/settings_test.py` (SQLite, sem django-tenants, com `SetTenantMiddleware`)
- Fixture central: `conftest.py` com `SetTenantMiddleware` e fixtures `tenant`, `authenticated_user`

## Documentação

- [Regras de negócio](docs/regras-negocio.md)
- [PRD](docs/PRD-grade-certa.md)
- [SDD Conceitual](docs/SDD-conceitual-grade-certa.md)
- [SDD Arquitetura](docs/SDD-arquitetura-sistema-grade-certa.md) — §22.2–22.5 (solver, cooldown, relatórios, métricas)
- [Modelagem de entidades](docs/modelagem-entidades-grade-certa.md)
- [Planejamento geral](docs/planejamento-geral-grade-certa.md)
- Sprint docs em [docs/sprints/](docs/sprints/)

## Licença

Projeto proprietário. Todos os direitos reservados.