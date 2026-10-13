-- =============================================================================
-- SISTEMA 2 - CENTRAL HOSPITALAR DE TRANSPLANTES
-- SGBD: SQLite 3
-- Objetivo: gerenciar doadores, receptores, orgaos disponiveis, filas de
--           espera e identificar compatibilidades (tipo sanguineo + orgao).
--
-- MODELO LOGICO (resumo do DER - ver docs/DER.md)
--   HOSPITAL (1,N) ---- (1,1) DOADOR / RECEPTOR / ORGAO_DISPONIVEL / TRANSPLANTE
--   DOADOR   (1,N) ---- (1,1) ORGAO_DISPONIVEL (1,1) ---- (1,N) TIPO_ORGAO
--   RECEPTOR (1,N) ---- (1,1) FILA_ESPERA      (1,1) ---- (1,N) TIPO_ORGAO
--   ORGAO_DISPONIVEL (1,1) ---- (0,1) TRANSPLANTE (0,1) ---- (1,1) RECEPTOR
--   COMPAT_ABO / COMPAT_RH: tabelas de dominio com as regras de compatibilidade
-- =============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1. REMOCAO DAS TABELAS E VIEWS
-- ----------------------------------------------------------------------------
DROP VIEW  IF EXISTS vw_compatibilidade;
DROP VIEW  IF EXISTS vw_fila_detalhada;
DROP TABLE IF EXISTS transplante;
DROP TABLE IF EXISTS fila_espera;
DROP TABLE IF EXISTS orgao_disponivel;
DROP TABLE IF EXISTS receptor;
DROP TABLE IF EXISTS doador;
DROP TABLE IF EXISTS tipo_orgao;
DROP TABLE IF EXISTS hospital;
DROP TABLE IF EXISTS compat_abo;
DROP TABLE IF EXISTS compat_rh;

-- ----------------------------------------------------------------------------
-- 2. CRIACAO DAS TABELAS
-- ----------------------------------------------------------------------------

CREATE TABLE hospital (
    id_hospital INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT NOT NULL,
    cidade      TEXT NOT NULL,
    uf          TEXT NOT NULL CHECK (length(uf) = 2),
    cnes        TEXT NOT NULL UNIQUE
);

-- Catalogo de orgaos/tecidos, com o tempo maximo de isquemia em horas
CREATE TABLE tipo_orgao (
    id_tipo_orgao        INTEGER PRIMARY KEY AUTOINCREMENT,
    nome                 TEXT    NOT NULL UNIQUE,
    tempo_isquemia_horas INTEGER NOT NULL CHECK (tempo_isquemia_horas > 0)
);

CREATE TABLE doador (
    id_doador       INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT    NOT NULL,
    cpf             TEXT    NOT NULL UNIQUE,
    data_nascimento TEXT    NOT NULL,
    tipo_sanguineo  TEXT    NOT NULL CHECK (tipo_sanguineo IN ('A','B','AB','O')),
    fator_rh        TEXT    NOT NULL CHECK (fator_rh IN ('+','-')),
    tipo_doador     TEXT    NOT NULL CHECK (tipo_doador IN ('VIVO','FALECIDO')),
    id_hospital     INTEGER NOT NULL,
    data_registro   TEXT    NOT NULL DEFAULT (date('now')),
    FOREIGN KEY (id_hospital) REFERENCES hospital(id_hospital)
);

CREATE TABLE receptor (
    id_receptor     INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT    NOT NULL,
    cpf             TEXT    NOT NULL UNIQUE,
    data_nascimento TEXT    NOT NULL,
    tipo_sanguineo  TEXT    NOT NULL CHECK (tipo_sanguineo IN ('A','B','AB','O')),
    fator_rh        TEXT    NOT NULL CHECK (fator_rh IN ('+','-')),
    id_hospital     INTEGER NOT NULL,
    contato         TEXT,
    FOREIGN KEY (id_hospital) REFERENCES hospital(id_hospital)
);

-- Orgao captado e disponivel para alocacao
CREATE TABLE orgao_disponivel (
    id_orgao      INTEGER PRIMARY KEY AUTOINCREMENT,
    id_doador     INTEGER NOT NULL,
    id_tipo_orgao INTEGER NOT NULL,
    id_hospital   INTEGER NOT NULL,                 -- onde o orgao esta hoje
    data_captacao TEXT    NOT NULL,                 -- YYYY-MM-DD HH:MM
    status        TEXT    NOT NULL DEFAULT 'DISPONIVEL'
                  CHECK (status IN ('DISPONIVEL','RESERVADO','TRANSPLANTADO','DESCARTADO')),
    observacao    TEXT,
    FOREIGN KEY (id_doador)     REFERENCES doador(id_doador)         ON DELETE CASCADE,
    FOREIGN KEY (id_tipo_orgao) REFERENCES tipo_orgao(id_tipo_orgao),
    FOREIGN KEY (id_hospital)   REFERENCES hospital(id_hospital)
);

-- Fila de espera: um receptor pode aguardar mais de um tipo de orgao
CREATE TABLE fila_espera (
    id_fila       INTEGER PRIMARY KEY AUTOINCREMENT,
    id_receptor   INTEGER NOT NULL,
    id_tipo_orgao INTEGER NOT NULL,
    prioridade    TEXT    NOT NULL DEFAULT 'NORMAL'
                  CHECK (prioridade IN ('EMERGENCIA','ALTA','NORMAL')),
    data_entrada  TEXT    NOT NULL DEFAULT (date('now')),
    status        TEXT    NOT NULL DEFAULT 'AGUARDANDO'
                  CHECK (status IN ('AGUARDANDO','TRANSPLANTADO','SUSPENSO','OBITO')),
    FOREIGN KEY (id_receptor)   REFERENCES receptor(id_receptor) ON DELETE CASCADE,
    FOREIGN KEY (id_tipo_orgao) REFERENCES tipo_orgao(id_tipo_orgao),
    UNIQUE (id_receptor, id_tipo_orgao)
);

-- Transplante efetivado: liga um orgao a um receptor (1:1 com o orgao)
CREATE TABLE transplante (
    id_transplante INTEGER PRIMARY KEY AUTOINCREMENT,
    id_orgao       INTEGER NOT NULL UNIQUE,
    id_receptor    INTEGER NOT NULL,
    id_hospital    INTEGER NOT NULL,
    data_cirurgia  TEXT    NOT NULL,
    cirurgiao      TEXT,
    resultado      TEXT    NOT NULL DEFAULT 'EM_ACOMPANHAMENTO'
                   CHECK (resultado IN ('SUCESSO','REJEICAO','OBITO','EM_ACOMPANHAMENTO')),
    FOREIGN KEY (id_orgao)    REFERENCES orgao_disponivel(id_orgao),
    FOREIGN KEY (id_receptor) REFERENCES receptor(id_receptor),
    FOREIGN KEY (id_hospital) REFERENCES hospital(id_hospital)
);

-- Regras de compatibilidade como tabelas de dominio: permitem resolver a
-- compatibilidade dentro do proprio SQL, sem logica na aplicacao.
CREATE TABLE compat_abo (
    abo_doador   TEXT NOT NULL CHECK (abo_doador   IN ('A','B','AB','O')),
    abo_receptor TEXT NOT NULL CHECK (abo_receptor IN ('A','B','AB','O')),
    PRIMARY KEY (abo_doador, abo_receptor)
);

CREATE TABLE compat_rh (
    rh_doador   TEXT NOT NULL CHECK (rh_doador   IN ('+','-')),
    rh_receptor TEXT NOT NULL CHECK (rh_receptor IN ('+','-')),
    PRIMARY KEY (rh_doador, rh_receptor)
);

CREATE INDEX idx_orgao_status ON orgao_disponivel (status, id_tipo_orgao);
CREATE INDEX idx_fila_status  ON fila_espera      (status, id_tipo_orgao, prioridade);

-- ----------------------------------------------------------------------------
-- 3. INSERCAO DE DADOS
-- ----------------------------------------------------------------------------

-- 3.1 Regras de compatibilidade sanguinea (doador -> receptor)
--     O doa para todos | A doa para A e AB | B doa para B e AB | AB doa para AB
INSERT INTO compat_abo (abo_doador, abo_receptor) VALUES
    ('O','O'), ('O','A'), ('O','B'), ('O','AB'),
    ('A','A'), ('A','AB'),
    ('B','B'), ('B','AB'),
    ('AB','AB');

-- RH negativo doa para ambos | RH positivo doa somente para positivo
INSERT INTO compat_rh (rh_doador, rh_receptor) VALUES
    ('-','-'), ('-','+'), ('+','+');

INSERT INTO hospital (nome, cidade, uf, cnes) VALUES
    ('Hospital Geral de Fortaleza',   'Fortaleza', 'CE', '2481286'),
    ('Hospital Universitario Walter', 'Fortaleza', 'CE', '2561573'),
    ('Instituto do Coracao',          'Sao Paulo', 'SP', '2077485'),
    ('Hospital das Clinicas Recife',  'Recife',    'PE', '0000396');

INSERT INTO tipo_orgao (nome, tempo_isquemia_horas) VALUES
    ('Coracao', 4),
    ('Pulmao',  6),
    ('Figado',  12),
    ('Rim',     24),
    ('Pancreas',12),
    ('Cornea',  168);

INSERT INTO doador (nome, cpf, data_nascimento, tipo_sanguineo, fator_rh, tipo_doador, id_hospital, data_registro) VALUES
    ('Roberto Alves',     '900.111.111-11', '1980-04-22', 'O',  '-', 'FALECIDO', 1, '2025-09-28'),
    ('Fernanda Gomes',    '900.222.222-22', '1975-12-05', 'A',  '+', 'FALECIDO', 2, '2025-10-01'),
    ('Marcos Vinicius',   '900.333.333-33', '1990-06-17', 'B',  '+', 'VIVO',     1, '2025-08-14'),
    ('Juliana Castro',    '900.444.444-44', '1988-02-28', 'AB', '+', 'FALECIDO', 3, '2025-10-05'),
    ('Paulo Cesar Dias',  '900.555.555-55', '1965-07-09', 'O',  '+', 'FALECIDO', 4, '2025-10-08'),
    ('Helena Barbosa',    '900.666.666-66', '1995-03-03', 'A',  '-', 'VIVO',     2, '2025-07-21');

INSERT INTO receptor (nome, cpf, data_nascimento, tipo_sanguineo, fator_rh, id_hospital, contato) VALUES
    ('Pedro Nogueira',    '800.111.111-11', '1970-01-15', 'A',  '+', 1, '(85) 97777-1111'),
    ('Sofia Mendes',      '800.222.222-22', '1983-05-27', 'O',  '-', 1, '(85) 97777-2222'),
    ('Gabriel Teixeira',  '800.333.333-33', '2005-09-12', 'AB', '+', 2, '(85) 97777-3333'),
    ('Rita de Cassia',    '800.444.444-44', '1958-11-30', 'B',  '+', 3, '(11) 97777-4444'),
    ('Thiago Moreira',    '800.555.555-55', '1992-08-08', 'O',  '+', 4, '(81) 97777-5555'),
    ('Camila Freitas',    '800.666.666-66', '2001-04-19', 'A',  '-', 2, '(85) 97777-6666'),
    ('Eduardo Pinheiro',  '800.777.777-77', '1966-02-02', 'B',  '-', 1, '(85) 97777-7777');

INSERT INTO orgao_disponivel (id_doador, id_tipo_orgao, id_hospital, data_captacao, status, observacao) VALUES
    (1, 4, 1, '2025-09-28 06:30', 'DISPONIVEL',    'Rim esquerdo'),
    (1, 3, 1, '2025-09-28 07:10', 'TRANSPLANTADO', 'Figado alocado em 29/09'),
    (2, 1, 2, '2025-10-01 22:40', 'DISPONIVEL',    'Coracao - prioridade de tempo'),
    (2, 4, 2, '2025-10-01 23:15', 'DISPONIVEL',    'Rim direito'),
    (3, 4, 1, '2025-08-14 09:00', 'TRANSPLANTADO', 'Doacao entre vivos (irmao)'),
    (4, 3, 3, '2025-10-05 15:20', 'DISPONIVEL',    NULL),
    (4, 6, 3, '2025-10-05 16:00', 'DISPONIVEL',    'Par de corneas'),
    (5, 2, 4, '2025-10-08 03:45', 'RESERVADO',     'Aguardando confirmacao de equipe'),
    (5, 4, 4, '2025-10-08 04:20', 'DISPONIVEL',    NULL),
    (6, 3, 2, '2025-07-21 10:00', 'DESCARTADO',    'Inviabilidade detectada na avaliacao');

INSERT INTO fila_espera (id_receptor, id_tipo_orgao, prioridade, data_entrada, status) VALUES
    (1, 4, 'ALTA',       '2024-03-11', 'AGUARDANDO'),
    (1, 5, 'NORMAL',     '2024-03-11', 'AGUARDANDO'),
    (2, 3, 'EMERGENCIA', '2025-01-20', 'AGUARDANDO'),
    (3, 1, 'EMERGENCIA', '2025-02-14', 'AGUARDANDO'),
    (3, 2, 'ALTA',       '2025-02-14', 'AGUARDANDO'),
    (4, 4, 'NORMAL',     '2023-10-02', 'AGUARDANDO'),
    (5, 4, 'ALTA',       '2024-07-19', 'AGUARDANDO'),
    (6, 6, 'NORMAL',     '2025-05-30', 'AGUARDANDO'),
    (7, 3, 'ALTA',       '2024-12-01', 'TRANSPLANTADO');

INSERT INTO transplante (id_orgao, id_receptor, id_hospital, data_cirurgia, cirurgiao, resultado) VALUES
    (2, 7, 1, '2025-09-29 02:00', 'Dr. Leandro Prado',  'EM_ACOMPANHAMENTO'),
    (5, 4, 1, '2025-08-14 14:30', 'Dra. Vanessa Luz',   'SUCESSO');

-- ----------------------------------------------------------------------------
-- 4. VIEWS DE APOIO
-- ----------------------------------------------------------------------------

-- Cruzamento doador x receptor: mesmo orgao + ABO e RH compativeis.
-- E o coracao do sistema: a compatibilidade e resolvida em SQL puro.
CREATE VIEW vw_compatibilidade AS
SELECT
    o.id_orgao,
    t.nome                                  AS orgao,
    d.nome                                  AS doador,
    d.tipo_sanguineo || d.fator_rh          AS sangue_doador,
    ho.nome                                 AS hospital_orgao,
    o.data_captacao,
    f.id_fila,
    r.id_receptor,
    r.nome                                  AS receptor,
    r.tipo_sanguineo || r.fator_rh          AS sangue_receptor,
    f.prioridade,
    f.data_entrada,
    hr.nome                                 AS hospital_receptor,
    CAST(julianday('now') - julianday(f.data_entrada) AS INTEGER) AS dias_na_fila
FROM orgao_disponivel o
JOIN doador      d  ON d.id_doador     = o.id_doador
JOIN tipo_orgao  t  ON t.id_tipo_orgao = o.id_tipo_orgao
JOIN hospital    ho ON ho.id_hospital  = o.id_hospital
JOIN fila_espera f  ON f.id_tipo_orgao = o.id_tipo_orgao
JOIN receptor    r  ON r.id_receptor   = f.id_receptor
JOIN hospital    hr ON hr.id_hospital  = r.id_hospital
JOIN compat_abo ca  ON ca.abo_doador = d.tipo_sanguineo AND ca.abo_receptor = r.tipo_sanguineo
JOIN compat_rh  cr  ON cr.rh_doador  = d.fator_rh       AND cr.rh_receptor  = r.fator_rh
WHERE o.status = 'DISPONIVEL'
  AND f.status = 'AGUARDANDO';

-- Fila de espera com os dados do receptor e do orgao aguardado
CREATE VIEW vw_fila_detalhada AS
SELECT
    f.id_fila,
    r.nome                         AS receptor,
    r.tipo_sanguineo || r.fator_rh AS sangue,
    t.nome                         AS orgao,
    f.prioridade,
    f.data_entrada,
    CAST(julianday('now') - julianday(f.data_entrada) AS INTEGER) AS dias_na_fila,
    f.status,
    h.nome                         AS hospital
FROM fila_espera f
JOIN receptor   r ON r.id_receptor   = f.id_receptor
JOIN tipo_orgao t ON t.id_tipo_orgao = f.id_tipo_orgao
JOIN hospital   h ON h.id_hospital   = r.id_hospital;

-- =============================================================================
-- 5. EXEMPLOS DE CONSULTA E ATUALIZACAO
-- =============================================================================

-- 5.1 Orgaos disponiveis com o doador de origem
-- SELECT o.id_orgao, t.nome AS orgao, d.nome AS doador,
--        d.tipo_sanguineo || d.fator_rh AS sangue, o.data_captacao, h.nome AS hospital
-- FROM orgao_disponivel o
-- JOIN tipo_orgao t ON t.id_tipo_orgao = o.id_tipo_orgao
-- JOIN doador     d ON d.id_doador     = o.id_doador
-- JOIN hospital   h ON h.id_hospital   = o.id_hospital
-- WHERE o.status = 'DISPONIVEL';

-- 5.2 Fila ordenada por prioridade e tempo de espera
-- SELECT * FROM vw_fila_detalhada WHERE status = 'AGUARDANDO'
-- ORDER BY CASE prioridade WHEN 'EMERGENCIA' THEN 1 WHEN 'ALTA' THEN 2 ELSE 3 END,
--          data_entrada;

-- 5.3 Receptores compativeis com um orgao especifico
-- SELECT receptor, sangue_receptor, prioridade, dias_na_fila, hospital_receptor
-- FROM vw_compatibilidade WHERE id_orgao = 1
-- ORDER BY CASE prioridade WHEN 'EMERGENCIA' THEN 1 WHEN 'ALTA' THEN 2 ELSE 3 END,
--          dias_na_fila DESC;

-- 5.4 Quantos candidatos compativeis existem por orgao disponivel
-- SELECT orgao, sangue_doador, COUNT(*) AS candidatos
-- FROM vw_compatibilidade GROUP BY id_orgao ORDER BY candidatos DESC;

-- 5.5 Receptores aguardando sem nenhum orgao compativel hoje (NOT IN)
-- SELECT receptor, sangue, orgao, dias_na_fila FROM vw_fila_detalhada
-- WHERE status = 'AGUARDANDO'
--   AND id_fila NOT IN (SELECT id_fila FROM vw_compatibilidade);

-- 5.6 Atualizacao: reservar um orgao
-- UPDATE orgao_disponivel SET status = 'RESERVADO' WHERE id_orgao = 1;

-- 5.7 Atualizacao: elevar a prioridade de um paciente na fila
-- UPDATE fila_espera SET prioridade = 'EMERGENCIA' WHERE id_fila = 6;

-- 5.8 Atualizacao: registrar o desfecho de um transplante
-- UPDATE transplante SET resultado = 'SUCESSO' WHERE id_transplante = 1;
