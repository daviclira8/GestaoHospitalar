-- =============================================================================
-- SISTEMA 1 - DIARIO DE SAUDE PESSOAL
-- SGBD: SQLite 3
-- Objetivo: organizar o historico de saude dos usuarios (tipo sanguineo,
--           fator RH, alergias, consultas, exames e vacinas).
--
-- MODELO LOGICO (resumo do DER - ver docs/DER.md)
--   USUARIO (1,N) ---- (1,1) CONSULTA (1,1) ---- (1,N) PROFISSIONAL
--   USUARIO (1,N) ---- (1,1) EXAME        (exame pode nascer de uma CONSULTA)
--   USUARIO (1,N) ---- (1,1) VACINACAO (1,1) --- (1,N) VACINA
--   USUARIO (N,N) ---- USUARIO_ALERGIA ---- (N,N) ALERGIA
-- =============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1. REMOCAO DAS TABELAS (ordem inversa das dependencias)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS vacinacao;
DROP TABLE IF EXISTS exame;
DROP TABLE IF EXISTS consulta;
DROP TABLE IF EXISTS usuario_alergia;
DROP TABLE IF EXISTS vacina;
DROP TABLE IF EXISTS alergia;
DROP TABLE IF EXISTS profissional;
DROP TABLE IF EXISTS usuario;

-- ----------------------------------------------------------------------------
-- 2. CRIACAO DAS TABELAS
-- ----------------------------------------------------------------------------

-- Entidade forte: dono do diario de saude
CREATE TABLE usuario (
    id_usuario      INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT    NOT NULL,
    cpf             TEXT    NOT NULL UNIQUE,
    data_nascimento TEXT    NOT NULL,                       -- YYYY-MM-DD
    sexo            TEXT    CHECK (sexo IN ('M','F','O')),
    tipo_sanguineo  TEXT    NOT NULL CHECK (tipo_sanguineo IN ('A','B','AB','O')),
    fator_rh        TEXT    NOT NULL CHECK (fator_rh IN ('+','-')),
    telefone        TEXT,
    email           TEXT
);

-- Medico / enfermeiro que atende as consultas
CREATE TABLE profissional (
    id_profissional INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT NOT NULL,
    especialidade   TEXT NOT NULL,
    registro        TEXT NOT NULL UNIQUE                    -- CRM / COREN
);

-- Catalogo de alergias (reaproveitado por varios usuarios)
CREATE TABLE alergia (
    id_alergia INTEGER PRIMARY KEY AUTOINCREMENT,
    nome       TEXT NOT NULL UNIQUE,
    categoria  TEXT NOT NULL CHECK (categoria IN ('MEDICAMENTO','ALIMENTO','AMBIENTAL','OUTRO'))
);

-- Tabela associativa N:N entre usuario e alergia (com atributos proprios)
CREATE TABLE usuario_alergia (
    id_usuario   INTEGER NOT NULL,
    id_alergia   INTEGER NOT NULL,
    gravidade    TEXT    NOT NULL CHECK (gravidade IN ('LEVE','MODERADA','GRAVE')),
    data_registro TEXT   NOT NULL DEFAULT (date('now')),
    observacao   TEXT,
    PRIMARY KEY (id_usuario, id_alergia),
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)   ON DELETE CASCADE,
    FOREIGN KEY (id_alergia) REFERENCES alergia(id_alergia)   ON DELETE CASCADE
);

-- Catalogo de vacinas
CREATE TABLE vacina (
    id_vacina           INTEGER PRIMARY KEY AUTOINCREMENT,
    nome                TEXT NOT NULL UNIQUE,
    doses_recomendadas  INTEGER NOT NULL DEFAULT 1 CHECK (doses_recomendadas > 0),
    fabricante          TEXT
);

-- Consultas realizadas pelo usuario
CREATE TABLE consulta (
    id_consulta     INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario      INTEGER NOT NULL,
    id_profissional INTEGER NOT NULL,
    data_hora       TEXT    NOT NULL,                       -- YYYY-MM-DD HH:MM
    motivo          TEXT    NOT NULL,
    diagnostico     TEXT,
    prescricao      TEXT,
    FOREIGN KEY (id_usuario)      REFERENCES usuario(id_usuario)           ON DELETE CASCADE,
    FOREIGN KEY (id_profissional) REFERENCES profissional(id_profissional)
);

-- Exames; podem ou nao estar vinculados a uma consulta (FK opcional)
CREATE TABLE exame (
    id_exame         INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario       INTEGER NOT NULL,
    id_consulta      INTEGER,
    tipo             TEXT    NOT NULL,
    data_realizacao  TEXT    NOT NULL,
    laboratorio      TEXT,
    resultado        TEXT,
    status           TEXT    NOT NULL DEFAULT 'PENDENTE'
                     CHECK (status IN ('PENDENTE','CONCLUIDO','CANCELADO')),
    FOREIGN KEY (id_usuario)  REFERENCES usuario(id_usuario)   ON DELETE CASCADE,
    FOREIGN KEY (id_consulta) REFERENCES consulta(id_consulta) ON DELETE SET NULL
);

-- Aplicacao de doses de vacina (historico ao longo do tempo)
CREATE TABLE vacinacao (
    id_vacinacao     INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario       INTEGER NOT NULL,
    id_vacina        INTEGER NOT NULL,
    dose             INTEGER NOT NULL DEFAULT 1 CHECK (dose > 0),
    data_aplicacao   TEXT    NOT NULL,
    lote             TEXT,
    local_aplicacao  TEXT,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_vacina)  REFERENCES vacina(id_vacina),
    UNIQUE (id_usuario, id_vacina, dose)
);

-- Indices de apoio as consultas mais frequentes
CREATE INDEX idx_consulta_usuario  ON consulta  (id_usuario, data_hora);
CREATE INDEX idx_exame_usuario     ON exame     (id_usuario, data_realizacao);
CREATE INDEX idx_vacinacao_usuario ON vacinacao (id_usuario, data_aplicacao);

-- ----------------------------------------------------------------------------
-- 3. INSERCAO DE DADOS FICTICIOS
-- ----------------------------------------------------------------------------
INSERT INTO usuario (nome, cpf, data_nascimento, sexo, tipo_sanguineo, fator_rh, telefone, email) VALUES
    ('Ana Beatriz Souza',   '111.111.111-11', '1992-03-14', 'F', 'O',  '-', '(85) 98888-1111', 'ana.souza@email.com'),
    ('Carlos Henrique Lima','222.222.222-22', '1985-11-02', 'M', 'A',  '+', '(85) 98888-2222', 'carlos.lima@email.com'),
    ('Mariana Rocha',       '333.333.333-33', '2000-07-25', 'F', 'AB', '+', '(85) 98888-3333', 'mariana.rocha@email.com'),
    ('Joao Victor Benevides','444.444.444-44','1998-01-09', 'M', 'B',  '-', '(85) 98888-4444', 'joao.benevides@email.com'),
    ('Luiza Martins',       '555.555.555-55', '1976-09-30', 'F', 'O',  '+', '(85) 98888-5555', 'luiza.martins@email.com');

INSERT INTO profissional (nome, especialidade, registro) VALUES
    ('Dr. Rafael Andrade',  'Clinica Geral',  'CRM-CE 12345'),
    ('Dra. Patricia Nunes', 'Cardiologia',    'CRM-CE 23456'),
    ('Dr. Mateus Oliveira', 'Endocrinologia', 'CRM-CE 34567'),
    ('Enf. Sandra Pereira', 'Enfermagem',     'COREN-CE 45678');

INSERT INTO alergia (nome, categoria) VALUES
    ('Penicilina',   'MEDICAMENTO'),
    ('Dipirona',     'MEDICAMENTO'),
    ('Lactose',      'ALIMENTO'),
    ('Camarao',      'ALIMENTO'),
    ('Poeira',       'AMBIENTAL'),
    ('Latex',        'OUTRO');

INSERT INTO usuario_alergia (id_usuario, id_alergia, gravidade, data_registro, observacao) VALUES
    (1, 1, 'GRAVE',    '2015-05-20', 'Reacao anafilatica em 2015; usar pulseira de alerta'),
    (1, 5, 'LEVE',     '2018-02-10', 'Rinite sazonal'),
    (2, 3, 'MODERADA', '2019-08-01', 'Intolerancia confirmada por exame'),
    (3, 4, 'GRAVE',    '2021-11-15', 'Edema de glote; portar adrenalina'),
    (4, 2, 'MODERADA', '2020-01-30', 'Urticaria apos uso injetavel'),
    (5, 6, 'LEVE',     '2017-06-05', 'Dermatite de contato com luvas');

INSERT INTO vacina (nome, doses_recomendadas, fabricante) VALUES
    ('Hepatite B',  3, 'Butantan'),
    ('Influenza',   1, 'Butantan'),
    ('COVID-19',    2, 'Fiocruz'),
    ('Tetano (dT)', 3, 'Butantan'),
    ('Febre Amarela',1,'Bio-Manguinhos');

INSERT INTO consulta (id_usuario, id_profissional, data_hora, motivo, diagnostico, prescricao) VALUES
    (1, 1, '2025-02-10 09:00', 'Dor de cabeca recorrente', 'Cefaleia tensional',        'Analgesico 500mg 8/8h por 3 dias'),
    (1, 2, '2025-06-18 14:30', 'Check-up cardiologico',    'Sem alteracoes',            'Retorno anual'),
    (2, 3, '2025-03-05 10:15', 'Cansaco e sede excessiva', 'Pre-diabetes',              'Dieta + metformina 500mg'),
    (2, 1, '2025-09-22 08:45', 'Retorno endocrino',        'Glicemia controlada',       'Manter dieta'),
    (3, 1, '2025-04-12 16:00', 'Crise alergica',           'Alergia alimentar (camarao)','Anti-histaminico; evitar frutos do mar'),
    (4, 2, '2025-07-30 11:00', 'Palpitacoes',              'Arritmia leve',             'Holter 24h'),
    (5, 1, '2025-08-14 09:30', 'Dor lombar',               'Lombalgia mecanica',        'Fisioterapia 10 sessoes');

INSERT INTO exame (id_usuario, id_consulta, tipo, data_realizacao, laboratorio, resultado, status) VALUES
    (1, 1,    'Hemograma completo',  '2025-02-12', 'Lab Vida',     'Serie vermelha e branca normais', 'CONCLUIDO'),
    (1, 2,    'Eletrocardiograma',   '2025-06-19', 'Clinica Coracao','Ritmo sinusal normal',          'CONCLUIDO'),
    (2, 3,    'Glicemia de jejum',   '2025-03-06', 'Lab Vida',     '118 mg/dL (alterado)',            'CONCLUIDO'),
    (2, 4,    'Hemoglobina glicada', '2025-09-23', 'Lab Vida',     '5.9% (limite)',                   'CONCLUIDO'),
    (3, NULL, 'IgE especifica',      '2025-04-20', 'Lab Alergo',   'Positivo para crustaceos',        'CONCLUIDO'),
    (4, 6,    'Holter 24h',          '2025-08-02', 'Clinica Coracao', NULL,                           'PENDENTE'),
    (5, 7,    'Raio-X lombar',       '2025-08-15', 'Imagem Center','Discreta escoliose',              'CONCLUIDO');

INSERT INTO vacinacao (id_usuario, id_vacina, dose, data_aplicacao, lote, local_aplicacao) VALUES
    (1, 1, 1, '2010-03-10', 'HB-2010A', 'UBS Centro'),
    (1, 1, 2, '2010-04-12', 'HB-2010B', 'UBS Centro'),
    (1, 1, 3, '2010-09-15', 'HB-2010C', 'UBS Centro'),
    (1, 3, 1, '2021-06-01', 'CV-21X',   'Posto Drive-thru'),
    (1, 3, 2, '2021-09-05', 'CV-21Y',   'Posto Drive-thru'),
    (1, 2, 1, '2025-04-02', 'INF-25',   'UBS Centro'),
    (2, 3, 1, '2021-05-20', 'CV-21A',   'UBS Aldeota'),
    (2, 3, 2, '2021-08-22', 'CV-21B',   'UBS Aldeota'),
    (2, 4, 1, '2019-02-11', 'DT-19',    'UBS Aldeota'),
    (3, 5, 1, '2022-01-18', 'FA-22',    'UBS Messejana'),
    (3, 2, 1, '2025-05-09', 'INF-25',   'UBS Messejana'),
    (4, 1, 1, '2012-07-07', 'HB-2012',  'UBS Parangaba'),
    (5, 2, 1, '2025-03-28', 'INF-25',   'UBS Centro'),
    (5, 4, 1, '2016-10-10', 'DT-16',    'UBS Centro');

-- =============================================================================
-- 4. EXEMPLOS DE CONSULTA (SELECT) E ATUALIZACAO (UPDATE)
--    Os mesmos comandos sao executados pelos menus do terminal e pela GUI.
-- =============================================================================

-- 4.1 Ficha do usuario com tipo sanguineo completo
-- SELECT nome, tipo_sanguineo || fator_rh AS sangue, data_nascimento
-- FROM usuario ORDER BY nome;

-- 4.2 Historico de consultas de um usuario (JOIN com profissional)
-- SELECT c.data_hora, p.nome AS profissional, p.especialidade, c.motivo, c.diagnostico
-- FROM consulta c JOIN profissional p ON p.id_profissional = c.id_profissional
-- WHERE c.id_usuario = 1 ORDER BY c.data_hora DESC;

-- 4.3 Alergias e gravidade (N:N)
-- SELECT u.nome, a.nome AS alergia, a.categoria, ua.gravidade
-- FROM usuario_alergia ua
-- JOIN usuario u ON u.id_usuario = ua.id_usuario
-- JOIN alergia a ON a.id_alergia = ua.id_alergia
-- WHERE ua.gravidade = 'GRAVE';

-- 4.4 Carteira de vacinacao com doses faltantes (agregacao + HAVING)
-- SELECT u.nome, v.nome AS vacina, COUNT(*) AS aplicadas, v.doses_recomendadas,
--        v.doses_recomendadas - COUNT(*) AS faltam
-- FROM vacinacao vc
-- JOIN usuario u ON u.id_usuario = vc.id_usuario
-- JOIN vacina  v ON v.id_vacina  = vc.id_vacina
-- GROUP BY u.id_usuario, v.id_vacina
-- HAVING COUNT(*) < v.doses_recomendadas;

-- 4.5 Exames pendentes (LEFT JOIN com consulta de origem)
-- SELECT e.tipo, e.data_realizacao, u.nome, c.motivo AS consulta_origem
-- FROM exame e
-- JOIN usuario u ON u.id_usuario = e.id_usuario
-- LEFT JOIN consulta c ON c.id_consulta = e.id_consulta
-- WHERE e.status = 'PENDENTE';

-- 4.6 Atualizacao: lancar o resultado de um exame pendente
-- UPDATE exame SET resultado = 'Extrassistoles isoladas', status = 'CONCLUIDO'
-- WHERE id_exame = 6;

-- 4.7 Atualizacao: corrigir contato do usuario
-- UPDATE usuario SET telefone = '(85) 99999-0000' WHERE id_usuario = 3;
