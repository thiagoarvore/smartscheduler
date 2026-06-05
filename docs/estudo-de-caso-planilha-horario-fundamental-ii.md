# Estudo de caso — planilha de horário do Fundamental II

> **Versão:** 0.1  
> **Fonte:** `/opt/data/cache/documents/doc_2848c84cd373_Horário Completo Fund.II - VERSÃO 25-01-2022.xlsx`  
> **Objetivo:** analisar a estrutura da planilha usada como referência prática para a modelagem da grade.  
> **Escopo:** leitura estrutural da planilha; não é importação de dados nem especificação de implementação.

---

## 1. Resumo do arquivo

- Total de abas: `15`
- Abas de manhã: `12`
- Abas de tarde: `3`

A leitura mostra um workbook organizado por **campus + período**. Cada aba representa um recorte operacional específico da rede/escola, com a grade semanal dos grupos daquele contexto.

## 2. Padrão estrutural observado

Em praticamente todas as abas, a planilha repete o mesmo padrão:

- nome do campus no topo;
- indicação do período (`MANHÃ` ou `TARDE`);
- identificadores das turmas/classes na linha superior;
- grade em matriz com dias da semana nas linhas e ordem das aulas nas colunas;
- em cada bloco de turma, campos de **professor** e **disciplina**;
- coluna auxiliar `Fre`, cujo significado ainda precisa ser confirmado tecnicamente.

## 3. O que a planilha sugere sobre o domínio

### 3.1 O período é uma fronteira forte

A planilha não trata manhã e tarde como mera etiqueta visual. Elas aparecem como blocos separados, com turmas, docentes e arranjos próprios. Para o modelo, isso reforça que `Period` deve ser um recorte operacional relevante, e não só um atributo decorativo.

### 3.2 A turma nasce do nível/série

As identificações das classes seguem o padrão de série + período + sequência, como `6ª M1`, `7ª T1` e semelhantes. Isso combina com a regra de negócio já confirmada: turma sempre derivada de uma série, sem mistura multi-série.

### 3.3 A grade é semanal

A organização por dias da semana e por ordem das aulas confirma que a unidade de planejamento da planilha é semanal. Isso apoia a modelagem de `weekly_lessons` como quantidade semanal e `lesson_duration_min` como duração individual de cada aula.

### 3.4 Há indícios de aulas compartilhadas

Algumas células trazem mais de um professor ou notação composta, sugerindo aulas compartilhadas ou arranjos especiais. Esse ponto ainda exige decisão de domínio antes de virar regra fechada no backend.

## 4. Implicações diretas para a modelagem

- `Period` deve representar o turno operacional da unidade, com manhã e tarde como contextos distintos;
- `Timetable` deve existir por unidade, período e ano letivo;
- `TimetableVersion` deve ser apenas um cenário gerado, sem edição manual;
- `WorkloadItem` deve separar quantidade semanal de aulas e duração em minutos;
- `ClassGroup` deve continuar ligado à `Series` e ao `Period`;
- o MVP não precisa de importação da planilha: o sistema apenas gera a grade.

## 5. Observações em aberto

- o significado técnico de `Fre` ainda não está fechado;
- as regras de aulas duplas e compartilhadas ainda precisam de definição final;
- a planilha é uma referência operacional forte, mas não substitui o modelo normalizado do sistema.

---

## 6. Exemplos de abas observadas

- `AL FUN M` — período: **Manhã**; turmas detectadas: `AL 6ª M1`, `AL 9ª M1`.
- `AL FUN T` — período: **Tarde**; turmas detectadas: `AL 6ª T1`.
- `CA FUN M` — período: **Manhã**; turmas detectadas: `CA 6ª M1`, `CA 8ª M3`.
- `CA FUN T` — período: **Tarde**; turmas detectadas: `CA 6ª T1`.
- `GV FUN M` — período: **Manhã**; turmas detectadas: `GV 6ª M1`, `GV 8ª M3`.
- `IP FUN M` — período: **Manhã**; turmas detectadas: `IP 6ª M1`, `IP 8ª M2`.
- `LG FUN M` — período: **Manhã**; turmas detectadas: `LG 6ª M1`.
- `MA FUN M` — período: **Manhã**; turmas detectadas: `MA 6ª M1`, `MA 8ª M3`.
- `PA FUN M` — período: **Manhã**; turmas detectadas: `PA 6ª M1`, `PA 9ª M2`.
- `PI FUN M` — período: **Manhã**; turmas detectadas: `PI 7º M1`.
- `PZ FUN M` — período: **Manhã**; turmas detectadas: `PZ 6ª M1`, `PZ 8ª M2`.
- `TA FUN M` — período: **Manhã**; turmas detectadas: `TA 6ª M1`, `TA 9ª M2`.
- `TE FUN M` — período: **Manhã**; turmas detectadas: `TE 6ª M1`, `TE 9ª M2`.
- `TE FUN T` — período: **Tarde**; turmas detectadas: `TE 7ª T1`.
- `VE FUN M` — período: **Manhã**; turmas detectadas: `VE 6ª M1`, `VE 9ªM1`.
