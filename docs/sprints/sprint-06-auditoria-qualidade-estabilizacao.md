# Grade Certa — Sprint 06

> **Sprint:** 06  
> **Nome:** Auditoria, qualidade e estabilização  
> **Duração sugerida:** 2 semanas  
> **Objetivo macro:** fechar rastreabilidade, qualidade e robustez antes de qualquer expansão de escopo.

## 1. Sprint Goal

Entregar auditoria consistente nos domínios relevantes, reforço de qualidade e estabilização geral da aplicação para a primeira versão utilizável.

## 1.1 Premissa transversal de autenticação

- o login do usuário é por e-mail;
- o projeto usa um `User` customizado baseado em `AbstractUser`;
- não usar o `django.contrib.auth.models.User` nativo.

## 2. Domínios cobertos

- **Auditoria transversal**
- **Hardening / qualidade**
- **Estabilização operacional**

## 3. Escopo da sprint

- aplicação consistente de `django-auditlog` nos modelos relevantes;
- revisão de testes e correções de integração;
- observabilidade básica;
- ajustes de logs e mensagens;
- revisão de consistência entre domínios já entregues;
- preparação para uso interno/review;
- documentação operacional e de limitações.

## 4. Entregáveis

- auditoria aplicada nos modelos centrais;
- trilha mínima de rastreabilidade;
- testes de integração leves passando;
- aplicação estável o suficiente para ciclo interno de uso;
- documentação de operação e limites atualizada.

## 5. Itens de backlog da sprint

1. Garantir `django-auditlog` nos modelos prioritários.
2. Revisar mensagens, logs e pontos de observabilidade.
3. Corrigir falhas de integração e regressões conhecidas.
4. Consolidar a suíte de testes.
5. Validar consistência entre os módulos já entregues.
6. Preparar a base para review interno e evolução pós-MVP.

## 6. Critérios de aceite

- as alterações relevantes ficam auditadas;
- os testes relevantes executam sem erro;
- a aplicação está estável o suficiente para uso interno;
- o backlog restante está claramente separado do que é essencial para a primeira versão;
- importação de planilhas segue fora do MVP.

## 7. Riscos e atenção

- deixar auditoria faltar em algum modelo importante;
- acumular dívida técnica ao adiar hardening;
- validar pouco a consistência entre módulos;
- tentar trazer importação cedo demais para o ciclo principal.

## 8. Saída esperada para review

- versão interna utilizável;
- base pronta para evolução pós-MVP.
