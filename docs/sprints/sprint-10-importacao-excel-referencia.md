# Grade Certa — Sprint 10

> **Sprint:** 10
> **Nome:** Importação do Excel de Referência e Validação com Dados Reais
> **Duração sugerida:** 2 semanas
> **Objetivo macro:** implementar o comando de management `import_reference_timetable` (§22.3) que popula o banco a partir de `horario-fundamental-ii-referencia.xlsx`, permitindo validar o solver (Sprint 08) e a camada de sugestões (Sprint 09) com dados reais de 15 unidades e ~95 turmas.

## 1. Sprint Goal

Entregar uma versão onde:

- o comando `python manage.py import_reference_timetable <arquivo.xlsx>` popula o banco a partir do Excel de referência;
- o comando tem 3 estratégias (`create-only`, `upsert`, `replace`) e modo `--dry-run`;
- o comando roda em <30s pra planilha completa;
- validações falham rápido com mensagens claras;
- gera um `ImportRecord` auditable por execução;
- permite testar o solver com dados reais em CI/dev.

## 2. Domínio coberto

- **Scheduling** — comando de management, model `ImportRecord`
- **Sistema** — CLI, logging, auditlog
- **Integração** — leitura de `.xlsx` (openpyxl/pandas)

## 3. Escopo da sprint

### 3.1 Dependência: leitor de Excel

- [ ] Verificar se `openpyxl` está no `pyproject.toml`. Se não, adicionar
- [ ] Criar `apps/scheduling/services/excel_parser.py:ExcelTimetableParser`
- [ ] Classe recebe `path: Path` no construtor
- [ ] Método `parse() -> ParsedTimetable`:
  - Lê 8 abas esperadas: `Estrutura`, `Series`, `Turmas`, `Professores`, `Disciplinas`, `Matriz`, `Habilitações`, `Disponibilidade`
  - Retorna dataclass com 8 listas (1 por aba)
  - Erro: `ParserError` com mensagem clara ("Aba 'Matriz' não encontrada")
- [ ] Heurística de leitura: ver `docs/estudo-de-caso-planilha-horario-fundamental-ii.md` pra estrutura exata
- [ ] Testes: parse do `horario-fundamental-ii-referencia.xlsx` real (count de linhas bate)

### 3.2 Model `ImportRecord`

- [ ] Criar `apps/scheduling/models.py:ImportRecord` (§22.3.7):
  - `arquivo_origem` (CharField max 512)
  - `tenant` (FK Tenant)
  - `school_year` (FK SchoolYear)
  - `strategy` (choice: `create-only | upsert | replace`)
  - `started_at`, `finished_at` (DateTimeField)
  - `exit_code` (IntegerField)
  - `criados`, `atualizados`, `erros` (IntegerField)
  - `log_path` (CharField max 512)
  - `user` (FK User, nullable — pra import via UI futura)
  - BaseModel (id, criado_em, atualizado_em)
- [ ] Migration
- [ ] Testes: criação, choices, FKs

### 3.3 Service `TimetableImporter`

- [ ] Criar `apps/scheduling/services/importer.py:TimetableImporter`
- [ ] Construtor: `__init__(parsed: ParsedTimetable, tenant, school_year, strategy, logger)`
- [ ] Método `run() -> ImportSummary`:
  - Cria/atualiza registros conforme strategy
  - Conta criados, atualizados, erros
  - Retorna `ImportSummary` (dataclass com contadores + lista de erros)
- [ ] Estratégia `create-only`:
  - Itera sobre cada lista de `parsed`
  - `get_or_create` por chave natural (nome + Unit, código, etc)
  - Incrementa `criados` ou pula
- [ ] Estratégia `upsert`:
  - Itera e `update_or_create` por chave natural
  - Incrementa `criados` ou `atualizados`
- [ ] Estratégia `replace`:
  - Apaga tudo do `school_year` (exceto auditlog e ImportRecord)
  - Roda `create-only` em seguida
  - **Requer confirmação** (passada pelo command)
- [ ] Transação atômica: se der erro no meio, rollback total
- [ ] Testes: 1 teste por estratégia com SQLite em memória

### 3.4 Validações pré-apply

- [ ] Criar `apps/scheduling/services/validators.py:TimetableValidator`
- [ ] Recebe `parsed: ParsedTimetable`
- [ ] Método `validate() -> list[ValidationError]`:
  1. **Linhas obrigatórias**: todas as 8 abas presentes
  2. **Carga horária**: soma `WorkloadItem.weekly_hours` por turma ≤ 35h
  3. **Sem duplicatas**: (Teacher.name, Unit) e (Subject.code) únicos
  4. **Códigos gerados**: se Subject sem código, gera a partir do nome
  5. **FKs válidas**: toda referência a Unit/Series/Teacher/Subject tem que bater
- [ ] Retorna lista de erros (vazia = OK)
- [ ] Cada erro tem `field`, `value`, `message`, `severity` (error/warning)
- [ ] Testes: cada validação isolada com fixture que viola

### 3.5 Comando `import_reference_timetable`

- [ ] Criar `apps/scheduling/management/commands/import_reference_timetable.py`
- [ ] Argumentos:
  - `arquivo` (positional, required)
  - `--tenant` (string, default = tenant ativo)
  - `--school-year` (string, default = cria "reference-2022")
  - `--dry-run` (flag)
  - `--diff` (flag, requer `--dry-run` ou apply)
  - `--strategy` (choice, default `create-only`)
  - `--yes` (flag, pula confirmação em `replace`)
- [ ] Fluxo:
  1. Parse args
  2. Resolve `tenant` e `school_year` (cria se necessário)
  3. Parse Excel (`ExcelTimetableParser`)
  4. Roda validações (`TimetableValidator.validate()`)
  5. Se há erros: aborta com exit 1, imprime erros
  6. Se `--dry-run`: imprime resumo, retorna
  7. Se `--strategy=replace` e sem `--yes`: pede confirmação input
  8. Cria `ImportRecord` com `started_at=now()`, `exit_code=0` (vai pro try)
  9. Roda `TimetableImporter.run()` (try/except com rollback)
  10. Atualiza `ImportRecord` com `finished_at`, contadores
  11. Imprime resumo final
  12. Exit code 0 (sucesso) ou 1 (erro)
- [ ] Logging: `logs/import-{YYYYMMDD-HHMM}.log` com arquivo, tenant, school_year, strategy, contadores, duração
- [ ] Output formatado: ver §22.3.6 (exemplo pronto)
- [ ] Testes E2E: comando roda em SQLite, importa planilha de exemplo, conta confere

### 3.6 Modo `--dry-run` e `--diff`

- [ ] Com `--dry-run`: roda parse + validate, **não** chama `TimetableImporter.run()`
- [ ] Imprime resumo formatado com tabelas ASCII
- [ ] Com `--diff` adicional: imprime linha-a-linha o que seria criado/atualizado
- [ ] Modo `--diff` standalone (sem `--dry-run`): aplica mudanças E imprime diff simultaneamente
- [ ] Testes: `--dry-run` não toca banco, `--diff` mostra linhas esperadas

### 3.7 Estratégia `replace` com confirmação

- [ ] Quando `--strategy=replace`:
  - Imprime warning: "⚠️ ATENÇÃO: esta operação apaga TODOS os dados do SchoolYear X (exceto audit log)"
  - Lista o que será apagado (count de Unit, ClassGroup, etc)
  - Pede input: "Digite YES pra confirmar: "
  - Se input != "YES" (case-sensitive): aborta com exit 1
  - Com `--yes`: pula input
- [ ] Apaga em ordem: do mais dependente pro menos (LessonAssignment → ClassGroup → Unit)
- [ ] Desabilita signals de auditlog durante o delete (evita ruído)
- [ ] Testes: replace confirmado apaga tudo, replace sem confirmação aborta

### 3.8 Códigos de disciplina gerados

- [ ] Função `generate_subject_code(name: str) -> str`:
  - Remove acentos, remove stopwords (de, da, do, para, em)
  - Pega primeiras 3 letras de cada palavra
  - Uppercase
  - Ex: "Matemática" → "MAT", "Língua Portuguesa" → "LPO", "Ciências" → "CIE"
- [ ] Se código já existe (collision): apenda número ("MAT2")
- [ ] Testes: 10 nomes comuns, verifica códigos gerados

### 3.9 Suporte a abas com cabeçalho variável

- [ ] `ExcelTimetableParser` tolera variações de cabeçalho ("Turma" vs "Turmas" vs "class_group")
- [ ] Usa heurística: case-insensitive, sem acentos, ignora plural/singular
- [ ] Mapeamento conhecido em dict interno: `{"turma": "turmas", "professor": "professores", ...}`
- [ ] Testes: parse com cabeçalho "Turma" funciona, "turmas" também

### 3.10 Documentação da planilha de referência

- [ ] Atualizar `docs/estudo-de-caso-planilha-horario-fundamental-ii.md` com:
  - Mapeamento exato de cada aba (coluna A, B, C → model field X, Y, Z)
  - Exemplos de linhas
  - Limitações conhecidas (ex: "SubjectRule não é importável")
  - Como regerar a planilha se perder
- [ ] Testes: doc tem todos os campos mencionados

## 4. Entregáveis

1. Service `ExcelTimetableParser` lendo as 8 abas
2. Model `ImportRecord` com migration
3. Service `TimetableImporter` com 3 estratégias
4. Service `TimetableValidator` com 5 validações
5. Comando `import_reference_timetable` com 6 flags
6. Modo `--dry-run` e `--diff` funcionais
7. Geração de código automático pra Subject
8. Logs em `logs/import-{TS}.log`
9. Documentação atualizada da planilha
10. Suite de testes E2E

## 5. Itens de backlog da sprint

### Dependência
1. [ ] Verificar `openpyxl` no `pyproject.toml`
2. [ ] Adicionar se necessário

### Parser
3. [ ] Criar `ExcelTimetableParser` em `services/excel_parser.py`
4. [ ] Implementar leitura das 8 abas
5. [ ] Dataclass `ParsedTimetable` retornado
6. [ ] `ParserError` com mensagens claras
7. [ ] Testes: parse do `horario-fundamental-ii-referencia.xlsx` real
8. [ ] Testes: aba faltando levanta `ParserError`

### Model `ImportRecord`
9. [ ] Criar model com todos os campos
10. [ ] Migration
11. [ ] Testes: criação, choices

### Service
12. [ ] Criar `TimetableImporter` em `services/importer.py`
13. [ ] Estratégia `create-only` com `get_or_create`
14. [ ] Estratégia `upsert` com `update_or_create`
15. [ ] Estratégia `replace` com delete em ordem
16. [ ] Transação atômica com rollback
17. [ ] Testes: 1 teste por estratégia

### Validações
18. [ ] Criar `TimetableValidator` em `services/validators.py`
19. [ ] Validação de linhas obrigatórias
20. [ ] Validação de carga horária ≤35h
21. [ ] Validação de duplicatas
22. [ ] Geração de código de Subject
23. [ ] Validação de FKs
24. [ ] Retornar lista de `ValidationError`
25. [ ] Testes: 1 teste por validação

### Comando
26. [ ] Criar `import_reference_timetable.py` em `management/commands/`
27. [ ] Argumentos: `arquivo`, `--tenant`, `--school-year`, `--dry-run`, `--diff`, `--strategy`, `--yes`
28. [ ] Fluxo: parse → validate → aborta se erro → dry-run OU apply
29. [ ] Confirmação interativa em `replace`
30. [ ] Log em `logs/import-{TS}.log`
31. [ ] Output formatado com tabelas ASCII
32. [ ] Exit code 0/1 correto
33. [ ] Testes E2E com SQLite em memória

### Códigos de Subject
34. [ ] Função `generate_subject_code`
35. [ ] Collision handling
36. [ ] Testes: 10 nomes comuns

### Robustez do parser
37. [ ] Mapeamento de cabeçalhos variantes
38. [ ] Case-insensitive, sem acentos
39. [ ] Testes: "Turma" e "turmas" funcionam

### Documentação
40. [ ] Atualizar `estudo-de-caso-planilha-horario-fundamental-ii.md`
41. [ ] Mapeamento coluna → field
42. [ ] Limitações conhecidas
43. [ ] Como regerar a planilha

## 6. Critérios de aceite

- [ ] Comando roda com o `horario-fundamental-ii-referencia.xlsx` real
- [ ] Em <30s, importa as 8 abas com 0 erros
- [ ] Modo `--dry-run` lê e valida sem tocar banco
- [ ] Modo `--diff` mostra linha-a-linha o que seria criado
- [ ] Estratégia `create-only` é idempotente (rodar 2x não duplica)
- [ ] Estratégia `upsert` atualiza registros existentes
- [ ] Estratégia `replace` apaga tudo do SchoolYear e reimporta
- [ ] Validações falham rápido com mensagem clara
- [ ] Cada execução real gera `ImportRecord` com contadores
- [ ] Log em arquivo com todas as infos
- [ ] Códigos de Subject são gerados quando ausentes
- [ ] Parser tolera variações de cabeçalho
- [ ] Documentação da planilha está atualizada
- [ ] Testes E2E passam em CI

## 7. Riscos e pontos de atenção

- **Planilha pode mudar** — se o Thiago regerar, cabeçalhos podem mudar. Mitigação: mapeamento de cabeçalhos variantes + testes com a planilha real
- **`replace` pode apagar produção** — mitigação: confirmação obrigatória + dry-run sempre disponível
- **Performance** — 95 turmas × múltiplas tabelas pode ser lento. Mitigação: `bulk_create`/`bulk_update` quando possível
- **Transação gigante** — `replace` apaga e recria tudo numa transaction. Se der erro no meio, rollback completo (ok), mas pode demorar. Mitigação: logs intermediários
- **Códigos gerados podem colidir** — "MAT" pode existir 2x. Mitigação: collision handling com sufixo numérico
- **Multi-tenant** — o comando precisa rodar no schema do tenant certo. Mitigação: usar `connection.set_tenant(tenant)` explicitamente, padrão `django-tenants`
- **Importação de grandes volumes** — se a planilha tiver 500+ turmas no futuro, memória pode ser problema. Mitigação: processar em chunks via `iterator()` (não crítico pro MVP)
- **Auditlog** — pode gerar ruído durante `replace`. Mitigação: desabilitar signals durante delete

## 8. Dependências

- Sprint 05 (scheduling) — models `Unit`, `ClassGroup`, `Teacher`, `Subject`, etc já existem
- Sprint 07 (correção cadastros) — UI de tenant, formulários padronizados (relevante se quiser expor comando via UI no futuro)
- venv-gws com `openpyxl` (adicionar se faltar)
- Arquivo `docs/exemplos/horario-fundamental-ii-referencia.xlsx` (já existe)

## 9. Definição de pronto

A sprint pode ser considerada pronta quando:

- todos os 43 itens do checklist estiverem marcados;
- `python manage.py import_reference_timetable docs/exemplos/horario-fundamental-ii-referencia.xlsx` roda com sucesso em <30s e popula 15 unidades + ~95 turmas;
- rodar o solver (Sprint 08) sobre os dados importados gera uma grade válida;
- rodar a camada de sugestões (Sprint 09) gera sugestões coerentes;
- nenhum teste flaky em CI;
- a documentação da planilha reflete a estrutura real.
