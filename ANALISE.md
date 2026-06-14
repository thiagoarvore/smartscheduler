# SmartSchedule (Grade Certa) — Análise & Roadmap

> Análise gerada em 13/06/2026 com base no `master` do repo `thiagoarvore/smartscheduler`.

## 1. Visão Geral

**Grade Certa** é um SaaS **multi-tenant** para escolas e redes educacionais **criarem, validarem e gerarem grades horárias complexas** (tipo fundamental II/médio). O domínio é um *timetabling problem* (NP-difícil) com regras pedagógicas, operacionais e de pessoal.

### Stack
- **Backend:** Django 6.0 + PostgreSQL 18.1
- **Multi-tenancy:** `django-tenants` (schema-based) — cada escola/rede = 1 schema
- **Auth:** Custom `User(AbstractUser)` com login por e-mail
- **Base:** `django-base-kit` (UUID + timestamps + auditlog + `active`)
- **UI:** DTL + HTMX + `widget_tweaks` (sem SPA, leve)
- **Container:** Docker + docker-compose
- **Deps:** Poetry (padrão) / pip-via-uv como alternativa
- **Testes:** pytest + pytest-django (SQLite em test mode)
- **Lint:** Ruff
- **Auditoria:** `django-auditlog`

---

## 2. Estado Atual (Sprint 7 — última fechada)

### ✅ Entregue
- **ÉPICO A — Fundação:** Docker, poetry, ruff, base-kit, tests
- **ÉPICO B — Tenancy + Auth:** django-tenants, schema público, User custom, login por e-mail, demo tenant bootstrap
- **ÉPICO C — Estrutura Escolar (Sprint 2):** Unit, TeachingLevel, SchoolYear, Period, ClassGroup
- **ÉPICO D — Currículo (Sprint 3):** Subject, CurriculumMatrix, WorkloadItem
- **ÉPICO E — Pessoas (Sprint 4):** Teacher, TeacherQualification, TeacherAvailability
- **ÉPICO F — Scheduling (Sprint 5):** Timetable, TimeSlot, Lesson, LessonComponent, validações
- **Sprint 6:** Importação, auditoria, hardening
- **Sprint 7 (última):** correções de cadastro, isolamento total por tenant, UX de forms com widget_tweaks, períodos/séries com herança global-vs-unit, disponibilidade como grid semanal, exclusões HTMX

### 📁 Estrutura dos Apps (DDD lógico dentro de cada app)
```
apps/
├── tenants/      # Tenant + Domain (schema público) + bootstrap
├── accounts/     # User custom (login e-mail)
├── schools/      # Unit, TeachingLevel, SchoolYear, Period, ClassGroup
├── curriculum/   # Subject, CurriculumMatrix, WorkloadItem
├── people/       # Teacher, TeacherQualification, TeacherAvailability
└── scheduling/   # Timetable, TimeSlot, Lesson, LessonComponent
```

---

## 3. Análise Crítica — O que está bom, o que falta

### ✅ Pontos Fortes
1. **Tenancy schema-based** é a escolha certa: isolamento real, backup por escola, GDPR-friendly
2. **BaseModel do django-base-kit** evita repetir `id/UUID/created_at/updated_at/active/auditlog` em todo model — produtividade
3. **Sprints curtas (2 semanas)** com DoD clara — sem half-done
4. **Demo tenant bootstrap** facilita onboarding e demos sem complicar produção (`DEMO_TENANT_ENABLED=False`)
5. **DTL + HTMX** > SPA para SaaS B2B: menor superfície de bug, melhor SEO, mais rápido de evoluir
6. **Herança global vs unit** (períodos, séries) com flag `is_tenant_default` é modelagem correta — atende a realidade de redes multi-unidade
7. **Auditlog já em uso** desde cedo — não foi retrofitted
8. **pyproject + poetry + ruff** — toolchain moderna

### ⚠️ Pontos de Atenção
1. **Algoritmo de geração da grade ainda não está claro.** Os models existem (Timetable, Lesson), mas não vi um `services/scheduler.py` ou solver real. É o **core do produto** — se não tem, o MVP não está pronto
2. **Testes:** vi `tests/test_settings.py`, `tests/conftest.py`, `tests/test_reports/` — preciso ver a cobertura. Se < 70% no scheduling, é risco
3. **Importação de planilhas (Sprint 6):** dito "entregue" mas precisa validar se funciona end-to-end com validação + erro handling
4. **Performance do tenant middleware** com muitos schemas — precisa ter índice em `Domain.domain`
5. **Sem `celery`/tarefas async** visível — geração de grade vai precisar (jobs longos)
6. **Sem CI/CD** visível (.github/workflows). Se não tem, você vai lembrar disso tarde
7. **Internacionalização:** strings estão em PT-BR (`gettext_lazy as _`), mas o `_("...")` precisa do locale configurado

### ❌ O que falta para MVP vendável
1. **Algoritmo de geração de grade** (solver — ainda não decidido, ver §5.1)
2. **Explicabilidade** ("por que essa aula ficou nesse slot?") — diferencial vs concorrente
3. **Detecção de inviabilidade** (dados incompletos → impossível montar grade)
4. **Editor visual da grade** (drag-and-drop ou pelo menos clica-e-arrasta)
5. **Exportação** (PDF, Excel, link público)
6. **Convite de usuários** (papéis: coord, prof, viewer)
7. **Faturamento/billing** (Asaas p/ Brasil) — multi-tenant SaaS sem isso é projeto, não produto

---

## 5.1 Restrições de produto já definidas

Restrições já consolidadas no **SDD de arquitetura** (`docs/SDD-arquitetura-sistema-grade-certa.md`):

- **§2.1 (Stack):** Task queue = **Celery + Redis**
- **§2.2.8 (Princípio):** Jobs longos não bloqueiam requests — execução obrigatória via Celery
- **§2.2.9 (Princípio):** Solver de grade pode demorar **até 30 minutos** por tenant
- **§13.2 (Docker):** Serviços `redis`, `worker`, `beat`, `flower` já estão no compose
- **§15.1 (Observabilidade):** Padrão de progresso, timeout e logs para tasks longas
- **§20 (Exemplo canônico):** Planilha de referência em `docs/exemplos/horario-fundamental-ii-referencia.xlsx` define a escala-alvo (15 unidades, ~95 turmas, 528 células) e o layout de saída

### Pendente de decisão

- [ ] Algoritmo do solver (heurística custom, OR-Tools CP-SAT, metaheurística, ou híbrido) — **ainda não decidido**
- [ ] Estratégia de importação do Excel de referência

### Quando reavaliar

- Se clientes reclamarem que 30 min é muito → reduzir (pode forçar escolha diferente de solver)
- Se clientes precisarem de SLA mais apertado → reavaliar solver

---

## 4. Roadmap Proposto — Próximas Fases

### 🚀 FASE 1 — Mínimo Viável do Coração (4-6 semanas)

> **Objetivo:** entregar a *promessa central* do produto — gerar uma grade válida.

#### Sprint 8 — Solver v1 (heurística)
- Implementar `apps/scheduling/services/solver_v1.py` com backtracking + ordenação por restrições (MRV)
- Constraints: professor não pode estar em 2 lugares, turma não pode ter 2 aulas no mesmo slot, capacidade do professor
- Comando: `python manage.py solve_timetable --timetable-id X`
- Async via `django-q` ou `celery` (decidir e instalar)
- Testes unitários do solver com fixtures de escolas pequenas

#### Sprint 9 — Detecção de inviabilidade
- Antes de rodar solver: validar que **dados são suficientes** (carga horária total = soma das aulas necessárias, professores habilitados, etc.)
- Mensagem clara: "Faltam 8 aulas de matemática na 7A. Adicione 1 prof com habilitação ou aumente carga horária"
- UI: dashboard "Saúde da Grade" antes de tentar gerar

#### Sprint 10 — Editor visual (HTMX, sem SPA)
- Tabela 5xN (dias x slots) com aulas
- Click numa aula → abre painel lateral com detalhes + opções de troca
- Trocar aula entre 2 slots via drag-and-drop nativo HTML5 (HTMX swap)
- Manter validações no backend (não confiar na UI)

#### Sprint 11 — Explicabilidade
- Cada aula alocada guarda `reason` (campo JSON): "professor X disponível, sala Y livre, regra Z respeitada"
- Botão "Por que essa alocação?" → mostra razão
- Diferencial competitivo real (nenhum concorrente tem isso bem feito)

### 🛠️ FASE 2 — Produção (4 semanas)

#### Sprint 12 — Hardening
- Rate limiting (`django-ratelimit`)
- Logging estruturado (`structlog`)
- Sentry
- Backups automatizados do PG (schema por tenant)
- Documentar `restore --tenant=<schema>`

#### Sprint 13 — Convite de usuários + papéis
- Roles: Admin (rede), Coordenador (unidade), Professor (leitura da própria grade)
- Convite por e-mail com token
- Permissões no backend via decorators/mixins, não só na UI

#### Sprint 14 — Billing
- `dj-stripe` + planos (Básico/Pro/Enterprise)
- Limites por plano (N unidades, N usuários)
- Webhook de pagamento → `Tenant.paid_until`

#### Sprint 15 — CI/CD + Observabilidade
- GitHub Actions: lint + test + build docker
- Deploy automatizado (fly.io / render / vps)
- Health check endpoint + dashboard Grafana básico

### 🌐 FASE 3 — Escala (4-6 semanas)

#### Sprint 16-17 — Importação robusta
- Excel/CSV com preview antes de salvar
- Validação linha-a-linha com relatório de erros
- Suporte a "modelo padrão" da rede (template)
- Importação em background (celery) com progresso

#### Sprint 18-19 — PWA / Mobile
- PWA instalável no celular
- Professor consulta **só a própria grade** no celular
- Notificação quando grade é atualizada

#### Sprint 20-21 — Diferenciação
- Geração multi-objetivo (minimizar janelas, balancear carga, respeitar preferências)
- Análise de impacto ("se trocar prof X por Y, quantas aulas mudam?")
- Simulador de cenários

---

## 5. Decisões Arquiteturais Pendentes

| Decisão | Opções | Minha recomendação |
|---------|--------|---------------------|
| Solver | OR-Tools (Google), heurística pura, SAT solver | **OR-Tools** se a escala for > 50 turmas; senão heurística é suficiente |
| Async | Celery, django-q, RQ | **django-q** se a infra for pequena; **Celery** se for crescer |
| Frontend | DTL+HTMX, Alpine+TURBO, React/Vue separado | **Manter DTL+HTMX** — vocês estão indo bem, não troquem |
| Hosting | Fly.io, Render, VPS, K8s | **Fly.io** para começar (simples, multi-region barato) |
| Billing | Stripe Iframe, Asaas (BR) | **Asaas** se for vender só no Brasil (nota fiscal inclusa) |
| PDF | WeasyPrint, ReportLab, headless Chrome | **WeasyPrint** (Django-friendly, templates HTML) |
| Editor grade | FullCalendar, build-it-yourself | **Build-it-yourself com HTMX** — controle total, sem lock-in |

---

## 6. Riscos & Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Solver não converge em escolas grandes | 🔴 Alto | Fallback para solver v1 (heurística) + UI de "edição manual" |
| Tenant leak (dados vazam entre escolas) | 🔴 Crítico | Testes E2E obrigatórios em CI; code review com checklist |
| Performance ruim com 100+ turmas | 🟡 Médio | Indexes em `(tenant_id, ...)`; cache de querysets pesados |
| Onboarding complexo | 🟡 Médio | Wizard de 1ª configuração com templates por nível de ensino |
| Vendor lock-in (BaseKit, django-tenants) | 🟢 Baixo | Ambos são OSS maduros, podem ser trocados com esforço médio |

---

## 7. TL;DR — O que eu faria AGORA

1. **Verificar se o solver v1 existe** (Sprint 8 do meu roadmap) — sem isso, não tem produto
2. **Adicionar CI no GitHub Actions** (lint + test) — 30 min de trabalho, evita regressões
3. **Métricas no scheduler** (tempo de geração, taxa de sucesso) — saber se está melhorando
4. **Documentar o algoritmo** (mesmo que heurística) em `docs/scheduler-algorithm.md` — pra você mesmo daqui a 3 meses

O projeto está **bem estruturado** e o ritmo de sprints é saudável. O gap real é o **algoritmo de geração** — é o coração do produto. Tudo o mais é execução disciplinada.
