# Grade Certa — Sprint 08

> **Sprint:** 08
> **Nome:** Solver — Três Variantes e Pipeline de Execução
> **Duração sugerida:** 3 semanas
> **Objetivo macro:** implementar o solver com as 3 variantes (A/B/C) em paralelo, infraestrutura de execução via Celery, persistência de runs e UI do botão "Rodar Grade Certa".

## 1. Sprint Goal

Entregar uma versão funcional do sistema de geração de grade horária onde:

- as 3 variantes (A - Restart, B - Hill Climbing, C - Híbrido) rodam sequencialmente via Celery;
- cada execução é persistida em `solver_run` com 8 métricas (§22.2.9);
- a UI permite disparar a geração e mostra a grade vencedora;
- cooldown 1x/hora funciona (e é desativado em ambiente não-produção);
- falhas transientes têm 1 retry transparente.

## 2. Domínio coberto

- **Scheduling** — solver, modelos `solver_variant` e `solver_run`, Celery tasks
- **Sistema** — settings (`NON_PRODUCTION_ENVIRONMENTS`), `TIME_ZONE`
- **UI** — view do botão "Rodar Grade Certa", página de resultado

## 3. Escopo da sprint

### 3.1 Contratos e tipos de domínio (TDD primeiro)

- [ ] Criar `apps/scheduling/solver/types.py` com dataclasses:
  - `Timetable` (input completo: turmas, professores, slots, restrições)
  - `Solution` (output: lista de `LessonAssignment`, `completude: float`, `buracos: list[Buraco]`)
  - `Buraco` (dia, número_aula, turma, motivo)
  - `Restricao` (rígida ou flexível)
  - `SolverError`, `UnsatisfiableError` (exceções do solver)
- [ ] Definir interface comum: `Solver.solve(timetable: Timetable, deadline: timedelta) -> Solution`
- [ ] Testes: 1 teste por tipo garantindo criação, serialização JSON, igualdade

### 3.2 Model `solver_variant`

- [ ] Migration criando `apps/scheduling/models.py:SolverVariant`:
  - FK `tenant`, FK `school_year` (nullable = global)
  - `nome` (choice: `A-Restart | B-HillClimbing | C-Hybrid`)
  - `descricao` (TextField)
  - `is_active` (bool, default True — 3 variantes coexistem)
  - `parametros` (JSONField com seed, timeout, max_restarts, etc.)
  - `criado_em`, `atualizado_em` (BaseModel)
- [ ] Admin Django: listar, criar, editar (sem delete em produção)
- [ ] Data migration: criar as 3 variantes (A, B, C) com `is_active=True`
- [ ] Testes: criação, listagem, constraint de unicidade `(tenant, school_year, nome)`

### 3.3 Model `solver_run`

- [ ] Migration criando `apps/scheduling/models.py:SolverRun`:
  - `variant_fk` (FK SolverVariant)
  - `school_year_fk` (FK SchoolYear, indexado)
  - `started_at`, `finished_at`
  - `status` (choice: `success | failed | interrupted`, default vazio)
  - `buracos` (int, default null)
  - `completude` (float 0-1, default null)
  - `tempo_ate_1a_solucao` (DurationField, nullable)
  - `tempo_total` (DurationField)
  - `iteracoes` (int, default 0)
  - `restarts` (int, default 0)
  - `criterio_parada` (choice: `timeout | zero_buracos | erro | interrupted`, nullable)
  - `seed` (int)
  - `solution_json` (JSONField, nullable)
  - `error_message` (TextField, nullable)
  - `disparado_por` (choice: `user | cron | api`)
  - `disparado_por_user` (FK User, nullable)
  - `suggestions_status` (choice: `not_run | running | done | timeout | disabled`, default `not_run`)
  - `suggestions_count` (int, default 0)
- [ ] Admin Django: readonly (não editar runs finalizados)
- [ ] Testes: criação, validação de status, querysets filtrados por tenant

### 3.4 Field `last_solver_run_at` em `SchoolYear`

- [ ] Migration: adicionar `last_solver_run_at: DateTimeField(null=True, db_index=True)` em `apps/schools/models.py:SchoolYear`
- [ ] Testes: campo nullable, index criado

### 3.5 Settings: `NON_PRODUCTION_ENVIRONMENTS` e `TIME_ZONE`

- [ ] Editar `config/settings.py`:
  - Adicionar `NON_PRODUCTION_ENVIRONMENTS = {"local", "dev", "test"}` (preservar `DEVELOPMENT_ENVIRONMENTS` existente)
  - Adicionar `GRADE_CERTA_COOLDOWN_DISABLED = ENVIRONMENT in NON_PRODUCTION_ENVIRONMENTS`
  - Adicionar `TIME_ZONE = "America/Sao_Paulo"` (era default do Django — mudou em 13/06/2026, decisão Thiago)
  - Adicionar `USE_TZ = True`
- [ ] Testes: setting muda corretamente conforme `ENVIRONMENT`

### 3.6 Variante A — Restart

- [ ] Implementar `apps/scheduling/solver/variant_a_restart.py`
- [ ] Construtor ingênuo: aloca aulas em ordem de `WorkloadItem.weekly_hours DESC` (heurística inicial)
- [ ] Loop: roda construtor N vezes (`max_restarts` em `parametros`), fica com a melhor `Solution`
- [ ] Cada tentativa curta (~18s)
- [ ] Retorna `Solution` com `completude` e `buracos`
- [ ] Salva checkpoint da `Solution` em `solver_run.solution_json` a cada restart
- [ ] Testes: 1 fixture pequena (5 turmas), verifica que produz grade válida, métricas preenchidas

### 3.7 Variante B — Hill Climbing

- [ ] Implementar `apps/scheduling/solver/variant_b_hill_climbing.py`
- [ ] 1 construção inicial (mesmo construtor da A)
- [ ] Loop: a cada iteração, gera 10 vizinhos (swap de 2 aulas aleatórias), aceita se `buracos` melhora
- [ ] Critério de parada: timeout (30 min) OU 0 buracos
- [ ] Sem temperatura (hill climbing puro, não simulated annealing)
- [ ] Retorna `Solution` com métricas
- [ ] Testes: fixture pequena, verifica que melhora a `Solution` ao longo das iterações

### 3.8 Variante C — Híbrido

- [ ] Implementar `apps/scheduling/solver/variant_c_hybrid.py`
- [ ] Várias construções (N=`max_construcoes` em `parametros`, cada uma com seed diferente)
- [ ] Pra cada construção, 1-2 min de hill climbing
- [ ] Fica com a melhor `Solution` global
- [ ] Retorna `Solution` com métricas
- [ ] Testes: fixture pequena, verifica que encontra melhor solução que A e B isolados

### 3.9 Celery task `run_3_variants`

- [ ] Criar `apps/scheduling/tasks.py:run_3_variants`:
  - Assinatura: `run_3_variants(school_year_id: UUID, disparado_por: str, user_id: UUID | None)`
  - Encadeia 3 tasks: `run_variant_a`, `run_variant_b`, `run_variant_c` (em sequência)
  - Cada `run_variant_X`:
    - Cria `solver_run` com `status=""`, `started_at=now()`
    - Carrega variante, instancia solver
    - Roda `solver.solve(timetable, deadline=30min)`
    - Preenche métricas, `status="success"` ou `"failed"`
    - Atualiza `last_solver_run_at` da SchoolYear
  - Após as 3, dispara `run_suggestions_layer` (Sprint 09, pode ser stub)
- [ ] Fila: `scheduler-long` (separada do default)
- [ ] Testes: task roda em modo eager, verifica que 3 `solver_run` foram criados

### 3.10 Wrapper de retry transiente

- [ ] Criar `apps/scheduling/tasks.py:transient_retry` decorator:
  - Detecta exceções transientes (§22.2.5): `OperationalError`, `InterfaceError`, `redis.ConnectionError`, `celery.exceptions.TimeoutError`
  - Em caso de transiente: log + retry 1x (sem backoff)
  - Em caso de não-transiente: propaga
  - Total máximo: 2 tentativas
- [ ] Aplicar em `run_variant_a/b/c`
- [ ] Testes: mock que lança `OperationalError` na 1ª tentativa, sucesso na 2ª, conta de tentativas = 2

### 3.11 View: botão "Rodar Grade Certa"

- [ ] Criar `apps/scheduling/views.py:run_timetable_view` (POST)
- [ ] Decorator `@login_required`
- [ ] Lógica:
  1. Verifica cooldown: `if last_solver_run_at and (now - last_solver_run_at) < 1h AND NOT GRADE_CERTA_COOLDOWN_DISABLED`
  2. Se em cooldown: retorna mensagem "⚠️ A geração da grade só pode ser rodada 1x por hora. Última execução: hoje HH:MM (America/Sao_Paulo). Próxima janela: HH:MM (America/Sao_Paulo)."
  3. Se liberado: dispara `run_3_variants.delay(school_year_id, 'user', request.user.id)`
  4. Redireciona pra página de progresso
- [ ] URL: `/scheduling/run/` em `apps/scheduling/urls.py`
- [ ] Template: botão no header da UI principal (`templates/base.html` ou similar)
- [ ] Testes: POST bloqueado em cooldown, POST liberado em janela, mensagem em JST

### 3.12 View: progresso e resultado

- [ ] Criar `apps/scheduling/views.py:run_progress_view` (GET)
- [ ] Mostra status atual: "Rodando variante A... (15 min elapsed)"
- [ ] HTMX poll a cada 30s atualiza o status
- [ ] Quando todas terminam: redireciona pra `run_result_view`
- [ ] Testes: status muda conforme `solver_run.status`, polling para quando todas terminam

### 3.13 View: resultado (grade visual)

- [ ] Criar `apps/scheduling/views.py:run_result_view` (GET)
- [ ] Identifica vencedora: `solver_run` com menor `buracos` entre os 3 da última execução; empate = menor `tempo_total`
- [ ] Renderiza grade semanal: tabela HTML com `turma × dia × aula`
- [ ] Botão "Baixar grade completa (.xlsx)" (futuro, pode ser placeholder disabled)
- [ ] Painel "💡 Sugestões para reduzir buracos" (placeholder, Sprint 09 popula)
- [ ] Testes: ordenação de vencedora, renderização de grade, botão de download

### 3.14 Geração de relatórios `.md` no Drive

- [ ] Criar `apps/scheduling/services/report.py`
- [ ] Função `generate_solver_report_md(school_year, runs) -> str` — gera `relatorio-solver-...md` (§22.2.7)
- [ ] Função `generate_grade_md(school_year, winning_run) -> str` — gera `grade-...md`
- [ ] Função `upload_to_drive(folder_id, filename, content) -> str` — wrapper GAPI
- [ ] Folder IDs:
  - `hermes-backup/{tenant.slug}/relatorios-solver/` (criar se não existir)
  - `hermes-backup/{tenant.slug}/grades-geradas/` (criar se não existir)
- [ ] Chamada: no `finally` de `run_3_variants` (mesmo em `failed`/`interrupted`, salva cabeçalho)
- [ ] Testes: mock GAPI, verifica que 2 arquivos foram "upados" com nomes corretos

## 4. Entregáveis

1. Contratos do solver (`types.py`) com testes
2. Models `solver_variant` e `solver_run` com migrations e admin
3. 3 variantes funcionais (A/B/C) com testes
4. Celery task `run_3_variants` com retry transiente
5. UI completa: botão "Rodar Grade Certa", progresso, resultado
6. Cooldown 1x/hora com detecção de ambiente não-produção
7. Geração automática de 2 `.md` no Drive
8. Settings `NON_PRODUCTION_ENVIRONMENTS`, `TIME_ZONE`, `GRADE_CERTA_COOLDOWN_DISABLED`
9. Field `last_solver_run_at` em `SchoolYear`

## 5. Itens de backlog da sprint

### Contratos
1. [ ] Criar `apps/scheduling/solver/types.py` com `Timetable`, `Solution`, `Buraco`, `Restricao`
2. [ ] Criar exceções `SolverError`, `UnsatisfiableError`
3. [ ] Definir interface `Solver.solve(timetable, deadline) -> Solution`
4. [ ] Testes unitários dos tipos

### Model `solver_variant`
5. [ ] Criar model `SolverVariant` em `apps/scheduling/models.py`
6. [ ] Migration inicial
7. [ ] Data migration criando A, B, C com `is_active=True`
8. [ ] Registrar no admin Django
9. [ ] Testes de criação e constraints

### Model `solver_run`
10. [ ] Criar model `SolverRun` com 8 métricas + 2 de suggestions
11. [ ] Migration inicial
12. [ ] Registrar no admin Django (somente leitura)
13. [ ] Testes de criação e querysets por tenant

### SchoolYear
14. [ ] Adicionar `last_solver_run_at` ao model `SchoolYear`
15. [ ] Migration
16. [ ] Teste do campo e index

### Settings
17. [ ] Adicionar `NON_PRODUCTION_ENVIRONMENTS` em `settings.py`
18. [ ] Adicionar `GRADE_CERTA_COOLDOWN_DISABLED` em `settings.py`
19. [ ] Adicionar `TIME_ZONE = "America/Sao_Paulo"` e `USE_TZ = True`
20. [ ] Testes: setting muda por `ENVIRONMENT`

### Variantes
21. [ ] Implementar `variant_a_restart.py` com construtor + N restarts
22. [ ] Testes da variante A com fixture pequena
23. [ ] Implementar `variant_b_hill_climbing.py` com busca local
24. [ ] Testes da variante B
25. [ ] Implementar `variant_c_hybrid.py` com N construções + hill climbing
26. [ ] Testes da variante C
27. [ ] Teste comparativo: C vence A e B em pelo menos 1 fixture

### Celery
28. [ ] Criar `tasks.py:run_3_variants` encadeando A → B → C
29. [ ] Criar `run_variant_a/b/c` com persistência de `solver_run`
30. [ ] Configurar fila `scheduler-long` no Celery
31. [ ] Criar decorator `transient_retry` com lista de exceções transientes
32. [ ] Aplicar retry nas 3 variantes
33. [ ] Testes: retry acontece, total ≤ 2 tentativas

### Views e UI
34. [ ] Criar `run_timetable_view` (POST) com lógica de cooldown
35. [ ] Criar `run_progress_view` (GET) com HTMX polling
36. [ ] Criar `run_result_view` (GET) com grade visual
37. [ ] Adicionar botão "Rodar Grade Certa" no template base
38. [ ] Mensagem de bloqueio em JST
39. [ ] Testes: cooldown bloqueia POST, libera POST, JST correto

### Relatórios
40. [ ] Criar `services/report.py` com `generate_solver_report_md`
41. [ ] Criar `generate_grade_md`
42. [ ] Criar `upload_to_drive` wrapper
43. [ ] Criar/criar folders `relatorios-solver/` e `grades-geradas/` por tenant
44. [ ] Chamar geração no `finally` de `run_3_variants`
45. [ ] Testes: 2 arquivos gerados com nomes corretos

## 6. Critérios de aceite

- [ ] As 3 variantes rodam em sequência via Celery
- [ ] Cada `solver_run` persiste as 8 métricas + 2 de suggestions
- [ ] UI permite disparar a geração e mostra a grade vencedora
- [ ] Cooldown 1x/hora bloqueia novo POST; `GRADE_CERTA_COOLDOWN_DISABLED=True` libera
- [ ] Falhas transientes têm 1 retry automático; não-transientes falham direto
- [ ] Relatórios `relatorio-solver-...md` e `grade-...md` são gerados no Drive após cada execução
- [ ] Mensagem de bloqueio mostra horário em BRT (America/Sao_Paulo)
- [ ] Settings `NON_PRODUCTION_ENVIRONMENTS`, `TIME_ZONE`, `USE_TZ` configurados
- [ ] Testes cobrem: contratos, models, 3 variantes, retry, views, relatórios

## 7. Riscos e pontos de atenção

- **Tempo total ~90 min** — exige Celery worker dedicado na fila `scheduler-long`, não pode conflitar com filas rápidas
- **Memória do worker** — variantes podem estourar OOM em escolas grandes (95+ turmas). Configurar `--max-memory-per-child=2GB` no Celery
- **Variante C tem 2 loops aninhados** — código mais complexo, mais chance de bug. TDD obrigatório
- **Serialização de `Solution` para JSON** — pode inflar `solver_run.solution_json` (95 turmas × 30 aulas × 5 dias = ~14k entradas). Considerar comprimir (`gzip` + `base64`) ou só salvar métricas + download sob demanda
- **Drive upload falha** — não pode quebrar a execução. Try/except com log; `solver_run` ganha campo `report_upload_status`
- **Retry transparente esconde bugs** — se `OperationalError` é comum, retry mascara problema. Adicionar log `WARNING` em todo retry

## 8. Dependências

- Sprint 05 (scheduling) — models `Timetable`, `LessonAssignment`, etc já existem
- Sprint 07 (correção cadastros) — UI padronizada, base pra botão
- §22.1, §22.2 — decisões já consolidadas neste SDD
- Sprint 09 (camada de sugestões) — `suggestions_status` e `suggestions_count` já são criados aqui mas preenchidos lá
- Sprint 10 (importação Excel) — `last_solver_run_at` em `SchoolYear` é pré-requisito pra rodar solver em dados importados

## 9. Definição de pronto

A sprint pode ser considerada pronta quando:

- todos os 45 itens do checklist estiverem marcados;
- as 3 variantes passam nos testes com fixture pequena (5 turmas);
- a UI permite disparar e ver resultado end-to-end;
- cooldown funciona em prod (`GRADE_CERTA_COOLDOWN_DISABLED=False`) e é desativado em dev/test;
- relatórios `.md` são gerados e "upados" no Drive (mesmo com mock do GAPI);
- nenhum teste flaky em CI.
