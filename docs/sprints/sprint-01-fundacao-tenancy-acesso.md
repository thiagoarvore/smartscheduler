# Grade Certa — Sprint 01

> **Sprint:** 01  
> **Nome:** Fundação técnica, tenancy e acesso base  
> **Duração sugerida:** 2 semanas  
> **Objetivo macro:** deixar o projeto executando com base técnica confiável e preparado para multi-tenancy e controle de acesso.

## 1. Sprint Goal

Entregar a fundação operacional do Grade Certa com Django, PostgreSQL, Docker, Poetry, Ruff e `django-tenants`, além do módulo inicial de acesso.

## 1.1 Imagens Docker base

- `python:3.13-alpine` como imagem base da aplicação;
- `postgres:18.1-trixie` como imagem do banco PostgreSQL;
- convenções de build e composição alinhadas ao padrão Thinkflow.

## 1.2 Premissa transversal de autenticação

- o login do usuário é por e-mail;
- o projeto usa um `User` customizado baseado em `AbstractUser`;
- não usar o `django.contrib.auth.models.User` nativo;
- o e-mail é o identificador de autenticação do backend.

## 2. Domínios cobertos

- **Tenancy / Governança**
- **Accounts / Acesso**

## 3. Escopo da sprint

### Tenancy

- configurar `django-tenants`;
- separar `SHARED_APPS` e `TENANT_APPS`;
- criar modelagem inicial de tenant e domínio;
- resolver tenant por domínio;
- preparar migrações para schema público e schemas de tenant.

### Acesso

- autenticação base;
- login por e-mail;
- `User` customizado com `AbstractUser`;
- papéis e permissões iniciais;
- vínculo de usuário com tenant/escopo;
- estrutura mínima de autorização por unidade e nível, ainda que simples.

### Fundação técnica

- Poetry como gerenciador;
- Ruff como verificador dev;
- Dockerfile e docker-compose;
- base do projeto Django;
- configuração de ambiente;
- pipeline inicial de testes.

## 4. Entregáveis

- projeto sobe localmente via Docker;
- banco PostgreSQL funcionando;
- tenant criado e resolvido por domínio;
- autenticação inicial operacional;
- estrutura base dos apps pronta;
- lint e testes básicos passando.

## 5. Itens de backlog da sprint

1. Estruturar o projeto base com a organização de apps.
2. Implementar a configuração de multi-tenancy.
3. Criar os modelos de tenant e domínio.
4. Configurar autenticação por e-mail, usuários e permissões mínimas.
5. Adotar Poetry e Ruff no fluxo de desenvolvimento.
6. Garantir que o ambiente Docker suba de forma reproduzível.

## 6. Critérios de aceite

- `docker compose up` sobe a stack sem intervenção manual extra.
- O tenant é identificado corretamente pelo host/domínio.
- Um usuário consegue autenticar por e-mail e ser associado ao escopo esperado.
- O `AUTH_USER_MODEL` customizado está configurado para o projeto.
- `ruff check` e a suíte inicial de testes executam sem erro.
- Não há segredos hardcoded no repositório.

## 7. Riscos e atenção

- erro na configuração do middleware de tenancy;
- mistura indevida entre dados compartilhados e dados do tenant;
- permissões iniciais insuficientes para as próximas sprints;
- assumir autenticação simples demais e depois ter que refatorar.

## 8. Saída esperada para review

- arquitetura base validada;
- decisão confirmada sobre apps compartilhados e tenant apps;
- caminho livre para iniciar a modelagem da estrutura escolar.
