# Grade Certa — Sprint 07

> **Sprint:** 07
> **Nome:** Correção de Cadastros, Isolamento por Tenant e UX
> **Duração sugerida:** 2 semanas
> **Objetivo macro:** corrigir fluxos de criação, edição e exclusão com isolamento correto por tenant, melhorar UX dos formulários e ajustar a modelagem de unidades, períodos, séries, professores e disponibilidade.

## 1. Sprint Goal

Entregar uma versão estável do sistema de cadastros onde:
- o tenant é completamente isolado e inmanipulável pelo usuário final;
- formulários são visuais, consistentes e sem campos internos expostos;
- períodos e séries seguem herança de tenant com exceções por unidade;
- a disponibilidade de professor é editada como tabela semanal;
- exclusões usam HTMX com confirmação;
- auditlog está organizado nos modelos corretos.

## 2. Domínio coberto

- **Cadastros** — unidades, períodos, séries, turmas
- **Pessoas** — professores, habilitações, disponibilidade
- **Sistema** — autenticação, tenancy, auditoria

## 3. Escopo da sprint

### 3.1 Isolamento por Tenant (transversal)

- tenant nunca aparece em formulários;
- tenant vem sempre do usuário autenticado;
- querysets sempre filtrados por tenant;
- validações de ownership no backend, não apenas na UI.

### 3.2 Melhoria de Formulários (transversal)

- aplicar `django-widget-tweaks`;
- padronizar campos, labels, classes CSS, mensagens de erro;
- remover campos internos da interface.

### 3.3 Unidade

- adicionar campo `address` ao model;
- ocultar configurações padrão da UI;
- transformar fuso horário em select com fusos do Brasil;
- valor default: `America/Sao_Paulo`.

### 3.4 Períodos

- relacionamento com unidades através de ManyToMany;
- flag `is_tenant_default` para período global;
- criar períodos globais no nível do tenant;
- herança automática para unidades novas;
- vincular/desvincular períodos na página da unidade via HTMX.

### 3.5 Séries

- mesma modelagem de períodos (global vs por unidade);
- herança automática para unidades novas;
- vincular/desvincular séries na página da unidade via HTMX.

### 3.6 Turmas

- confirmar que são obrigatoriamente por unidade;
- validação de tenant no backend.

### 3.7 Professor

- corrigir semântica de carga semanal (exata, não mínima/máxima);
- atualizar labels, help text e documentação.

### 3.8 Disponibilidade do Professor

- redesign como tabela semanal visual;
- selecionar professor, mostrar grade de 7 dias;
- adicionar intervalos por dia;
- feedback visual claro.

### 3.9 Auditlog

- mover todos os `auditlog.register(...)` de `signals` para `models.py`;
- manter signals apenas para lógica que dependa de sinais.

### 3.10 Sidebar

- habilitar itens "Currículo" e "Ano Letivo" com rotas corretas.

### 3.11 Exclusões com HTMX

- confirmação antes de excluir;
- atualização parcial via HTMX, sem reload completo.

## 4. Entregáveis

1. Tenant blindado em todos os formulários e views.
2. Model de `Unit` com `address` e select de fuso horário.
3. Model de `Period` com ManyToMany e `is_tenant_default`.
4. Model de `Series` com ManyToMany e `is_tenant_default`.
5. Herança automática de períodos e séries para unidades novas.
6. Disponibilidade do professor como tabela semanal.
7. Carga semanal do professor com semântica corrigida.
8. Auditlog em models.py, fora de signals.
9. Sidebar com currículo e ano letivo habilitados.
10. Deletes com HTMX e confirmação.
11. Formulários com widget-tweaks e sem campos internos.

## 5. Itens de backlog da sprint

### Isolamento e formulários (transversais)
1. [ ] Remover campo tenant de todos os forms.
2. [ ] Adicionar filtro de tenant em todas as views.
3. [ ] Adicionar validação de ownership no backend.
4. [ ] Aplicar `django-widget-tweaks` nos forms principais.
5. [ ] Remover campos internos da UI.

### Unidade
6. [ ] Adicionar campo `address` no model `Unit`.
7. [ ] Incluir `address` nos forms e templates.
8. [ ] Trocar fuso horário para select com fusos do Brasil.
9. [ ] Ocultar configurações padrão da interface.

### Períodos
10. [ ] Alterar `ForeignKey` de `Period.unit` para `ManyToMany`.
11. [ ] Adicionar campo `is_tenant_default` em `Period`.
12. [ ] Implementar herança automática para unidades novas.
13. [ ] Permitir vincular/desvincular períodos na edição da unidade via HTMX.
14. [ ] Criar migrations de dados para converter registros existentes.

### Séries
15. [ ] Alterar `ForeignKey` de `Series.unit` para `ManyToMany`.
16. [ ] Adicionar campo `is_tenant_default` em `Series`.
17. [ ] Implementar herança automática para unidades novas.
18. [ ] Permitir vincular/desvincular séries na edição da unidade via HTMX.

### Turmas
19. [ ] Confirmar que `Class` continua com `ForeignKey` obrigatória para `Unit`.
20. [ ] Adicionar validação de tenant no backend.

### Professor
21. [ ] Corrigir label e help text de carga semanal.
22. [ ] Atualizar documentação/PRD com semântica exata.

### Disponibilidade
23. [ ] Redesenhar interface como tabela semanal.
24. [ ] Permitir adicionar intervalos por dia.
25. [ ] Garantir que professor sem disponibilidade = indisponível.

### Auditlog
26. [ ] Buscar todos os `auditlog.register` no projeto.
27. [ ] Mover registros para `models.py` dos modelos correspondentes.
28. [ ] Verificar que não há duplicidade ou erro de inicialização.

### Sidebar
29. [ ] Habilitar link "Currículo" na sidebar.
30. [ ] Habilitar link "Ano Letivo" na sidebar.

### HTMX Deletes
31. [ ] Implementar confirmação de exclusão com HTMX modal/alert.
32. [ ] Atualizar lista via HTMX após exclusão.
33. [ ] Garantir que exclusões respeitam tenant e permissões.

## 6. Critérios de aceite

- [ ] Formulários não expõem tenant.
- [ ] Querysets filtram por tenant do usuário autenticado.
- [ ] Validações de tenant existem no backend.
- [ ] Unidade tem `address` e select de fuso horário.
- [ ] Períodos globais do tenant são herdados por todas as unidades.
- [ ] Nova unidade herda períodos e séries globais existentes.
- [ ] Vincular/desvincular período/série de uma unidade não afeta outras.
- [ ] Carga semanal do professor é claramente "exata".
- [ ] Disponibilidade do professor é editada como tabela semanal.
- [ ] Auditlog está em `models.py`, não em `signals`.
- [ ] Sidebar mostra currículo e ano letivo.
- [ ] Deletes pedem confirmação e atualizam via HTMX.
- [ ] Testes manuais das telas cobertas pelas evidências passam.

## 7. Riscos e pontos de atenção

- **ManyToMany em período/série**: exige migração cuidadosa de dados existentes.
- **Herança automática**: deve evitar duplicidade quando unidades novas forem criadas.
- **HTMX + erros de validação**: formulários com erro devem re-renderizar corretamente.
- **Desvincular vs deletar**: ação em uma unidade não pode remover o registro global.
- **Validação de tenant no backend**: toda alteração em objetos de unidade precisa validar.

## 8. Dependências

- Sprint 01 (fundação de tenancy e acesso) — base de isolamento existente.
- Sprint 04 (pessoas) — modelos de professor e disponibilidade existentes.

## 9. Definição de pronto

A sprint pode ser considerada pronta quando:
- todos os itens do checklist acima estiverem marcados;
- testes manuais das telas cobertas pelas evidências forem repetidos com sucesso;
- tenant estiver completamente protegido contra seleção ou manipulação indevida;
- nenhuma página de formulário expõe campos internos do sistema.