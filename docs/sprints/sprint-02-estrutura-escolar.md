# Grade Certa — Sprint 02

> **Sprint:** 02  
> **Nome:** Estrutura escolar  
> **Duração sugerida:** 2 semanas  
> **Objetivo macro:** modelar a base organizacional da escola que será usada por currículo, pessoas e scheduling.

## 1. Sprint Goal

Entregar o domínio de estrutura escolar com unidades, níveis, períodos, séries e turmas, com regras básicas testadas.

## 1.1 Premissa transversal de autenticação

- o login do usuário é por e-mail;
- o projeto usa um `User` customizado baseado em `AbstractUser`;
- não usar o `django.contrib.auth.models.User` nativo.

## 2. Domínio coberto

- **Estrutura escolar**

## 3. Escopo da sprint

- cadastro e edição de unidades;
- níveis de ensino;
- períodos escolares;
- séries;
- turmas;
- relações entre unidade, nível, período, série e turma;
- validações estruturais iniciais;
- auditoria nos modelos relevantes.

## 4. Entregáveis

- app de estrutura escolar criado e organizado no padrão do projeto;
- modelos persistidos com migrações;
- views/forms/templates básicos;
- testes de modelo e validação;
- auditoria aplicada aos modelos centrais.

## 5. Itens de backlog da sprint

1. Criar o app `schools`.
2. Implementar os modelos centrais do domínio.
3. Definir relacionamentos e restrições principais.
4. Expor CRUD mínimo para operação interna.
5. Aplicar `django-auditlog` aos modelos centrais.
6. Cobrir regras com testes unitários.

## 6. Critérios de aceite

- uma unidade pode ser criada e usada como base para outras entidades;
- a estrutura de níveis, períodos, séries e turmas está consistente;
- os testes passam para regras centrais;
- a auditoria registra alterações em entidades críticas;
- a modelagem não cria dependências desnecessárias com currículo ou scheduling.

## 7. Riscos e atenção

- modelar a estrutura escolar com pouca flexibilidade;
- acoplar demais aos casos de currículo antes da hora;
- criar hierarquias rígidas que dificultem exceções futuras.

## 8. Saída esperada para review

- domínio escolar consolidado como base para currículo;
- dependências de estrutura prontas para os próximos módulos.
