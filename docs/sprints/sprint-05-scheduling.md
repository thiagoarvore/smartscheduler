# Grade Certa — Sprint 05

> **Sprint:** 05  
> **Nome:** Scheduling  
> **Duração sugerida:** 2 semanas  
> **Objetivo macro:** entregar o núcleo do produto: geração, validação e manutenção da grade.

## 1. Sprint Goal

Entregar o domínio de scheduling com slots, grade, aulas alocadas, conflitos e regras centrais de validação.

## 1.1 Premissa transversal de autenticação

- o login do usuário é por e-mail;
- o projeto usa um `User` customizado baseado em `AbstractUser`;
- não usar o `django.contrib.auth.models.User` nativo.

## 2. Domínio coberto

- **Scheduling**

## 3. Escopo da sprint

- grade de horários;
- slots;
- aulas alocadas;
- componentes de aula;
- conflitos de professor/turma/sala quando aplicável;
- regra de slot vazio inválido;
- dobradinha consecutiva no mesmo dia;
- regras de composição de aula e contagem para a turma;
- validações operacionais da grade.

## 4. Entregáveis

- criação e edição de grade;
- alocação de aulas;
- validações de conflito e consistência;
- testes unitários e de integração leve;
- interfaces básicas em Django + HTMX para operação interna.

## 5. Itens de backlog da sprint

1. Criar o app `scheduling`.
2. Implementar os modelos de grade e slot.
3. Criar a entidade de aula alocada e seus componentes.
4. Implementar validações de conflito.
5. Cobrir dobradinha, slots vazios e composição de aula com testes.
6. Expor fluxos operacionais com templates e HTMX.

## 6. Critérios de aceite

- a grade pode ser criada e modificada com persistência confiável;
- conflitos críticos são detectados;
- slots vazios não passam como grade pronta;
- a dobradinha consecutiva é validada corretamente;
- as regras de contagem de aula para a turma permanecem consistentes.

## 7. Riscos e atenção

- complexidade combinatória alta;
- regras de exceção mal testadas;
- dependências ocultas entre currículo, pessoas e scheduling;
- tentar resolver tudo com uma única modelagem rígida demais.

## 8. Saída esperada para review

- núcleo funcional da grade disponível para operação e validação.
