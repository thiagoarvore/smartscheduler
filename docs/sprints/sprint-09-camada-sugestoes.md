# Grade Certa — Sprint 09

> **Sprint:** 09
> **Nome:** Camada de Sugestões e Relatórios no Drive
> **Duração sugerida:** 2 semanas
> **Objetivo macro:** implementar a camada de sugestões (§20.4, §22.4) que varre o espaço de parâmetros após cada execução do solver, gera sugestões de melhorias concretas e as exibe na UI; finalizar pipeline de relatórios `.md` no Drive.

## 1. Sprint Goal

Entregar uma versão onde, após cada execução bem-sucedida do solver com buracos remanescentes:

- a camada de sugestões roda automaticamente em Celery separado (≤10 min);
- até 20 sugestões concretas são geradas (4 categorias × 5 cada);
- as sugestões aparecem na UI da grade vencedora;
- 2 relatórios `.md` (solver + grade) são gerados no Drive por execução.

## 2. Domínio coberto

- **Scheduling** — service de sugestões, model `Suggestion`, Celery task
- **UI** — painel de sugestões, modal de detalhes
- **Integração** — Google Drive (geração de pastas, upload)

## 3. Escopo da sprint

### 3.1 Model `Suggestion`

- [ ] Criar `apps/scheduling/models.py:Suggestion` (§22.4.2):
  - FK `school_year`, FK `solver_run`
  - `categoria` (choice: `workload_increase | teacher_add | teacher_availability | subject_rule_relax`)
  - `titulo` (CharField max 200)
  - `descricao` (TextField)
  - `buracos_antes`, `buracos_depois` (int)
  - `delta` (int, computed: `buracos_antes - buracos_depois`)
  - `param_diff` (JSONField)
  - `criado_em` (auto_now_add)
  - `aplicado_em` (DateTimeField, nullable)
  - `status` (choice: `pending | applied | ignored`, default `pending`)
  - Indexes: `(school_year, -criado_em)`, `(solver_run)`
- [ ] Migration
- [ ] Testes: criação, JSON round-trip, index criado

### 3.2 Field `suggestions_enabled` em `SchoolYear`

- [ ] Adicionar `suggestions_enabled: bool` (default True) ao model `SchoolYear`
- [ ] Migration
- [ ] Teste: default True, configurável por SchoolYear

### 3.3 Service `SuggestionsService`

- [ ] Criar `apps/scheduling/services/suggestions.py:SuggestionsService`
- [ ] Classe recebe `solver_run: SolverRun` no construtor
- [ ] Carrega `school_year` e valida que `buracos > 0` e `suggestions_enabled=True`
- [ ] Método `run_all_categories() -> list[Suggestion]`:
  1. `self._run_workload_increase()` → retorna até 5 sugestões
  2. `self._run_teacher_add()` → até 5
  3. `self._run_teacher_availability()` → até 5
  4. `self._run_subject_rule_relax()` → até 5
  5. Concatena e retorna tudo
- [ ] Cada método privado:
  - Itera sobre os parâmetros da categoria
  - Pra cada, simula mudança e chama `solver.solve_rapido(timetable, deadline=60s)`
  - Compara `novos_buracos` com `buracos_atuais`
  - Se melhorou, cria `Suggestion` com `delta` e `param_diff`
  - Retorna top 5 por `delta DESC`
- [ ] Versão rápida do solver (`solve_rapido`):
  - Reutiliza `Solver.solve` com `deadline=60s`
  - Foco em resolver só buracos remanescentes (heurística: congelar aulas já alocadas)
- [ ] Testes: 1 teste por categoria com fixture que produz melhoria, 1 teste com timeout (mock)

### 3.4 Celery task `run_suggestions_layer`

- [ ] Criar `apps/scheduling/tasks.py:run_suggestions_layer` (§22.4.5):
  - Assinatura: `run_suggestions_layer(solver_run_id: UUID)`
  - Lógica:
    1. Carrega `solver_run`
    2. Se `buracos == 0` ou `school_year.suggestions_enabled == False`: marca `suggestions_status="disabled"`, retorna
    3. Marca `suggestions_status="running"`
    4. Roda `SuggestionsService(solver_run).run_all_categories()` (try/except com timeout de 10 min via `signal.alarm` ou similar)
    5. Em sucesso: `suggestions_status="done"`, `suggestions_count=len(result)`
    6. Em timeout: `suggestions_status="timeout"`
    7. Em exceção: `suggestions_status="failed"`, log do stack trace, **NÃO** propaga (não pode matar o pipeline)
- [ ] Fila: `scheduler-medium`
- [ ] Chamada: encadeada após `run_3_variants` terminar
- [ ] Testes: roda em modo eager, verifica que sugestões foram criadas e status correto

### 3.5 UI: painel de sugestões na grade vencedora

- [ ] Editar `apps/scheduling/views.py:run_result_view` (criado na Sprint 08)
- [ ] Adicionar query: `solver_run.suggestions.order_by("-delta")` (related_name de `Suggestion`)
- [ ] Renderizar painel colapsável `<details>` com lista de sugestões
- [ ] Visível só se `suggestions_count > 0`
- [ ] Cada item mostra: `titulo`, `descricao`, `delta` (com badge colorido: verde se delta ≥ 3, amarelo se 1-2)
- [ ] Botões: `[Aplicar]` (placeholder disabled com tooltip "Previsto pra sprint futura"), `[Detalhes]`, `[Ignorar]`
- [ ] Testes: painel aparece com `count > 0`, não aparece com `count == 0`, badges coloridos corretos

### 3.6 Modal "Detalhes" da sugestão

- [ ] View HTMX: `apps/scheduling/views.py:suggestion_detail_view` (GET)
- [ ] Retorna partial template com:
  - `param_diff` formatado em JSON legível
  - Histórico de tentativas (se houver)
  - Botão "Voltar" fecha o modal
- [ ] Testes: retorna 200 pra sugestão existente, 404 pra inexistente, partial correto

### 3.7 Botão "Ignorar" sugestão

- [ ] View POST: `apps/scheduling/views.py:suggestion_ignore_view` (POST)
- [ ] Marca `status="ignored"`, `aplicado_em=now()`
- [ ] Retorna HTMX response que remove a sugestão da lista (swap outer)
- [ ] Testes: POST muda status, retorna partial de "ignorado"

### 3.8 Geração de relatórios `.md` (consolidação)

- [ ] Criar `apps/scheduling/services/report.py` (base — Sprint 08 já criou)
- [ ] Função `generate_solver_report_md(school_year, runs) -> str`:
  - Cabeçalho: escola, ano letivo, timestamp JST, quem disparou, tenant, total de aulas
  - Seção "🏆 Variante Vencedora" com 6 campos
  - Tabela comparativa das 3 variantes (8 colunas)
  - Rodapé: link pro `solver_run` vencedor
- [ ] Função `generate_grade_md(school_year, winning_run) -> str`:
  - Cabeçalho: escola, ano letivo, timestamp JST, total de buracos
  - Grade visual: 1 tabela HTML/Markdown por turma
  - Linhas: horário (07:00–07:50, 07:50–08:40, ...)
  - Colunas: Seg, Ter, Qua, Qui, Sex
  - Células: disciplina (e professor se cabe)
- [ ] Testes: 2 funções com fixture pequena, verifica estrutura

### 3.9 Integração Google Drive

- [ ] Service `apps/scheduling/services/drive.py`
- [ ] Função `get_or_create_folder(tenant_slug, subfolder) -> str`:
  - Usa GAPI (google-api-python-client) já instalado no venv-gws
  - Procura `hermes-backup/{tenant_slug}/{subfolder}` no Drive
  - Se não existe, cria (com parent correto)
  - Retorna folder ID
- [ ] Função `upload_md(folder_id, filename, content) -> str`:
  - Cria arquivo `.md` no folder
  - Content-Type: `text/markdown`
  - Retorna file ID do Drive
- [ ] Token: reusar `/opt/data/google_token.json` (8 escopos, já tem Drive)
- [ ] Testes: mock GAPI, verifica chamadas corretas (2 uploads por execução)
- [ ] Teste integração manual: rodar solver de verdade em dev, verificar Drive

### 3.10 Falha no upload não pode quebrar pipeline

- [ ] `run_suggestions_layer` (e `run_3_variants` da Sprint 08) envolvem upload em try/except
- [ ] Falha de upload: loga, marca `report_upload_status="failed"` em `solver_run`, **NÃO** propaga exceção
- [ ] Campo novo em `SolverRun`: `report_upload_status: choice[pending, success, failed, disabled]`, default `pending`
- [ ] Testes: mock GAPI que lança exceção, pipeline continua, status fica `failed`

## 4. Entregáveis

1. Model `Suggestion` com migration e testes
2. Field `suggestions_enabled` em `SchoolYear`
3. `SuggestionsService` com 4 categorias implementadas
4. Solver rápido (`solve_rapido`) funcional
5. Celery task `run_suggestions_layer` com tratamento de timeout
6. Painel de sugestões na UI com 3 botões
7. Modal de detalhes e ação de ignorar
8. Service de geração de 2 relatórios `.md`
9. Integração com Google Drive (criação de pastas, upload)
10. Robustez: falhas de upload não quebram pipeline

## 5. Itens de backlog da sprint

### Model `Suggestion`
1. [ ] Criar model `Suggestion` com todos os campos
2. [ ] Migration
3. [ ] Indexes `(school_year, -criado_em)` e `(solver_run)`
4. [ ] Testes de criação, JSON round-trip

### SchoolYear
5. [ ] Adicionar `suggestions_enabled: bool` (default True)
6. [ ] Migration
7. [ ] Teste do campo

### Service
8. [ ] Criar `SuggestionsService` em `services/suggestions.py`
9. [ ] Implementar `_run_workload_increase`
10. [ ] Implementar `_run_teacher_add`
11. [ ] Implementar `_run_teacher_availability`
12. [ ] Implementar `_run_subject_rule_relax`
13. [ ] Implementar `solve_rapido` no solver (reutiliza `solver.solve` com deadline curto)
14. [ ] Testes: 1 teste por categoria + 1 teste de timeout
15. [ ] Teste de top-5 por delta

### Celery
16. [ ] Criar `tasks.py:run_suggestions_layer`
17. [ ] Configurar fila `scheduler-medium`
18. [ ] Encadear após `run_3_variants` (na Sprint 08)
19. [ ] Testes: status `disabled` quando buracos=0 ou desativado
20. [ ] Testes: status `done` em sucesso
21. [ ] Testes: status `timeout` quando excede 10 min
22. [ ] Testes: exceção não propaga

### UI
23. [ ] Editar `run_result_view` pra incluir painel de sugestões
24. [ ] Criar template do painel colapsável
25. [ ] Badges coloridos por delta
26. [ ] Botão `[Aplicar]` placeholder disabled
27. [ ] Botão `[Detalhes]` abre modal
28. [ ] Botão `[Ignorar]` POST e remove da lista
29. [ ] Testes: painel visível/invisível, badges, ações

### Modal
30. [ ] View `suggestion_detail_view` (GET HTMX)
31. [ ] Template partial com `param_diff` formatado
32. [ ] Testes: 200 existente, 404 inexistente

### Relatórios
33. [ ] Criar `services/report.py`
34. [ ] `generate_solver_report_md` com cabeçalho, vencedor, tabela comparativa
35. [ ] `generate_grade_md` com grade visual por turma
36. [ ] Testes: 2 funções com fixture pequena

### Drive
37. [ ] Criar `services/drive.py`
38. [ ] `get_or_create_folder` (com mock de GAPI)
39. [ ] `upload_md` (com mock)
40. [ ] Testes unitários com mock
41. [ ] Teste manual em dev: rodar solver, verificar Drive

### Robustez
42. [ ] Wrap upload em try/except
43. [ ] Adicionar `report_upload_status` em `SolverRun`
44. [ ] Migration pro campo novo
45. [ ] Testes: falha de upload não propaga

## 6. Critérios de aceite

- [ ] Model `Suggestion` criado e funcional
- [ ] `SuggestionsService` gera sugestões nas 4 categorias
- [ ] Cada categoria respeita limite de 5 sugestões (top por `delta`)
- [ ] Celery task `run_suggestions_layer` roda em ≤10 min, com timeout correto
- [ ] UI mostra painel de sugestões com badges, 3 botões funcionais (2 reais, 1 placeholder)
- [ ] Modal de detalhes funciona via HTMX
- [ ] Botão "Ignorar" muda status e remove da lista
- [ ] 2 relatórios `.md` são gerados e upados no Drive por execução
- [ ] Pastas `relatorios-solver/` e `grades-geradas/` são criadas automaticamente por tenant
- [ ] Falha no upload **não** quebra o pipeline
- [ ] `report_upload_status` reflete sucesso/falha
- [ ] Testes cobrem: model, service, task, views, drive, robustez

## 7. Riscos e pontos de atenção

- **Solver rápido pode divergir do solver real** — se `solve_rapido` produzir nº de buracos diferentes do `solve` original, sugestões podem ser enganosas. Considerar rodar o `solve` original 1x no início pra ter baseline, e o rápido pra simular mudanças
- **Tempo de execução** — 4 categorias × N params × 60s + overhead pode estourar 10 min. Limitar N (top 10 workitems, top 10 subjects, top 5 availabilities, top 5 rules) e medir
- **Race condition com `solver_run`** — se `solver_run` é editado enquanto sugestões rodam, pode dar inconsistência. Usar `select_for_update()` na carga
- **Drive API rate limit** — 1000 req/100s por usuário. 2 uploads por execução é tranquilo, mas se houver batch (reimportação) pode estourar. Implementar backoff exponencial
- **Conteúdo `.md` grande** — grade com 95 turmas pode gerar `.md` de megabytes. Considerar truncar ou comprimir
- **Token do Drive expirar** — `google_token.json` tem expiração. Implementar refresh automático (já existe no venv-gws, reusar)

## 8. Dependências

- Sprint 08 (solver 3 variantes) — `solver_run`, `run_3_variants`, `run_result_view` já existem
- Sprint 05 (scheduling) — `WorkloadItem`, `Subject`, `Teacher`, `TeacherAvailability`, `SubjectRule` já existem
- venv-gws com `google-api-python-client` — já instalado
- `google_token.json` com escopo `drive.file` — já configurado

## 9. Definição de pronto

A sprint pode ser considerada pronta quando:

- todos os 45 itens do checklist estiverem marcados;
- rodar solver em dev gera sugestões e elas aparecem na UI;
- 2 relatórios `.md` são criados no Drive após cada execução;
- falha simulada de upload não derruba o pipeline;
- nenhum teste flaky em CI.
