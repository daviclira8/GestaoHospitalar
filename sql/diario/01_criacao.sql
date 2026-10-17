DROP VIEW  IF EXISTS vw_ficha_usuario      CASCADE;
DROP VIEW  IF EXISTS vw_linha_do_tempo     CASCADE;
DROP TABLE IF EXISTS metrica_saude         CASCADE;
DROP TABLE IF EXISTS exame                 CASCADE;
DROP TABLE IF EXISTS consulta              CASCADE;
DROP TABLE IF EXISTS aplicacao_vacina      CASCADE;
DROP TABLE IF EXISTS vacina                CASCADE;
DROP TABLE IF EXISTS usuario_doenca        CASCADE;
DROP TABLE IF EXISTS doenca                CASCADE;
DROP TABLE IF EXISTS alergia               CASCADE;
DROP TABLE IF EXISTS usuario               CASCADE;
DROP TYPE  IF EXISTS sexo                  CASCADE;
DROP TYPE  IF EXISTS tipo_sanguineo        CASCADE;
DROP TYPE  IF EXISTS fator_rh              CASCADE;
DROP TYPE  IF EXISTS gravidade_alergia     CASCADE;
DROP TYPE  IF EXISTS status_doenca         CASCADE;

CREATE TYPE sexo              AS ENUM ('masculino', 'feminino', 'outro');
CREATE TYPE tipo_sanguineo    AS ENUM ('A', 'B', 'AB', 'O');
CREATE TYPE fator_rh          AS ENUM ('positivo', 'negativo');
CREATE TYPE gravidade_alergia AS ENUM ('leve', 'moderada', 'grave');
CREATE TYPE status_doenca     AS ENUM ('ativa', 'controlada', 'curada');

CREATE TABLE usuario (
    id               SERIAL        PRIMARY KEY,
    nome             VARCHAR(120)  NOT NULL,
    cpf              CHAR(11)      NOT NULL UNIQUE
                     CHECK (cpf ~ '^[0-9]{11}$'),
    data_nascimento  DATE          NOT NULL
                     CHECK (data_nascimento <= CURRENT_DATE),
    sexo             sexo          NOT NULL,
    tipo_sanguineo   tipo_sanguineo,
    fator_rh         fator_rh,
    cidade           VARCHAR(80),
    uf               CHAR(2)       CHECK (uf ~ '^[A-Z]{2}$'),
    email            VARCHAR(120)  UNIQUE
                     CHECK (email LIKE '%_@_%._%'),
    telefone         VARCHAR(20),
    criado_em        TIMESTAMP     NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_sangue_completo
        CHECK ((tipo_sanguineo IS NULL) = (fator_rh IS NULL))
);

CREATE TABLE alergia (
    id          SERIAL             PRIMARY KEY,
    usuario_id  INT                NOT NULL
                REFERENCES usuario(id) ON DELETE CASCADE,
    substancia  VARCHAR(100)       NOT NULL,
    gravidade   gravidade_alergia  NOT NULL,
    observacao  TEXT,
    CONSTRAINT uq_alergia UNIQUE (usuario_id, substancia)
);

CREATE TABLE doenca (
    id             SERIAL        PRIMARY KEY,
    nome           VARCHAR(120)  NOT NULL UNIQUE,
    cid            VARCHAR(10)   UNIQUE,
    impede_doacao  BOOLEAN       NOT NULL DEFAULT FALSE
);

CREATE TABLE usuario_doenca (
    id                SERIAL         PRIMARY KEY,
    usuario_id        INT            NOT NULL
                      REFERENCES usuario(id) ON DELETE CASCADE,
    doenca_id         INT            NOT NULL
                      REFERENCES doenca(id)  ON DELETE RESTRICT,
    data_diagnostico  DATE           NOT NULL
                      CHECK (data_diagnostico <= CURRENT_DATE),
    status            status_doenca  NOT NULL DEFAULT 'ativa',
    CONSTRAINT uq_usuario_doenca UNIQUE (usuario_id, doenca_id, data_diagnostico)
);

CREATE TABLE vacina (
    id          SERIAL        PRIMARY KEY,
    nome        VARCHAR(100)  NOT NULL,
    fabricante  VARCHAR(100),
    CONSTRAINT uq_vacina UNIQUE (nome, fabricante)
);

CREATE TABLE aplicacao_vacina (
    id              SERIAL       PRIMARY KEY,
    usuario_id      INT          NOT NULL
                    REFERENCES usuario(id) ON DELETE CASCADE,
    vacina_id       INT          NOT NULL
                    REFERENCES vacina(id)  ON DELETE RESTRICT,
    data_aplicacao  DATE         NOT NULL
                    CHECK (data_aplicacao <= CURRENT_DATE),
    dose            VARCHAR(20)  NOT NULL,
    lote            VARCHAR(30),
    CONSTRAINT uq_aplicacao UNIQUE (usuario_id, vacina_id, dose)
);

CREATE TABLE consulta (
    id             SERIAL        PRIMARY KEY,
    usuario_id     INT           NOT NULL
                   REFERENCES usuario(id) ON DELETE CASCADE,
    data_hora      TIMESTAMP     NOT NULL,
    especialidade  VARCHAR(80)   NOT NULL,
    profissional   VARCHAR(120),
    local          VARCHAR(120),
    observacoes    TEXT
);

CREATE TABLE exame (
    id           SERIAL        PRIMARY KEY,
    usuario_id   INT           NOT NULL
                 REFERENCES usuario(id)  ON DELETE CASCADE,
    consulta_id  INT
                 REFERENCES consulta(id) ON DELETE SET NULL,
    tipo         VARCHAR(100)  NOT NULL,
    data         DATE          NOT NULL CHECK (data <= CURRENT_DATE),
    resultado    TEXT
);

CREATE TABLE metrica_saude (
    id          SERIAL         PRIMARY KEY,
    usuario_id  INT            NOT NULL
                REFERENCES usuario(id) ON DELETE CASCADE,
    tipo        VARCHAR(50)    NOT NULL,
    valor       NUMERIC(8,2)   NOT NULL CHECK (valor >= 0),
    unidade     VARCHAR(20)    NOT NULL,
    data_hora   TIMESTAMP      NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alergia_usuario     ON alergia(usuario_id);
CREATE INDEX idx_usdoenca_usuario    ON usuario_doenca(usuario_id);
CREATE INDEX idx_usdoenca_doenca     ON usuario_doenca(doenca_id);
CREATE INDEX idx_aplicacao_usuario   ON aplicacao_vacina(usuario_id);
CREATE INDEX idx_consulta_usuario    ON consulta(usuario_id, data_hora);
CREATE INDEX idx_exame_usuario       ON exame(usuario_id, data);
CREATE INDEX idx_exame_consulta      ON exame(consulta_id);
CREATE INDEX idx_metrica_usuario     ON metrica_saude(usuario_id, tipo, data_hora);

CREATE VIEW vw_ficha_usuario AS
SELECT u.id,
       u.nome,
       u.cpf,
       u.data_nascimento,
       DATE_PART('year', AGE(u.data_nascimento))::INT              AS idade,
       u.sexo,
       u.tipo_sanguineo,
       u.fator_rh,
       u.tipo_sanguineo::TEXT ||
         CASE u.fator_rh WHEN 'positivo' THEN '+' WHEN 'negativo' THEN '-' END
                                                                   AS sangue,
       u.cidade,
       u.uf,
       EXISTS (SELECT 1
                 FROM usuario_doenca ud
                 JOIN doenca d ON d.id = ud.doenca_id
                WHERE ud.usuario_id = u.id
                  AND ud.status    <> 'curada'
                  AND d.impede_doacao)                             AS restricao_doacao,
       (SELECT STRING_AGG(a.substancia || ' (' || a.gravidade || ')', ', ')
          FROM alergia a WHERE a.usuario_id = u.id)                AS alergias
  FROM usuario u;

CREATE VIEW vw_linha_do_tempo AS
SELECT usuario_id, data_hora::DATE AS data, 'Consulta' AS evento,
       especialidade || COALESCE(' — ' || profissional, '') AS descricao
  FROM consulta
UNION ALL
SELECT usuario_id, data, 'Exame', tipo || COALESCE(': ' || resultado, '')
  FROM exame
UNION ALL
SELECT av.usuario_id, av.data_aplicacao, 'Vacina', v.nome || ' (' || av.dose || ')'
  FROM aplicacao_vacina av JOIN vacina v ON v.id = av.vacina_id
UNION ALL
SELECT ud.usuario_id, ud.data_diagnostico, 'Diagnóstico',
       d.nome || ' [' || ud.status || ']'
  FROM usuario_doenca ud JOIN doenca d ON d.id = ud.doenca_id;
