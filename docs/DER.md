# Modelagem dos Bancos de Dados (DER / MER)

SGBD utilizado: **SQLite 3**.
Scripts de criacao: `DiarioPessoal/bdDiarioPessoal.sql` e
`CentralHospitalar/bdCentralHospitalar.sql`.

Convencoes dos diagramas: `PK` chave primaria, `FK` chave estrangeira,
`UK` chave unica. A notacao de cardinalidade segue o padrao "pe de galinha"
(`||--o{` = um para muitos, `}o--o{` = muitos para muitos).

---

## 1. Diario de Saude Pessoal

### Entidades e cardinalidades

| Relacionamento | Cardinalidade | Leitura |
|---|---|---|
| USUARIO - CONSULTA | 1:N | um usuario tem varias consultas; cada consulta pertence a um usuario |
| PROFISSIONAL - CONSULTA | 1:N | um profissional realiza varias consultas |
| USUARIO - EXAME | 1:N | um usuario realiza varios exames |
| CONSULTA - EXAME | 1:N (opcional) | um exame pode ter se originado de uma consulta (FK aceita NULL) |
| USUARIO - VACINACAO | 1:N | um usuario recebe varias doses |
| VACINA - VACINACAO | 1:N | uma vacina e aplicada em varias doses/usuarios |
| USUARIO - ALERGIA | N:N | resolvido pela tabela associativa USUARIO_ALERGIA |

```mermaid
erDiagram
    USUARIO ||--o{ CONSULTA        : "realiza"
    USUARIO ||--o{ EXAME           : "realiza"
    USUARIO ||--o{ VACINACAO       : "recebe"
    USUARIO ||--o{ USUARIO_ALERGIA : "possui"
    ALERGIA ||--o{ USUARIO_ALERGIA : "classifica"
    PROFISSIONAL ||--o{ CONSULTA   : "atende"
    CONSULTA ||--o{ EXAME          : "origina"
    VACINA   ||--o{ VACINACAO      : "aplicada em"

    USUARIO {
        INTEGER id_usuario PK
        TEXT    nome
        TEXT    cpf UK
        TEXT    data_nascimento
        TEXT    sexo
        TEXT    tipo_sanguineo "A, B, AB, O"
        TEXT    fator_rh "+ ou -"
        TEXT    telefone
        TEXT    email
    }
    PROFISSIONAL {
        INTEGER id_profissional PK
        TEXT    nome
        TEXT    especialidade
        TEXT    registro UK "CRM / COREN"
    }
    ALERGIA {
        INTEGER id_alergia PK
        TEXT    nome UK
        TEXT    categoria "MEDICAMENTO, ALIMENTO, AMBIENTAL, OUTRO"
    }
    USUARIO_ALERGIA {
        INTEGER id_usuario PK "FK -> USUARIO"
        INTEGER id_alergia PK "FK -> ALERGIA"
        TEXT    gravidade "LEVE, MODERADA, GRAVE"
        TEXT    data_registro
        TEXT    observacao
    }
    CONSULTA {
        INTEGER id_consulta PK
        INTEGER id_usuario FK
        INTEGER id_profissional FK
        TEXT    data_hora
        TEXT    motivo
        TEXT    diagnostico
        TEXT    prescricao
    }
    EXAME {
        INTEGER id_exame PK
        INTEGER id_usuario FK
        INTEGER id_consulta FK "opcional"
        TEXT    tipo
        TEXT    data_realizacao
        TEXT    laboratorio
        TEXT    resultado
        TEXT    status "PENDENTE, CONCLUIDO, CANCELADO"
    }
    VACINA {
        INTEGER id_vacina PK
        TEXT    nome UK
        INTEGER doses_recomendadas
        TEXT    fabricante
    }
    VACINACAO {
        INTEGER id_vacinacao PK
        INTEGER id_usuario FK
        INTEGER id_vacina FK
        INTEGER dose "UK com usuario e vacina"
        TEXT    data_aplicacao
        TEXT    lote
        TEXT    local_aplicacao
    }
```

### Decisoes de modelagem

- **Tipo sanguineo e fator RH separados** (`tipo_sanguineo` + `fator_rh`), com
  `CHECK` em cada um. A exibicao "O-" e feita por concatenacao nas consultas.
- **Alergias em catalogo + tabela associativa**: evita repetir o nome da
  alergia em cada usuario e permite que a *gravidade* seja um atributo do
  relacionamento, nao da alergia.
- **Exame com FK opcional para consulta**: exames podem ser avulsos
  (`ON DELETE SET NULL` preserva o exame se a consulta for removida).
- **VACINACAO com `UNIQUE (id_usuario, id_vacina, dose)`**: impede registrar a
  mesma dose duas vezes e permite calcular doses faltantes comparando com
  `vacina.doses_recomendadas`.

---

## 2. Central Hospitalar de Transplantes

### Entidades e cardinalidades

| Relacionamento | Cardinalidade | Leitura |
|---|---|---|
| HOSPITAL - DOADOR / RECEPTOR | 1:N | cada pessoa esta vinculada a um hospital |
| DOADOR - ORGAO_DISPONIVEL | 1:N | um doador pode doar varios orgaos |
| TIPO_ORGAO - ORGAO_DISPONIVEL | 1:N | classifica o orgao captado |
| RECEPTOR - FILA_ESPERA | 1:N | um receptor pode aguardar mais de um tipo de orgao |
| TIPO_ORGAO - FILA_ESPERA | 1:N | cada posicao na fila e para um tipo de orgao |
| ORGAO_DISPONIVEL - TRANSPLANTE | 1:1 | um orgao gera no maximo um transplante (`UNIQUE`) |
| RECEPTOR - TRANSPLANTE | 1:N | um receptor pode receber mais de um transplante ao longo do tempo |

```mermaid
erDiagram
    HOSPITAL ||--o{ DOADOR           : "registra"
    HOSPITAL ||--o{ RECEPTOR         : "acompanha"
    HOSPITAL ||--o{ ORGAO_DISPONIVEL : "armazena"
    HOSPITAL ||--o{ TRANSPLANTE      : "realiza"
    DOADOR   ||--o{ ORGAO_DISPONIVEL : "doa"
    TIPO_ORGAO ||--o{ ORGAO_DISPONIVEL : "classifica"
    TIPO_ORGAO ||--o{ FILA_ESPERA    : "define demanda"
    RECEPTOR ||--o{ FILA_ESPERA      : "aguarda em"
    RECEPTOR ||--o{ TRANSPLANTE      : "recebe"
    ORGAO_DISPONIVEL ||--|| TRANSPLANTE : "alocado em"

    HOSPITAL {
        INTEGER id_hospital PK
        TEXT    nome
        TEXT    cidade
        TEXT    uf
        TEXT    cnes UK
    }
    TIPO_ORGAO {
        INTEGER id_tipo_orgao PK
        TEXT    nome UK
        INTEGER tempo_isquemia_horas
    }
    DOADOR {
        INTEGER id_doador PK
        TEXT    nome
        TEXT    cpf UK
        TEXT    data_nascimento
        TEXT    tipo_sanguineo
        TEXT    fator_rh
        TEXT    tipo_doador "VIVO, FALECIDO"
        INTEGER id_hospital FK
        TEXT    data_registro
    }
    RECEPTOR {
        INTEGER id_receptor PK
        TEXT    nome
        TEXT    cpf UK
        TEXT    data_nascimento
        TEXT    tipo_sanguineo
        TEXT    fator_rh
        INTEGER id_hospital FK
        TEXT    contato
    }
    ORGAO_DISPONIVEL {
        INTEGER id_orgao PK
        INTEGER id_doador FK
        INTEGER id_tipo_orgao FK
        INTEGER id_hospital FK
        TEXT    data_captacao
        TEXT    status "DISPONIVEL, RESERVADO, TRANSPLANTADO, DESCARTADO"
        TEXT    observacao
    }
    FILA_ESPERA {
        INTEGER id_fila PK
        INTEGER id_receptor FK "UK com tipo de orgao"
        INTEGER id_tipo_orgao FK
        TEXT    prioridade "EMERGENCIA, ALTA, NORMAL"
        TEXT    data_entrada
        TEXT    status "AGUARDANDO, TRANSPLANTADO, SUSPENSO, OBITO"
    }
    TRANSPLANTE {
        INTEGER id_transplante PK
        INTEGER id_orgao FK "UNIQUE: 1:1 com o orgao"
        INTEGER id_receptor FK
        INTEGER id_hospital FK
        TEXT    data_cirurgia
        TEXT    cirurgiao
        TEXT    resultado "SUCESSO, REJEICAO, OBITO, EM_ACOMPANHAMENTO"
    }
    COMPAT_ABO {
        TEXT abo_doador PK
        TEXT abo_receptor PK
    }
    COMPAT_RH {
        TEXT rh_doador PK
        TEXT rh_receptor PK
    }
```

### Compatibilidade como dado, nao como codigo

As regras de compatibilidade sanguinea ficam em duas tabelas de dominio:

| compat_abo | |
|---|---|
| O | O, A, B, AB |
| A | A, AB |
| B | B, AB |
| AB | AB |

| compat_rh | |
|---|---|
| - | -, + |
| + | + |

A view `vw_compatibilidade` cruza orgao disponivel x fila de espera usando
essas tabelas, de modo que a compatibilidade e resolvida em SQL puro:

```sql
JOIN compat_abo ca ON ca.abo_doador = d.tipo_sanguineo
                  AND ca.abo_receptor = r.tipo_sanguineo
JOIN compat_rh  cr ON cr.rh_doador  = d.fator_rh
                  AND cr.rh_receptor = r.fator_rh
WHERE o.status = 'DISPONIVEL' AND f.status = 'AGUARDANDO'
```

A ordem de alocacao aplicada nas consultas e: **prioridade**
(EMERGENCIA > ALTA > NORMAL) e, em seguida, **maior tempo de espera**.

### Decisoes de modelagem

- **TIPO_ORGAO como entidade** (e nao um texto livre em ORGAO_DISPONIVEL):
  garante que fila e orgao falem do mesmo orgao e guarda o tempo de isquemia,
  usado para destacar orgaos fora do prazo.
- **ORGAO_DISPONIVEL com status**: o ciclo de vida do orgao
  (DISPONIVEL -> RESERVADO -> TRANSPLANTADO / DESCARTADO) fica em um unico
  registro, sem precisar apagar dados.
- **FILA_ESPERA com `UNIQUE (id_receptor, id_tipo_orgao)`**: o receptor nao
  entra duas vezes na mesma fila, mas pode aguardar orgaos diferentes.
- **TRANSPLANTE com `UNIQUE (id_orgao)`**: impede alocar o mesmo orgao duas
  vezes. A efetivacao do transplante ocorre em uma transacao que insere o
  transplante e atualiza o status do orgao e da fila.
