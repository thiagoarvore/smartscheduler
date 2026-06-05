# Grade Certa — Planejamento Geral de Produção

> **Versão:** 0.2  
> **Papel:** Scrum Master / Planejamento de entrega  
> **Base:** PRD, SDD conceitual, SDD de arquitetura e regras de negócio consolidadas  
> **Stack-alvo:** Django, PostgreSQL, Docker, `django-base-kit`, `django-tenants`, `django-auditlog`, Poetry, Ruff, DTL + HTMX

## 1. Objetivo do planejamento

Organizar a produção do Grade Certa em sprints curtas, com entrega incremental por domínio, mantendo a arquitetura proposta e reduzindo risco de retrabalho.

O foco do MVP é **cadastro, validação e geração da grade**. Importação de planilhas fica para fase posterior.

## 2. Princípios de planejamento

- Entregar por domínio, não por camada técnica isolada.
- Garantir uma base técnica sólida antes das regras mais sensíveis.
- Validar cada domínio com testes antes de expandir o próximo.
- Manter a arquitetura Thinkflow: apps por bounded context, DDD lógico dentro de cada app.
- Registrar rastreabilidade e auditoria desde o início nos modelos relevantes.
- Priorizar o que desbloqueia o próximo domínio dependente.
- Manter o MVP enxuto: gerar a grade com confiabilidade antes de expandir para fluxos auxiliares.

## 3. Cadência sugerida

- **Duração da sprint:** 2 semanas
- **Ritual mínimo:**
  - Planejamento da sprint
  - Daily curta
  - Refinamento contínuo do backlog
  - Review
  - Retrospectiva
- **Critério de pronto (DoD):**
  - implementação concluída;
  - testes relevantes escritos e passando;
  - validação manual mínima executada;
  - documentação do que mudou atualizada;
  - sem segredos hardcoded;
  - lint/verificação dev aprovados (`ruff`).

## 4. Épicos macro

### Épico A — Fundação técnica e operabilidade

Inclui:

- Docker e Docker Compose;
- Poetry;
- Ruff;
- estrutura base do projeto;
- `django-base-kit`;
- configuração inicial do Django;
- pipeline de testes;
- base para multi-tenancy;
- observabilidade básica de desenvolvimento.

### Épico B — Tenancy e acesso

Inclui:

- `django-tenants`;
- schema público e schemas por tenant;
- autenticação;
- permissões;
- papéis;
- governança de acesso.

### Épico C — Estrutura escolar

Inclui:

- unidades;
- níveis;
- períodos;
- séries;
- turmas;
- regras de relação entre unidade, período, série e turma.

### Épico D — Currículo

Inclui:

- disciplinas;
- códigos locais;
- matrizes curriculares;
- cargas horárias;
- herança e exceções;
- regras de composição do currículo;
- vínculo entre currículo e série/nível/período.

### Épico E — Pessoas

Inclui:

- professores;
- habilitações;
- disponibilidade;
- janelas;
- restrições de unidade/nível/série;
- regras de atuação por contexto escolar.

### Épico F — Scheduling e geração da grade

Inclui:

- grade de horários;
- slots;
- alocação de aulas;
- conflitos;
- aula dupla;
- aula compartilhada, quando aplicável;
- regras de validação da grade;
- versionamento da grade gerada;
- tentativa/revisão de geração.

### Épico G — Auditoria, qualidade e estabilização

Inclui:

- auditoria com `django-auditlog` nos modelos de domínio;
- testes de integração;
- observabilidade mínima;
- hardening;
- estabilização pré-go-live;
- documentação operacional.

### Épico H — Futuro pós-MVP

Inclui itens que **não entram no MVP**:

- importação de planilhas;
- mapeamento assistido de dados;
- relatórios avançados de inconsistência;
- automações complementares de carga inicial.

## 5. Roadmap de sprints

### Sprint 1 — Fundação técnica + tenancy + acesso base

Entrega base para o restante do projeto.

### Sprint 2 — Estrutura escolar

Modelar a base estrutural do contexto escolar.

### Sprint 3 — Currículo

Fechar o coração das regras de disciplinas, cargas e herança.

### Sprint 4 — Pessoas

Modelar professores, habilitações e disponibilidade.

### Sprint 5 — Scheduling e geração da grade

Construir a grade, os slots, as validações centrais e o versionamento da geração.

### Sprint 6 — Auditoria, qualidade e estabilização

Fechar rastreabilidade, qualidade e robustez para a primeira versão utilizável.

## 6. Dependências entre domínios

- **Tenancy e acesso** precisam existir antes de tudo que dependa do tenant.
- **Estrutura escolar** depende de tenancy/acesso.
- **Currículo** depende de estrutura escolar.
- **Pessoas** depende da estrutura escolar e do currículo para regras de habilitação.
- **Scheduling** depende de estrutura escolar, currículo e pessoas.
- **Auditoria e qualidade** são transversais, mas devem ser aplicadas desde o início nos modelos relevantes.
- **Importação** fica fora do MVP e deve ser tratada somente depois que a geração da grade estiver consistente.

## 7. Entregáveis por sprint

Cada sprint deve terminar com:

- incremento funcional demonstrável;
- testes automatizados relevantes;
- documentação atualizada;
- backlog replanejado com base no aprendizado.

## 8. Riscos principais

- excesso de complexidade na modelagem de grade;
- dependências ocultas entre currículo e scheduling;
- retrabalho se tenancy não estiver bem resolvido cedo;
- tentar incluir importação antes da geração estar estável;
- tentar “fechar” visual cedo demais, desviando o foco do domínio.

## 9. Arquivos de sprint

- `docs/sprints/sprint-01-fundacao-tenancy-acesso.md`
- `docs/sprints/sprint-02-estrutura-escolar.md`
- `docs/sprints/sprint-03-curriculo.md`
- `docs/sprints/sprint-04-pessoas.md`
- `docs/sprints/sprint-05-scheduling.md`
- `docs/sprints/sprint-06-auditoria-qualidade-estabilizacao.md`

## 10. Observação de gestão

A prioridade é sempre manter o projeto produzindo incremento útil. Se uma sprint terminar com menos escopo, o próximo planejamento deve reequilibrar o backlog sem quebrar a sequência dos domínios.
