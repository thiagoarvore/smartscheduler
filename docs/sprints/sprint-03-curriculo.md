# Grade Certa — Sprint 03

> **Sprint:** 03  
> **Nome:** Currículo  
> **Duração sugerida:** 2 semanas  
> **Objetivo macro:** consolidar o domínio curricular, que define disciplinas, cargas e regras de herança.

## 1. Sprint Goal

Entregar o domínio de currículo com disciplinas, códigos locais, matrizes curriculares, cargas horárias e regras de herança/exceção.

## 1.1 Premissa transversal de autenticação

- o login do usuário é por e-mail;
- o projeto usa um `User` customizado baseado em `AbstractUser`;
- não usar o `django.contrib.auth.models.User` nativo.

## 2. Domínio coberto

- **Currículo**

## 3. Escopo da sprint

- disciplina;
- código local da disciplina;
- matriz curricular;
- carga horária;
- herança de carga e disciplina entre estruturas;
- exceções locais;
- regras para composição do currículo por série/nível/período;
- auditoria nos modelos relevantes.

## 4. Entregáveis

- modelos do currículo persistidos;
- regras de herança implementadas e testadas;
- edição de cargas e exceções controlada;
- telas administrativas internas básicas;
- registros de auditoria para alterações relevantes.

## 5. Itens de backlog da sprint

1. Criar o app `curriculum`.
2. Implementar disciplina e código local.
3. Modelar matriz curricular e cargas.
4. Implementar herança e exceções locais.
5. Escrever testes para regras de composição e validação.
6. Registrar entidades auditáveis no `django-auditlog`.

## 6. Critérios de aceite

- disciplinas podem ser cadastradas sem violar as regras de unicidade definidas;
- cargas horárias podem herdar e ser ajustadas quando permitido;
- exceções locais ficam explícitas e testadas;
- o domínio suporta as bases para o scheduling sem retrabalho estrutural.

## 7. Riscos e atenção

- confundir regra de negócio com exceção operacional;
- deixar herança implícita demais;
- não preservar a rastreabilidade de mudanças curriculares.

## 8. Saída esperada para review

- currículo apto a alimentar disponibilidade e grade;
- regras de herança estabilizadas.
