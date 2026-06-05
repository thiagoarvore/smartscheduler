# Sistema de Grade Horária Escolar — Regras de Negócio

> Documento inicial de concepção do produto.
>
> **Status:** rascunho de regras de negócio  
> **Versão:** 0.3  
> **Caso-chave:** Colégio Objetivo — 13 unidades próprias em São Paulo  
> **Objetivo do sistema:** gerar grades horárias próximas do ideal para escolas complexas, apontando conflitos, restrições não atendidas e o que falta para tornar a grade viável.

---

## 1. Visão do Produto

O sistema deve apoiar escolas na criação de grades horárias complexas, considerando múltiplas unidades, níveis de ensino, turmas, professores, disciplinas, espaços físicos, restrições pedagógicas, disponibilidade de profissionais e regras operacionais.

A dor principal é que a construção manual da grade se torna caótica quando:

- a escola tem muitas unidades;
- professores lecionam em mais de uma unidade;
- professores lecionam para mais de um nível de ensino;
- professores podem lecionar mais de uma disciplina;
- professores possuem disponibilidade restrita;
- disciplinas dependem de espaços específicos, como laboratórios;
- algumas disciplinas podem ou não dividir horário com outras;
- há necessidade de equilibrar qualidade pedagógica, logística e viabilidade operacional.

O sistema não deve apenas tentar montar uma grade. Ele deve também explicar:

- quais restrições foram atendidas;
- quais restrições foram violadas;
- por que uma grade ideal não foi possível;
- quais dados, decisões ou flexibilizações seriam necessários para tornar a grade possível.

---

## 2. Modelo Comercial e Multi-tenant

A ideia é vender o sistema para várias escolas ou grupos educacionais.

Por isso, o sistema deve ser **multi-tenant**.

### 2.1 Tenant

Cada cliente/escola/grupo educacional deve ter seu próprio tenant.

Exemplos:

- Objetivo São Paulo;
- uma rede menor com 3 unidades;
- uma escola única;
- um grupo educacional com várias marcas.

### 2.2 Isolamento de dados

Cada tenant deve ter dados isolados dos demais.

Um usuário de uma escola não pode ver:

- professores de outra escola;
- turmas de outra escola;
- grades de outra escola;
- unidades de outro tenant;
- regras específicas de outro cliente.

### 2.3 Usuários por tenant

Cada tenant deve poder criar mais de um usuário.

Possíveis perfis iniciais:

- **Administrador do tenant:** configura escola, unidades, usuários e regras gerais;
- **Coordenador pedagógico:** cadastra turmas, disciplinas, cargas horárias e restrições pedagógicas;
- **Secretaria/operacional:** cadastra disponibilidade, salas, unidades e dados auxiliares;
- **Visualizador:** consulta grades, relatórios e conflitos, sem editar;
- **Superadmin da plataforma:** equipe dona do produto, com acesso administrativo controlado.

### 2.4 Unidades dentro do tenant

Um tenant pode ter uma ou várias unidades.

No caso-chave do Objetivo:

- tenant: Objetivo;
- unidades: 13 unidades próprias em São Paulo;
- professores podem circular entre unidades;
- a grade precisa considerar deslocamento, disponibilidade e conflito entre unidades.

---

## 3. Entidades Principais do Domínio

### 3.1 Tenant

Representa a organização cliente.

Campos possíveis:

- nome;
- CNPJ ou identificador administrativo;
- status da assinatura;
- plano contratado;
- timezone padrão;
- ano letivo ativo;
- configurações gerais.

### 3.2 Unidade Escolar

Representa uma escola física ou campus dentro do tenant.

Campos possíveis:

- nome da unidade;
- endereço;
- cidade;
- bairro;
- tempo mínimo de deslocamento entre outras unidades;
- níveis atendidos;
- horários de funcionamento;
- salas e espaços disponíveis.

Regras:

- uma unidade pertence a um tenant;
- uma unidade pode ter vários níveis de ensino;
- uma unidade pode ter várias turmas;
- uma unidade pode compartilhar professores com outras unidades.

### 3.3 Ano Letivo / Período de Planejamento

A grade deve ser criada dentro de um período.

Exemplos:

- ano letivo 2026;
- primeiro semestre de 2026;
- segundo semestre de 2026;
- ciclo bimestral/trimestral, se a escola trabalhar assim.

Campos possíveis:

- ano;
- data de início;
- data de fim;
- quantidade de semanas;
- calendário de feriados;
- dias letivos;
- eventos fixos da escola.

### 3.4 Nível de Ensino

Exemplos:

- Educação Infantil;
- Ensino Fundamental I;
- Ensino Fundamental II;
- Ensino Médio;
- Pré-vestibular, se aplicável.

Regras:

- cada turma pertence a um nível;
- disciplinas podem ter regras diferentes por nível;
- professores podem ou não estar habilitados para determinados níveis.

### 3.5 Série / Ano Escolar

Exemplos:

- Infantil 4;
- 1º ano do Fundamental;
- 9º ano do Fundamental;
- 1ª série do Ensino Médio;
- 3ª série do Ensino Médio.

Regras:

- cada série pertence a um nível;
- cada série possui uma matriz curricular;
- a matriz define disciplinas e carga horária obrigatória.

### 3.6 Turma

Representa um grupo de alunos.

Exemplos:

- 6º ano A;
- 6º ano B;
- 1ª série EM C.

Campos possíveis:

- nome/código;
- unidade;
- nível;
- série;
- turno;
- quantidade de alunos;
- sala preferencial;
- grade curricular associada.

Regras:

- uma turma não pode ter duas aulas obrigatórias no mesmo horário;
- uma turma pode ter horários bloqueados;
- uma turma pode ter preferências pedagógicas, como não ter muitas aulas pesadas seguidas.

### 3.7 Disciplina

Representa uma área ou componente curricular.

Exemplos:

- Matemática;
- História;
- Física;
- Química;
- Biologia;
- Inglês;
- Educação Física;
- Laboratório de Ciências;
- Redação.

Campos possíveis:

- nome;
- área;
- nível/séries aplicáveis;
- carga horária semanal;
- duração padrão da aula;
- necessidade de espaço específico;
- possibilidade de aula dupla;
- possibilidade de dividir horário com outra disciplina;
- prioridade pedagógica.

### 3.8 Matriz Curricular

Define quais disciplinas cada série/turma precisa ter e com qual carga horária.

Exemplo:

- 6º ano Fundamental II:
  - Matemática: 5 aulas semanais;
  - Português: 5 aulas semanais;
  - História: 2 aulas semanais;
  - Geografia: 2 aulas semanais;
  - Ciências: 3 aulas semanais.

Regras:

- cada série deve ter uma matriz curricular;
- a matriz pode variar por tenant, unidade ou ano letivo;
- a matriz é uma das entradas mais importantes do algoritmo.

### 3.9 Professor

Representa o profissional docente.

Campos possíveis:

- nome;
- e-mail;
- telefone;
- vínculo empregatício;
- carga horária contratada;
- carga horária máxima semanal;
- disciplinas que pode lecionar;
- níveis/séries que pode lecionar;
- unidades em que pode atuar;
- disponibilidade por dia/horário;
- preferências;
- restrições fortes;
- restrições flexíveis.

Regras:

- um professor não pode estar em duas aulas no mesmo horário;
- um professor pode lecionar em mais de uma unidade;
- um professor pode lecionar mais de uma disciplina;
- um professor pode lecionar em mais de um nível de ensino;
- um professor pode ter disponibilidade restrita;
- um professor pode ter limite diário e semanal de aulas;
- deslocamentos entre unidades devem ser considerados.

### 3.10 Espaço Físico

Representa sala, laboratório, quadra ou outro ambiente.

Exemplos:

- Sala 101;
- Laboratório de Química;
- Laboratório de Informática;
- Quadra;
- Auditório.

Campos possíveis:

- nome;
- unidade;
- tipo;
- capacidade;
- recursos disponíveis;
- disciplinas compatíveis;
- horários bloqueados;
- prioridade de uso.

Regras:

- algumas disciplinas exigem espaço específico;
- um espaço não pode receber duas turmas no mesmo horário, salvo se permitido;
- a capacidade do espaço deve comportar a turma;
- alguns espaços podem ser compartilhados em casos específicos.

### 3.11 Horário / Slot

Representa um bloco de tempo em que uma aula pode acontecer.

Campos possíveis:

- dia da semana;
- horário de início;
- horário de fim;
- turno;
- ordem da aula no dia;
- unidade;
- se é intervalo ou aula;
- se aceita aula dupla.

Exemplo:

- Segunda-feira, 07:30–08:20;
- Segunda-feira, 08:20–09:10;
- intervalo;
- Segunda-feira, 09:30–10:20.

### 3.12 Aula Alocada

Representa uma decisão de grade.

Campos possíveis:

- turma;
- disciplina;
- professor;
- espaço;
- dia;
- horário;
- unidade;
- status: fixa, sugerida, validada, com conflito;
- justificativa da escolha.

---

## 4. Tipos de Restrições

O sistema deve diferenciar restrições rígidas e restrições flexíveis.

### 4.1 Restrições rígidas

São regras que não podem ser violadas.

Se forem violadas, a grade é inválida.

Exemplos:

- professor não pode estar em duas unidades no mesmo horário;
- professor não pode estar em duas turmas ao mesmo tempo;
- turma não pode ter duas disciplinas obrigatórias no mesmo horário;
- laboratório não pode receber duas turmas simultaneamente;
- disciplina que exige laboratório não pode ser alocada em sala comum;
- professor não pode ser alocado fora de sua disponibilidade absoluta;
- turma precisa cumprir a carga horária mínima obrigatória;
- aula não pode acontecer em horário bloqueado pela escola.

### 4.2 Restrições flexíveis

São preferências ou objetivos de qualidade.

Podem ser violadas, mas geram penalidade.

Exemplos:

- evitar professor com muitas janelas;
- evitar turma com muitas aulas da mesma disciplina no mesmo dia;
- evitar aulas pesadas no final do dia;
- preferir que professores concentrem aulas na mesma unidade no mesmo dia;
- preferir que aulas de laboratório fiquem próximas de aulas teóricas;
- preferir distribuição equilibrada das disciplinas ao longo da semana;
- evitar primeira ou última aula para certas disciplinas;
- respeitar preferências do professor quando possível.

### 4.3 Peso das restrições

Cada tenant pode configurar pesos para restrições flexíveis.

Exemplo:

- minimizar janelas de professores: peso alto;
- evitar aulas de Matemática no último horário: peso médio;
- manter professor na mesma unidade no dia: peso alto;
- evitar aula dupla: peso baixo.

---

## 5. Regras de Professores

### 5.1 Disponibilidade

Cada professor deve ter disponibilidade cadastrada por dia e horário.

A disponibilidade pode ser:

- disponível;
- indisponível;
- preferencial;
- disponível apenas se necessário;
- bloqueado por compromisso fixo.

### 5.2 Habilitação

O sistema deve saber quais disciplinas, níveis e séries cada professor pode lecionar.

Exemplo:

- Professor João:
  - Matemática para Fundamental II;
  - Física para Ensino Médio;
  - não leciona Educação Infantil.

### 5.3 Carga horária

O sistema deve controlar:

- carga horária contratada;
- carga horária mínima desejada;
- carga horária máxima permitida;
- carga horária por unidade;
- carga horária por nível de ensino;
- quantidade máxima de aulas por dia.

### 5.4 Janelas

Janela é um intervalo vazio entre aulas do professor no mesmo dia.

Regras possíveis:

- evitar janelas;
- limitar número máximo de janelas por semana;
- permitir janelas apenas se necessário;
- diferenciar janela curta de janela longa.

### 5.5 Deslocamento entre unidades

Como o caso-chave envolve 13 unidades em São Paulo, deslocamento é uma regra central.

O sistema deve armazenar tempos mínimos de deslocamento entre unidades.

Regras:

- professor não pode ser alocado em unidades diferentes em horários consecutivos se não houver tempo mínimo de deslocamento;
- o deslocamento pode variar por turno ou por tabela fixa;
- em uma primeira versão, pode-se usar matriz manual de tempos entre unidades;
- em versões futuras, pode-se integrar mapas/tempo real.

### 5.6 Preferências do professor

Exemplos:

- prefere manhã;
- prefere tarde;
- prefere concentrar aulas em poucos dias;
- prefere não dar primeira aula;
- prefere não se deslocar entre unidades no mesmo dia.

Preferências devem ser flexíveis, não garantidas.

---

## 6. Regras de Disciplinas

### 6.1 Carga semanal

Cada disciplina deve ter uma carga semanal por turma/série.

Exemplo:

- História: 2 aulas por semana;
- Matemática: 5 aulas por semana.

### 6.2 Distribuição semanal

Algumas disciplinas devem ser distribuídas ao longo da semana.

Exemplos:

- 5 aulas de Matemática não devem ficar todas em dois dias;
- 2 aulas de História podem ocorrer em dias diferentes;
- Redação pode preferir aula dupla.

### 6.3 Aula dupla

Algumas disciplinas podem ou devem ocorrer em blocos duplos.

Exemplos:

- Laboratório de Química: preferencialmente aula dupla;
- Redação: pode ser aula dupla;
- Educação Física: pode exigir aula dupla dependendo da escola.

### 6.4 Espaço obrigatório

Algumas disciplinas exigem espaço específico.

Exemplos:

- Química prática → laboratório de química;
- Informática → laboratório de informática;
- Educação Física → quadra;
- Arte → sala específica, se houver.

### 6.5 Compatibilidade entre disciplinas

Algumas disciplinas podem dividir o mesmo horário ou espaço em casos especiais.

Exemplos possíveis:

- uma turma dividida entre Laboratório A e Laboratório B;
- metade da turma em laboratório e metade em outra atividade;
- disciplinas eletivas simultâneas;
- itinerários formativos no Ensino Médio.

Essa regra precisa ser modelada com cuidado, porque pode significar:

- duas disciplinas no mesmo slot para grupos diferentes da mesma turma;
- divisão da turma em subgrupos;
- aulas paralelas opcionais;
- rodízio entre grupos.

---

## 7. Regras de Turmas

### 7.1 Conflito de turma

Uma turma não pode ter duas aulas obrigatórias no mesmo horário, exceto quando houver regra explícita de divisão de turma, eletivas ou subgrupos.

### 7.2 Carga diária

A turma deve respeitar:

- quantidade máxima de aulas por dia;
- horários de entrada e saída;
- intervalos obrigatórios;
- turno da turma.

### 7.3 Equilíbrio pedagógico

Preferências possíveis:

- evitar muitas disciplinas de alta carga cognitiva no mesmo dia;
- evitar concentração de uma mesma disciplina;
- evitar todos os laboratórios na mesma semana/dia;
- distribuir avaliações ou atividades especiais, futuramente.

### 7.4 Horários fixos

Algumas turmas podem ter horários fixos, como:

- reunião de orientação;
- projeto interdisciplinar;
- aula de vida/projeto de vida;
- atividade esportiva;
- evento recorrente.

---

## 8. Regras de Espaços

### 8.1 Capacidade

O espaço precisa comportar a turma.

### 8.2 Tipo de espaço

Cada disciplina pode exigir ou preferir tipos de espaço.

Tipos iniciais:

- sala comum;
- laboratório de informática;
- laboratório de ciências;
- laboratório de química;
- quadra;
- auditório;
- sala maker;
- biblioteca.

### 8.3 Conflito de uso

Um espaço não pode ser usado por duas turmas ao mesmo tempo, salvo se houver configuração explícita permitindo compartilhamento.

### 8.4 Bloqueios

Espaços podem ter horários bloqueados por:

- manutenção;
- eventos;
- uso administrativo;
- reserva fixa.

---

## 9. Regras de Unidades

### 9.1 Horários de funcionamento

Cada unidade pode ter horários diferentes.

Exemplos:

- unidade A funciona das 07:00 às 18:00;
- unidade B tem aulas noturnas;
- unidade C tem Educação Infantil apenas pela manhã.

### 9.2 Calendário próprio

Cada unidade pode ter eventos ou bloqueios próprios.

### 9.3 Compartilhamento de professores

O sistema deve permitir que professores sejam compartilhados entre unidades, mas com restrições de:

- disponibilidade;
- deslocamento;
- carga horária;
- preferência;
- limite operacional.

---

## 10. Cadastro de Informações

A primeira grande etapa do produto é permitir registrar os dados necessários para o algoritmo.

### 10.1 Cadastros mínimos para gerar uma grade

Para gerar uma grade, o sistema precisa de:

1. tenant;
2. unidades;
3. horários/slots de cada unidade;
4. níveis de ensino;
5. séries;
6. turmas;
7. disciplinas;
8. matriz curricular;
9. professores;
10. habilitações dos professores;
11. disponibilidade dos professores;
12. espaços físicos;
13. restrições de disciplinas e espaços;
14. regras de deslocamento entre unidades;
15. eventos ou bloqueios fixos.

### 10.2 Importação de dados

Como escolas grandes já podem ter planilhas, o sistema deve permitir importação.

Possíveis importações:

- professores via CSV/Excel;
- turmas via CSV/Excel;
- matriz curricular via CSV/Excel;
- disponibilidade dos professores via formulário ou planilha;
- salas e espaços via CSV/Excel.

### 10.3 Validação dos dados antes da geração

Antes de tentar gerar a grade, o sistema deve rodar uma validação inicial.

Exemplos:

- disciplina sem professor habilitado;
- turma sem matriz curricular;
- professor sem disponibilidade cadastrada;
- laboratório exigido, mas inexistente na unidade;
- carga horária da turma maior que slots disponíveis;
- professor com carga horária requerida maior que disponibilidade;
- unidade sem horários cadastrados.

---

## 11. Geração da Grade

### 11.1 Objetivo

Gerar uma grade válida ou o mais próxima possível da ideal.

O sistema deve buscar:

1. atender todas as restrições rígidas;
2. maximizar a qualidade da grade segundo restrições flexíveis;
3. explicar conflitos e impossibilidades.

### 11.2 Saídas possíveis

O sistema pode retornar:

- grade totalmente válida;
- grade válida, mas não ideal;
- grade parcialmente gerada;
- impossibilidade de gerar grade sem mudanças;
- relatório de conflitos.

### 11.3 Pontuação da grade

A grade pode receber uma pontuação.

Exemplo:

- 100%: todas as restrições rígidas e flexíveis atendidas;
- 90%: rígidas atendidas, poucas preferências violadas;
- 70%: rígidas atendidas, muitas preferências violadas;
- inválida: alguma restrição rígida violada.

### 11.4 Explicabilidade

O sistema deve explicar decisões e conflitos.

Exemplos:

- “Não foi possível alocar Química no 2º ano B porque não há laboratório disponível nos horários em que o professor está disponível.”
- “A professora Maria tem disponibilidade apenas segunda e quarta de manhã, mas precisa cumprir 18 aulas semanais.”
- “O professor João aparece em duas unidades com intervalo insuficiente de deslocamento.”
- “A carga horária exigida para a turma 9º A é maior que a quantidade de slots disponíveis no turno.”

---

## 12. O Que Falta Para Ser Possível

Essa é uma parte central do produto.

Quando não conseguir gerar uma grade ideal ou válida, o sistema deve indicar caminhos.

### 12.1 Tipos de recomendação

O sistema pode sugerir:

- contratar ou alocar mais professores para determinada disciplina;
- aumentar disponibilidade de um professor;
- liberar determinado laboratório em outro horário;
- permitir aula dupla em determinada disciplina;
- permitir deslocamento em outro dia;
- trocar professor de unidade;
- abrir mais slots no turno;
- reduzir restrição flexível;
- dividir turma;
- criar mais um espaço físico;
- revisar matriz curricular.

### 12.2 Exemplo de saída

```text
Não foi possível gerar uma grade válida para o 1º ano EM A.

Motivos:
1. Física exige 3 aulas semanais.
2. Só há 1 professor habilitado para Física nessa unidade.
3. Esse professor só tem 2 slots disponíveis compatíveis.

Para tornar possível, escolha uma das opções:
- aumentar a disponibilidade do professor em pelo menos 1 slot;
- permitir que outro professor habilitado lecione Física;
- mover uma das aulas para outra unidade/turno;
- reduzir ou reorganizar uma restrição de laboratório associada.
```

---

## 13. Priorização Inicial do Produto

### 13.1 MVP conceitual

O MVP não precisa resolver todos os casos do Objetivo de primeira.

Mas precisa modelar corretamente:

- multi-tenant;
- unidades;
- usuários por escola;
- professores;
- disciplinas;
- turmas;
- matriz curricular;
- disponibilidade;
- espaços;
- restrições rígidas;
- restrições flexíveis;
- geração de grade;
- relatório de conflitos.

### 13.2 O que pode ficar para depois

Possíveis itens para versões futuras:

- integração com Google Calendar;
- integração com mapas para deslocamento real;
- IA conversacional para explicar conflitos;
- importação avançada de sistemas escolares;
- portal do professor para preencher disponibilidade;
- simulação financeira de contratação;
- versionamento avançado de grades;
- comparação entre cenários;
- aprovação colaborativa.

---

## 14. Perguntas em Aberto

### 14.1 Sobre o Objetivo

- Quais são as 13 unidades próprias?
- Todas seguem a mesma matriz curricular?
- Todas têm os mesmos horários de aula?
- Existem professores exclusivos de uma unidade?
- Existem professores que obrigatoriamente circulam entre unidades?
- Há turnos diferentes por unidade?
- Há Ensino Infantil, Fundamental e Médio em todas as unidades?
- A grade é anual, semestral ou pode mudar por bimestre?

### 14.2 Sobre professores

- O professor informa disponibilidade ou a coordenação define?
- Disponibilidade é rígida ou negociável?
- Existe carga mínima contratual?
- Existe limite de aulas consecutivas?
- Existe limite de unidades por dia?
- Existem professores substitutos ou reserva?

### 14.3 Sobre disciplinas

- Quais disciplinas exigem laboratório?
- Quais aceitam aula dupla?
- Quais devem ser distribuídas pela semana?
- Quais podem acontecer simultaneamente por divisão de turma?
- Existem eletivas ou itinerários formativos?

### 14.4 Sobre espaços

- Cada unidade tem quantos laboratórios?
- Laboratórios são específicos por disciplina?
- Espaços podem ser compartilhados?
- Há salas fixas por turma?

### 14.5 Sobre qualidade da grade

- O que a escola considera uma grade boa?
- Minimizar janelas de professor é mais importante que distribuir bem disciplinas?
- A prioridade é professor, turma, unidade ou espaço?
- Quem decide quando uma restrição pode ser flexibilizada?

---

## 15. Ideia de Arquitetura de Regras

O sistema pode organizar regras em três camadas:

### 15.1 Regras globais do tenant

Valem para toda a organização.

Exemplos:

- duração padrão de aula;
- política de janelas;
- limite de aulas por dia;
- peso das restrições flexíveis.

### 15.2 Regras da unidade

Valem para uma unidade específica.

Exemplos:

- horário de funcionamento;
- espaços disponíveis;
- bloqueios locais;
- matriz curricular adaptada.

### 15.3 Regras específicas

Valem para professores, turmas, disciplinas ou espaços.

Exemplos:

- professor X não trabalha às sextas;
- laboratório Y bloqueado na quarta;
- Química precisa de laboratório;
- 3º EM A tem simulado toda sexta de manhã.

---

## 16. Conceitos Importantes Para o Algoritmo

Mesmo que o documento atual seja de regra de negócio, algumas ideias ajudam a orientar o futuro técnico.

### 16.1 Problema de otimização com restrições

O problema se parece com um problema clássico de timetabling/scheduling.

Ele provavelmente exigirá:

- modelagem de restrições;
- busca por solução viável;
- otimização por pontuação;
- geração de explicações;
- comparação de cenários.

### 16.2 Possíveis abordagens técnicas futuras

Ainda não é decisão final, mas opções incluem:

- constraint programming;
- OR-Tools;
- programação inteira;
- heurísticas;
- algoritmos genéticos;
- simulated annealing;
- combinação de heurísticas com validação de restrições.

### 16.3 Regra importante

O algoritmo não pode ser uma “caixa-preta” total.

A escola precisa entender por que uma grade foi gerada daquela forma e o que bloqueia uma solução melhor.

---

## 17. Próximos Passos de Descoberta

1. Mapear as entidades definitivas do domínio.
2. Separar restrições rígidas e flexíveis.
3. Criar exemplos reais pequenos, antes do caso Objetivo completo.
4. Desenhar um fluxo de cadastro inicial.
5. Definir o primeiro formato de importação por planilha.
6. Criar um exemplo de grade com 1 unidade, 3 turmas, 5 professores e poucos espaços.
7. Testar manualmente as regras nesse exemplo.
8. Só depois pensar no algoritmo.

---

## 18. Observação de Produto

O caso Objetivo deve ser usado como caso extremo e realista.

Mas o produto precisa ser vendável para escolas menores. Portanto, a interface deve permitir começar simples e crescer em complexidade.

Uma escola pequena talvez precise apenas de:

- professores;
- turmas;
- disciplinas;
- disponibilidade;
- salas;
- geração de grade.

Uma rede grande como o Objetivo precisa de:

- multiunidades;
- deslocamento;
- muitos níveis de ensino;
- regras específicas por espaço;
- conflitos complexos;
- relatórios de impossibilidade;
- simulações de cenário.

O produto deve atender os dois mundos sem obrigar a escola pequena a preencher informações desnecessárias.

---

## 19. Refinamento a partir de uma grade real — Fundamental II 2022

Arquivo analisado:

```text
Horário Completo Fund.II - VERSÃO 25-01-2022.xlsx
```

### 19.1 O que a planilha revela

A planilha não é apenas uma lista de aulas. Ela já mostra várias regras de negócio escondidas no formato.

Foram identificadas:

- **15 abas** de grade;
- **13 unidades/turnos representados**;
- **96 turmas** do Fundamental II;
- **2.535 aulas preenchidas**;
- **165 nomes de professores ou combinações de professores**;
- **25 códigos de disciplina ou combinações de disciplinas**;
- turnos de **manhã** e **tarde**;
- turmas do **6º ao 9º ano**;
- grades com **5 ou 6 aulas por dia**;
- turmas com carga semanal típica de **25, 26, 29 ou 30 aulas**;
- várias ocorrências de aulas com **dois professores/duas disciplinas no mesmo slot**.

Isso confirma que o produto precisa tratar o problema como uma grade real de rede escolar, não como uma grade simples de uma única escola.

### 19.2 Estrutura observada na planilha

Cada aba representa uma combinação de:

- unidade;
- nível de ensino;
- turno.

Exemplos de abas:

- `AL FUN M` → Alphaville, Fundamental II, manhã;
- `AL FUN T` → Alphaville, Fundamental II, tarde;
- `CA FUN M` → Cantareira, Fundamental II, manhã;
- `TE FUN T` → Teodoro, Fundamental II, tarde.

Cada turma aparece como um bloco de três colunas:

```text
Prof | Disc | Fre
```

Isso sugere que uma aula alocada deve guardar pelo menos:

- professor;
- disciplina;
- frequência ou observação associada;
- turma;
- dia;
- número da aula;
- unidade;
- turno.

A coluna `Fre` apareceu vazia na maior parte da amostra analisada, mas deve ser mantida no modelo como campo possível, porque ela provavelmente representa frequência, frente, fragmentação, observação ou algum código operacional usado pela escola.

### 19.3 Unidades identificadas no exemplo

A planilha contém unidades como:

- Alphaville;
- Cantareira;
- Granja Viana;
- Ipiranga;
- Luís Goes;
- Marquês;
- Paulista;
- Pinheiros;
- Paz;
- Tatuapé;
- Teodoro;
- Vergueiro.

Observação: algumas unidades aparecem em mais de um turno. Portanto, `unidade` e `turno` não devem ser confundidos. O modelo precisa separar:

```text
Unidade Escolar
Turno
Grade da Unidade no Turno
```

Regra confirmada por Thiago:

```text
Uma escola pode ter somente manhã, somente tarde, manhã e tarde, ou período integral.
```

Portanto, o sistema deve tratar turno/período como uma configuração flexível da unidade, não como uma enumeração fechada apenas com manhã/tarde.

Períodos iniciais possíveis:

- manhã;
- tarde;
- noite, se algum cliente usar;
- integral;
- contraturno;
- personalizado.

Uma unidade pode ter mais de um período ativo ao mesmo tempo.

### 19.4 Padrão de nomes das turmas

As turmas seguem uma codificação compacta.

Exemplos:

```text
AL 6ª M1
AL 6ª M2
AL 7ª M1
AL 8ª M1
AL 9ª M3
CA 6ª T1
TE 9ª T1
VE 9ª M2
```

Aparentemente o código contém:

```text
[prefixo da unidade] [ano/série] [turno + número da turma]
```

Exemplo:

```text
AL 6ª M1
```

Pode significar:

- unidade: Alphaville;
- série: 6º ano;
- turno: manhã;
- turma/seção: 1.

Regra de negócio derivada:

O sistema deve permitir nomes amigáveis e códigos estruturados para turmas. O código estruturado ajuda importação, validação e comparação entre planilhas.

### 19.5 Padrão de dias e aulas

A grade usa dias da semana como blocos:

- segunda;
- terça;
- quarta;
- quinta;
- sexta.

Cada dia possui aulas numeradas:

```text
1ª Aula
2ª Aula
3ª Aula
4ª Aula
5ª Aula
6ª Aula
```

Algumas grades têm 5 aulas por dia; outras têm 6. Algumas turmas deixam a 6ª aula vazia em determinados dias.

Regra de negócio derivada:

O sistema não pode assumir que todas as turmas têm o mesmo número de aulas por dia. A quantidade de slots deve ser configurável por:

- tenant;
- unidade;
- período/turno;
- série;
- turma;
- dia da semana.

Para período integral, a configuração de slots precisa permitir uma grade contínua ou composta, por exemplo:

- manhã + almoço + tarde;
- manhã regular + contraturno;
- blocos pedagógicos maiores;
- atividades não curriculares no meio da grade;
- horários de descanso, refeição e transição.

O sistema deve evitar uma modelagem rígida demais baseada apenas em `M` e `T`.

### 19.6 Códigos de disciplina observados

A planilha usa códigos curtos, como:

```text
M, P, C, H, G, A, I, EF, Y, Y-Y, ES, OE
```

Hipóteses prováveis, a confirmar com Thiago:

- `M` → Matemática;
- `P` → Português;
- `C` → Ciências;
- `H` → História;
- `G` → Geografia;
- `A` → Arte;
- `I` → Inglês;
- `EF` → Educação Física;
- `Y` → Informática, usando `Y` para não confundir com `I` de Inglês;
- `Y-Y` → duas frentes, dois professores ou composição paralela de Informática;
- `ES` → Espanhol ou Estudos Sociais;
- `OE` → Orientação Educacional.

Regra confirmada por Thiago:

```text
Y = Informática. O código não usa I para evitar confusão com Inglês.
```

Regra de negócio derivada:

O sistema deve ter uma entidade de **Disciplina** separada de **Código da Disciplina**.

Exemplo:

```text
Nome: Matemática
Código interno do tenant: M
```

Isso é importante porque cada escola pode usar códigos próprios.

### 19.7 Aulas compostas ou paralelas

Foram encontradas muitas células com dois professores e duas disciplinas no mesmo horário.

Exemplos reais da planilha:

```text
Daiene - Carmen | Y-Y
Júlia - Edu | I-A
Andreia Paixão - Silmara | C-C
Benassi - Edu | I-A
Luana - Pagotto | C-A
Roberto - Alessandro | Y-Y
Angelo - Narciso | C-C
```

Isso muda a modelagem.

Uma aula alocada nem sempre é simplesmente:

```text
1 turma + 1 professor + 1 disciplina + 1 sala + 1 slot
```

Ela pode ser:

```text
1 turma + 2 professores + 2 disciplinas + 1 slot
```

ou:

```text
1 turma dividida em subgrupos + professores diferentes + atividades paralelas
```

ou ainda:

```text
rodízio entre disciplinas/professores em semanas alternadas
```

### 19.8 Nova entidade necessária: Composição de Aula

Para representar os casos compostos, o modelo deve incluir uma entidade conceitual como `Composição de Aula` ou `Grupo de Aula`.

Uma aula alocada deve poder ter um ou mais componentes.

Exemplo simples:

```text
Aula Alocada
- turma: CA 7ª M1
- dia: quarta
- horário: 1ª aula
- componentes:
  - professor: Júlia
    disciplina: I
  - professor: Edu
    disciplina: A
```

Exemplo com mesma disciplina em paralelo:

```text
Aula Alocada
- turma: LG 8ª M1
- dia: terça
- horário: 1ª aula
- componentes:
  - professor: Angelo
    disciplina: C
  - professor: Narciso
    disciplina: C
```

Esse caso pode significar divisão da turma, reforço, laboratório, correção conjunta ou frente diferente da mesma disciplina.

Pergunta importante para descoberta:

```text
Quando aparece "Professor A - Professor B" e "C-C", isso significa dois professores simultâneos para a mesma turma, divisão de turma, alternância semanal ou apenas anotação operacional?
```

### 19.9 Restrições derivadas das aulas compostas

O sistema deve permitir configurar:

- aula com mais de um professor;
- aula com mais de uma disciplina;
- aula com divisão de turma em subgrupos;
- aula com duas frentes da mesma disciplina;
- aula com alternância semanal entendida como revezamento operacional de grupos, não como conceito separado nesta versão;
- aula com professor titular e professor auxiliar;
- aula que ocupa mais de um espaço físico;
- aula que aparece como uma única aula para a turma, mas como duas alocações para professores.

Essas situações afetam:

- contagem de carga horária da turma;
- contagem de carga horária do professor;
- disponibilidade de professores;
- uso de salas/laboratórios;
- validação de conflitos;
- importação de planilhas existentes.

### 19.10 Carga horária observada

As turmas não têm todas a mesma carga semanal na planilha.

Distribuição observada:

- muitas turmas com **26 aulas semanais**;
- algumas com **25 aulas semanais**;
- algumas com **29 aulas semanais**;
- algumas com **30 aulas semanais**.

Regra de negócio derivada:

A carga horária semanal não deve ser definida apenas por nível de ensino. Ela pode variar por:

- unidade;
- série;
- turma;
- turno;
- versão da matriz curricular;
- ano letivo.

### 19.11 Slots vazios

A análise encontrou muitos slots vazios dentro da estrutura da grade.

Isso pode significar:

- ausência real de aula;
- janela da turma;
- 6ª aula não usada naquele dia;
- espaço reservado;
- informação ainda não preenchida;
- diferença entre turno regular e carga complementar.

Regra de negócio derivada:

No modelo atual, qualquer slot vazio na grade final indica que a grade ainda não está pronta.

### 19.12 Status da grade

O título da planilha usa a expressão:

```text
HORÁRIO PROVISÓRIO
```

Isso indica que uma grade pode ter status de versão.

Novos status necessários:

- rascunho;
- provisória;
- em validação;
- aprovada;
- publicada;
- arquivada;
- substituída.

Também será importante versionar alterações.

Exemplo:

```text
Grade Fundamental II 2026 — versão 1
Grade Fundamental II 2026 — versão 2
Grade Fundamental II 2026 — versão final
```

### 19.13 Importação de planilhas legadas

A planilha mostra que muitas escolas provavelmente já trabalham com arquivos manuais em Excel.

O produto deve ter importação com etapas:

1. upload da planilha;
2. identificação automática de abas;
3. leitura de unidades, turnos e turmas;
4. mapeamento de colunas `Prof`, `Disc`, `Fre`;
5. normalização de professores e disciplinas;
6. identificação de aulas compostas;
7. validação de conflitos;
8. tela de revisão antes de gravar no sistema.

### 19.14 Validações específicas que a planilha sugere

Além das validações já previstas, o sistema deve verificar:

- professor com nomes escritos de formas diferentes;
- disciplina desconhecida pelo código;
- célula com professor, mas sem disciplina;
- célula com disciplina, mas sem professor;
- aula composta com quantidade diferente de professores e disciplinas;
- turma com carga semanal divergente da matriz;
- turma com slot vazio onde deveria haver aula;
- professor alocado simultaneamente em duas turmas;
- professor alocado em turnos/unidades incompatíveis;
- disciplina com código composto não mapeado;
- aula de Educação Física ou laboratório sem espaço associado;
- grade provisória sendo tratada como definitiva sem aprovação.

### 19.15 Nova prioridade de produto após olhar a planilha

Antes de tentar criar o algoritmo ideal, o MVP deve conseguir fazer algo mais básico e muito valioso:

```text
Importar uma grade real existente e apontar inconsistências.
```

Isso reduz risco porque permite:

- aprender o padrão real das escolas;
- validar o modelo de dados;
- entregar valor antes do gerador automático completo;
- comparar uma grade humana com uma grade gerada;
- criar relatórios de conflito e qualidade.

### 19.16 Fluxo de MVP ajustado

Novo fluxo sugerido para o MVP:

1. cadastrar tenant;
2. cadastrar ou importar unidades;
3. importar uma planilha de grade existente;
4. detectar turmas, professores, disciplinas e slots;
5. pedir ao usuário para confirmar mapeamentos;
6. salvar a grade como versão provisória/importada;
7. rodar validações;
8. mostrar conflitos e estatísticas;
9. só depois oferecer geração ou otimização de nova grade.

### 19.17 Perguntas novas para Thiago

- O que exatamente significa a coluna `Fre`?
- O que significa o código `Y`?
- O que significa `Y-Y`?
- Quando aparecem dois professores separados por hífen, eles estão na mesma aula ao mesmo tempo?
- Quando aparecem dois códigos de disciplina, a turma é dividida?
- Existem aulas em semanas alternadas?
- O 6º horário vazio é aula vaga, intervalo, carga não usada ou apenas célula não preenchida?
- A grade provisória era revisada por quem?
- O Objetivo usava algum sistema oficial ou tudo era consolidado em Excel?
- Professores podiam dar aula em unidades diferentes no mesmo dia?
- Havia regra formal de deslocamento entre unidades?
- A distribuição de 25/26/29/30 aulas por semana vem da série, da unidade ou de decisões locais?
