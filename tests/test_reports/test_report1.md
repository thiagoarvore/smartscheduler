# Relatorio de Ajustes - Fluxos de Cadastro e Edicao

Este documento consolida os problemas encontrados nos testes manuais e transforma as observacoes em um briefing de implementacao para outro agente de IA assumir as mudancas.

## Objetivo

Corrigir os fluxos de criacao, edicao e exclusao para respeitar isolamento por tenant, melhorar UX dos formularios e ajustar a modelagem de unidades, periodos, series, professores e disponibilidade.

## Evidencias Visuais

| Evidencia | Arquivo | O que demonstra |
| --- | --- | --- |
| Tenant selecionavel no formulario | [escolher_tenant.png](../testing_evidences/escolher_tenant.png) | O usuario consegue escolher tenant manualmente, o que nao deve existir. |
| Criacao de periodo | [create_period.png](../testing_evidences/create_period.png) | Periodo esta preso a unidade de forma obrigatoria e precisa seguir heranca por tenant. |
| Carga semanal do professor | [carga_prof.png](../testing_evidences/carga_prof.png) | Campo deve representar carga semanal exata, nao carga minima ou maxima. |
| Disponibilidade do professor | [avaiablility.png](../testing_evidences/avaiablility.png) | Interface atual esta pouco visual e precisa virar tabela semanal. |

## Regra Central de Tenant

O tenant nunca deve ser escolhido pelo usuario em formularios de criacao ou edicao.

Regras obrigatorias:

- O tenant deve sempre vir do usuario autenticado.
- Formularios nao devem renderizar campo de tenant.
- Views nao devem aceitar tenant vindo do `POST`.
- Querysets devem ser filtrados pelo tenant do usuario.
- Objetos de outro tenant nao podem ser visualizados, editados, vinculados ou excluidos.
- Validacoes de ownership devem existir tambem no backend, nao apenas na UI.

## Melhorias Gerais de Formularios

- Usar `django-widget-tweaks` para melhorar a renderizacao visual dos formularios.
- Padronizar campos, labels, classes CSS, mensagens de erro e estado de campos obrigatorios.
- Remover campos internos ou tecnicos da interface quando eles nao forem relevantes para o usuario final.

## Unidade

### Problemas

- O campo de configuracoes padrao aparece para o usuario, mas deve ser interno do sistema.
- Falta campo de endereco no cadastro de unidade.
- Fuso horario esta como texto livre.

### Mudancas Necessarias

- Adicionar campo `address` no model de `Unit`.
- Incluir `address` nos forms e templates de criacao/edicao de unidade.
- Remover o campo de configuracoes padrao da interface do usuario, mantendo-o no codigo se for necessario para uso interno.
- Transformar fuso horario em `select`.
- Preencher o fuso horario padrao com Sao Paulo.
- Limitar as opcoes de fuso horario aos fusos do Brasil.

### Criterios de Aceite

- Usuario consegue cadastrar unidade com endereco.
- Usuario nao ve nem edita configuracoes internas.
- Campo de fuso horario inicia com `America/Sao_Paulo`.
- Campo de fuso horario nao permite texto livre.

## Periodos

### Regra de Negocio Esperada

Periodos podem existir no nivel do tenant ou no nivel de uma unidade especifica.

- Periodo do tenant deve ser herdado por todas as unidades.
- Periodo especifico de uma unidade deve valer apenas para aquela unidade.
- Uma unidade criada depois de periodos globais do tenant deve herdar esses periodos automaticamente.
- Remover um periodo de uma unidade nao pode remover esse periodo de outras unidades nem do tenant.

### Mudancas Necessarias

- O relacionamento `unit` em `Period` nao deve ser `ForeignKey` obrigatoria.
- Substituir a relacao por `ManyToMany` com unidades, ou modelagem equivalente que permita heranca por tenant e excecoes por unidade.
- Criar uma flag para identificar periodo global do tenant, por exemplo `is_tenant_default`.
- Permitir criar periodos globais no tenant.
- Permitir criar, vincular e remover periodos por unidade na pagina de edicao da propria unidade.
- Implementar a interacao de periodos por unidade com HTMX.

### Criterios de Aceite

- Criar periodo global nao exige escolher unidade.
- Todas as unidades do tenant recebem periodos globais.
- Nova unidade herda periodos globais ja existentes.
- Edicao da unidade permite adicionar periodo local via HTMX.
- Edicao da unidade permite remover periodo apenas daquela unidade via HTMX.
- Alteracoes em uma unidade nao impactam outras unidades indevidamente.

## Series

### Regra de Negocio Esperada

Series seguem a mesma logica de heranca dos periodos.

- Serie global do tenant deve ser herdada por todas as unidades.
- Serie especifica de unidade deve valer apenas para aquela unidade.
- Criacao e remocao por unidade devem acontecer na pagina de edicao da unidade.
- Remover uma serie de uma unidade nao pode remover essa serie de outras unidades nem do tenant.

### Mudancas Necessarias

- Revisar modelagem de series para permitir nivel tenant e nivel unidade.
- Implementar heranca automatica para unidades novas.
- Implementar criacao e remocao por unidade com HTMX na pagina de edicao da unidade.

### Criterios de Aceite

- Criar serie global nao exige escolher unidade.
- Todas as unidades do tenant recebem series globais.
- Nova unidade herda series globais ja existentes.
- Edicao da unidade permite adicionar e remover series locais sem recarregar a pagina.

## Turmas

Turmas continuam sendo por unidade.

### Criterios de Aceite

- Toda turma deve estar vinculada a uma unidade.
- A unidade escolhida ou disponivel para vinculo deve pertencer ao tenant do usuario.
- Nao deve ser possivel criar turma para unidade de outro tenant.

## Professores

### Problema

O campo de carga semanal esta com semantica incorreta.

### Mudancas Necessarias

- Ajustar label, help text e documentacao do campo para representar carga semanal exata.
- Nao tratar o campo como carga minima ou maxima.
- Atualizar o PRD para registrar que a carga semanal pode ser usada como sugestao quando nao houver grade possivel.

### Sugestoes Esperadas do Sistema

Quando nao houver grade viavel, o sistema pode sugerir ajustes como:

- Aumentar em 1 ou 2 aulas a carga semanal de um professor especifico.
- Diminuir em 1 aula a carga semanal de um professor especifico.
- Indicar quais professores e quais restricoes estao bloqueando a geracao da grade.

### Criterios de Aceite

- Interface deixa claro que a carga semanal e exata.
- PRD documenta a carga semanal como possivel fonte de sugestoes do sistema.

## Disponibilidade do Professor

### Problema

A UX atual de cadastro de disponibilidade esta pouco visual e dificil de usar.

### Mudancas Necessarias

- Usuario deve selecionar o professor.
- Depois da selecao, a tela deve mostrar uma tabela com os sete dias da semana.
- A tabela deve permitir inserir intervalos de disponibilidade.
- A interface deve ser mais visual, preferencialmente com interacoes dinamicas e feedback claro.

### Criterios de Aceite

- Disponibilidade e gerenciada em formato de grade semanal.
- Usuario consegue adicionar intervalos por dia da semana.
- Usuario consegue visualizar rapidamente os dias e horarios disponiveis do professor.
- Interface substitui o fluxo atual mostrado na evidencia.

## Auditlog

### Problema

Registros como `auditlog.register(Tenant)` e `auditlog.register(Domain)` nao devem ficar em `signals`.

### Mudancas Necessarias

- Revisar o projeto inteiro em busca de chamadas `auditlog.register(...)`.
- Mover os registros para o `models.py` correspondente a cada model.
- Manter `signals` apenas para logica de eventos que realmente dependa de sinais.

### Criterios de Aceite

- Nenhum `auditlog.register(...)` fica em arquivos de signals.
- Cada model auditado e registrado no arquivo de model apropriado.
- Projeto continua inicializando sem duplicidade ou erro de registro de auditlog.

## Sidebar

### Mudancas Necessarias

- Habilitar os itens que ainda faltam na sidebar:
  - Curriculo
  - Ano letivo

### Criterios de Aceite

- Links aparecem na sidebar.
- Links apontam para as rotas corretas.
- Visibilidade respeita permissao e tenant quando aplicavel.

## Exclusoes com HTMX

### Mudancas Necessarias

- Fluxos de delete devem usar HTMX.
- Usuario deve receber alerta/confirmacao antes de excluir.
- Excluir nao deve causar recarregamento completo da pagina quando for possivel atualizar apenas o trecho afetado.

### Criterios de Aceite

- Delete apresenta confirmacao antes de executar.
- Delete atualiza a lista ou componente afetado via HTMX.
- A pagina nao recarrega totalmente em fluxos que podem ser parciais.
- Exclusoes respeitam tenant e permissoes.

## Checklist de Implementacao

- [ ] Remover selecao manual de tenant dos formularios.
- [ ] Garantir filtros e validacoes por tenant em views, forms e querysets.
- [ ] Aplicar `django-widget-tweaks` nos formularios principais.
- [ ] Adicionar `address` em `Unit`.
- [ ] Ocultar configuracoes internas de unidade da UI.
- [ ] Trocar fuso horario de unidade para select com fusos do Brasil.
- [ ] Modelar periodos globais por tenant e especificos por unidade.
- [ ] Implementar heranca de periodos para unidades novas.
- [ ] Gerenciar periodos na pagina de edicao da unidade com HTMX.
- [ ] Modelar series globais por tenant e especificas por unidade.
- [ ] Implementar heranca de series para unidades novas.
- [ ] Gerenciar series na pagina de edicao da unidade com HTMX.
- [ ] Confirmar que turmas continuam obrigatoriamente por unidade.
- [ ] Corrigir semantica de carga semanal do professor.
- [ ] Atualizar PRD com sugestoes baseadas em carga semanal.
- [ ] Redesenhar disponibilidade do professor como tabela semanal.
- [ ] Mover registros de auditlog para `models.py`.
- [ ] Habilitar curriculo e ano letivo na sidebar.
- [ ] Implementar deletes com HTMX e confirmacao.

## Riscos e Pontos de Atencao

- Mudancas de `ForeignKey` para `ManyToMany` exigem migracoes cuidadosas e possivel migracao de dados existentes.
- Heranca de periodos e series precisa evitar duplicidade quando unidades novas forem criadas.
- Remocoes por unidade devem desvincular, nao deletar o registro global.
- Todas as alteracoes em objetos relacionados a unidade precisam validar tenant no backend.
- A UX com HTMX deve funcionar tambem quando houver erro de validacao.

## Definicao de Pronto

Esta demanda pode ser considerada pronta quando:

- O tenant estiver completamente protegido contra selecao ou manipulacao indevida.
- Formularios principais estiverem visualmente melhores e sem campos internos desnecessarios.
- Unidade, periodos, series, turmas, professores e disponibilidade seguirem as regras acima.
- Sidebar e deletes estiverem ajustados.
- Auditlog estiver organizado nos arquivos de models.
- Testes manuais das telas cobertas pelas evidencias forem repetidos com sucesso.
