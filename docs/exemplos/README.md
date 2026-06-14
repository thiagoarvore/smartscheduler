# Exemplo Canônico de Grade — Rede de Fundamental II

> **Arquivo:** `docs/exemplos/horario-fundamental-ii-referencia.xlsx`
> **Origem:** fornecido pelo cliente em 13/06/2026, representa uma das maiores redes atendidas pelo Grade Certa.
> **Status:** exemplo de referência. Não usar dados nominais sem anonimização.

## 1. Por que este arquivo existe

Este arquivo é a **linha de base visual e dimensional** para o Grade Certa. Ele mostra:

1. **Porte de escala real** — quantas turmas/unidades o sistema precisa aguentar
2. **Layout de saída** — como a grade é apresentada ao usuário final
3. **Vocabulário do domínio** — como professores, disciplinas e períodos são nomeados
4. **Padrão de qualidade** — o que o cliente espera que o sistema entregue

Todo o desenvolvimento (solver, UI, validações) deve mirar este arquivo como referência de "fez certo".

## 2. Estrutura do arquivo

- **15 abas** = 15 unidades da rede (cada unidade tem sua própria planilha)
- Convenção de nomes: `<SIGLA> FUN M` (manhã) e `<SIGLA> FUN T` (tarde)
- Unidades representadas: AL, AL(T), CA, CA(T), GV, IP, LG, MA, PA, PI, PZ, TA, TE, TE(T), VE

### Cabeçalho de cada aba

```
Linha 1:  [vazio] NOME DA UNIDADE
Linha 2:  [vazio] HORÁRIO PROVISÓRIO DO FUNDAMENTAL II - MANHÃ/TARDE
Linha 3:  Nomes das turmas (ex.: AL 6ª M1, AL 6ª M2, AL 7ª M1, AL 8ª M1)
Linha 4:  Dia | Horários | Prof | Disc | Fre | Prof | Disc | Fre | ...
Corpo:    SEGUNDA a SÁBADO × 1ª a 6ª aula
```

- **Colunas por turma:** `Prof` (nome) + `Disc` (sigla da disciplina) + `Fre` (frequência? ou flag)
- **Linhas:** dia da semana × número da aula (1ª a 6ª)

## 3. Dimensões (escala-alvo)

| Métrica | Valor |
|---------|-------|
| Unidades (abas) | 15 |
| Turmas totais | ~95 |
| Aulas/horário | 528 células preenchidas |
| Séries | 6ª, 7ª, 8ª, 9ª (Fundamental II) |
| Turnos | Manhã (M) e Tarde (T) |
| Aulas/dia por turma | até 6 (1ª a 6ª) |
| Dias/semana | Seg a Sáb |

**Esta é a escala que o solver precisa suportar nativamente** (e considerar até 2-3× maior para clientes futuros).

## 4. Siglas de disciplinas observadas

Lidas diretamente das abas (amostra de AL FUN M e MA FUN M):

- `M` — Matemática
- `P` — Português
- `H` — História
- `I` — Inglês
- `G` — Geografia
- `C` — Ciências
- `EF` — Educação Física
- `A` — Artes

> **Implicação para o modelo:** o sistema precisa suportar **siglas curtas** (1-3 chars) além de nome completo da disciplina. Provavelmente a `Subject` precisa ter campo `short_code`.

## 5. O que o sistema precisa entregar para ser "compatível" com este layout

### 5.1 Saída

- [ ] Exportação por unidade (uma aba por unidade)
- [ ] Convenção de nome de aba `<SIGLA> FUN <M|T>`
- [ ] Cabeçalho com nome da unidade + turno
- [ ] Colunas agrupadas por turma (Prof + Disc + Fre)
- [ ] Linhas agrupadas por dia × número de aula
- [ ] Células vazias onde não há aula

### 5.2 Fidelidade ao exemplo

- [ ] Suportar 6ª série até 9ª série (Fundamental II)
- [ ] Suportar turno M e T
- [ ] Permitir múltiplas turmas da mesma série/unidade (M1, M2, M3...)
- [ ] Mostrar nome curto do professor (não ID)
- [ ] Mostrar sigla da disciplina

### 5.3 Validações a fazer após gerar a grade

Comparando contra o exemplo, o sistema deve detectar:

- [ ] Janelas (buracos) no horário de uma turma
- [ ] Janelas no horário de um professor
- [ ] Professor alocado em 2 turmas no mesmo horário
- [ ] Turma sem cobertura completa de alguma disciplina
- [ ] Aulas duplas/forçadas não respeitadas
- [ ] Inconsistência de carga horária (soma de aulas ≠ carga semanal esperada)

> **Definição de buraco** (registrada no SDD §20.3): slot (dia × número da aula) sem aula alocada, **independentemente do motivo**. O solver registra o buraco, mas não investiga a causa — isso é função da camada de sugestões (§20.4 do SDD).

## 6. Regras de uso deste arquivo

- **NÃO** usar como dado de produção (pode conter dados pessoais de alunos/professores)
- **PODE** usar como fixture de teste, desde que anonimizado
- **PODE** usar como gabarito visual ao construir o exportador
- **DEVE** ser referenciado em qualquer PR que mexa no módulo de export/visualização de grade

## 7. Quando atualizar este exemplo

- [ ] Cliente fornecer nova versão da planilha (ex.: ano letivo 2027)
- [ ] Sistema ganhar suporte a nova série (ex.: Ensino Médio)
- [ ] Layout de saída mudar (decisão de UX)
