# Grade Certa — Sprint 04

> **Sprint:** 04  
> **Nome:** Pessoas  
> **Duração sugerida:** 2 semanas  
> **Objetivo macro:** modelar os professores e suas restrições para permitir alocação correta na grade.

## 1. Sprint Goal

Entregar o domínio de pessoas com professores, habilitações, disponibilidade, janelas e escopos de atuação.

## 1.1 Premissa transversal de autenticação

- o login do usuário é por e-mail;
- o projeto usa um `User` customizado baseado em `AbstractUser`;
- não usar o `django.contrib.auth.models.User` nativo.

## 2. Domínio coberto

- **Pessoas**

## 3. Escopo da sprint

- professor;
- habilitações;
- unidades permitidas;
- níveis permitidos;
- séries permitidas;
- disponibilidade por dia/horário;
- interpretação de ausência de disponibilidade como indisponibilidade;
- janelas como restrição flexível;
- auditoria nos modelos relevantes.

## 4. Entregáveis

- cadastro e edição de professores;
- restrições de atuação por unidade/nível/série;
- matriz de disponibilidade operante;
- validações e testes para conflitos de agenda;
- audit log aplicado aos modelos centrais.

## 5. Itens de backlog da sprint

1. Criar o app `people`.
2. Implementar professor e habilitações.
3. Modelar disponibilidade e janelas.
4. Criar validações para escopo de atuação.
5. Cobrir as regras com testes unitários.
6. Garantir auditoria nos pontos críticos.

## 6. Critérios de aceite

- um professor pode ser cadastrado com seus escopos de atuação;
- a disponibilidade por horário está explícita;
- horários não informados são tratados como indisponíveis;
- as janelas permanecem como restrição flexível, não como bloqueio absoluto;
- o domínio já sustenta a preparação para scheduling.

## 7. Riscos e atenção

- modelar disponibilidade de forma ambígua;
- não tratar exceções de agenda com clareza;
- espalhar regra de professor em múltiplos módulos.

## 8. Saída esperada para review

- base de pessoas pronta para ser consumida pelo scheduling.
