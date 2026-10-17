DROP VIEW     IF EXISTS vw_processos            CASCADE;
DROP VIEW     IF EXISTS vw_orgaos_disponiveis   CASCADE;
DROP VIEW     IF EXISTS vw_fila_ativa           CASCADE;
DROP TABLE    IF EXISTS alocacao                CASCADE;
DROP TABLE    IF EXISTS fila_espera             CASCADE;
DROP TABLE    IF EXISTS receptor                CASCADE;
DROP TABLE    IF EXISTS orgao_disponivel        CASCADE;
DROP TABLE    IF EXISTS doador                  CASCADE;
DROP TABLE    IF EXISTS bolsa_sangue            CASCADE;
DROP TABLE    IF EXISTS tipo_orgao              CASCADE;
DROP TABLE    IF EXISTS hospital                CASCADE;
DROP TABLE    IF EXISTS compatibilidade_abo     CASCADE;
DROP FUNCTION IF EXISTS fn_distancia_km         CASCADE;
DROP FUNCTION IF EXISTS fn_modal_transporte     CASCADE;
DROP FUNCTION IF EXISTS fn_tempo_transporte_h   CASCADE;
DROP FUNCTION IF EXISTS fn_abo_compativel       CASCADE;
DROP FUNCTION IF EXISTS fn_sangue_compativel    CASCADE;
DROP FUNCTION IF EXISTS fn_candidatos_orgao     CASCADE;
DROP FUNCTION IF EXISTS fn_alocar_orgao         CASCADE;
DROP FUNCTION IF EXISTS fn_registrar_entrega    CASCADE;
DROP FUNCTION IF EXISTS fn_concluir_transplante CASCADE;
DROP FUNCTION IF EXISTS fn_cancelar_alocacao    CASCADE;
DROP FUNCTION IF EXISTS fn_descartar_orgaos_expirados CASCADE;
DROP FUNCTION IF EXISTS fn_atualizar_bolsas_vencidas  CASCADE;
DROP FUNCTION IF EXISTS fn_valida_orgao         CASCADE;
DROP TYPE     IF EXISTS tipo_sanguineo          CASCADE;
DROP TYPE     IF EXISTS fator_rh                CASCADE;
DROP TYPE     IF EXISTS tipo_doador             CASCADE;
DROP TYPE     IF EXISTS status_doador           CASCADE;
DROP TYPE     IF EXISTS status_orgao            CASCADE;
DROP TYPE     IF EXISTS status_fila             CASCADE;
DROP TYPE     IF EXISTS status_logistica        CASCADE;
DROP TYPE     IF EXISTS status_bolsa            CASCADE;

CREATE TYPE tipo_doador      AS ENUM ('vivo', 'falecido');
CREATE TYPE status_doador    AS ENUM ('apto', 'inapto');
CREATE TYPE status_orgao     AS ENUM ('disponivel', 'alocado', 'descartado');
CREATE TYPE status_fila      AS ENUM ('aguardando', 'transplantado', 'removido');
CREATE TYPE status_logistica AS ENUM ('em_transporte', 'entregue', 'realizado', 'cancelado');
CREATE TYPE status_bolsa     AS ENUM ('disponivel', 'utilizada', 'vencida');
CREATE TYPE tipo_sanguineo   AS ENUM ('A', 'B', 'AB', 'O');
CREATE TYPE fator_rh         AS ENUM ('positivo', 'negativo');

CREATE TABLE hospital (
    id         SERIAL        PRIMARY KEY,
    nome       VARCHAR(120)  NOT NULL UNIQUE,
    cidade     VARCHAR(80)   NOT NULL,
    uf         CHAR(2)       NOT NULL CHECK (uf ~ '^[A-Z]{2}$'),
    latitude   NUMERIC(9,6)  NOT NULL CHECK (latitude  BETWEEN  -90 AND  90),
    longitude  NUMERIC(9,6)  NOT NULL CHECK (longitude BETWEEN -180 AND 180)
);

CREATE TABLE tipo_orgao (
    id                        SERIAL       PRIMARY KEY,
    nome                      VARCHAR(50)  NOT NULL UNIQUE,
    tempo_max_isquemia_horas  INT          NOT NULL CHECK (tempo_max_isquemia_horas > 0),
    permite_doador_vivo       BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE TABLE doador (
    id             SERIAL         PRIMARY KEY,
    usuario_id     INT            NOT NULL UNIQUE,
    tipo           tipo_doador    NOT NULL,
    hospital_id    INT            NOT NULL REFERENCES hospital(id),
    data_cadastro  DATE           NOT NULL DEFAULT CURRENT_DATE,
    status         status_doador  NOT NULL DEFAULT 'apto'
);

CREATE TABLE orgao_disponivel (
    id                  SERIAL        PRIMARY KEY,
    doador_id           INT           NOT NULL REFERENCES doador(id),
    tipo_orgao_id       INT           NOT NULL REFERENCES tipo_orgao(id),
    hospital_id         INT           NOT NULL REFERENCES hospital(id),
    data_hora_captacao  TIMESTAMP     NOT NULL DEFAULT NOW(),
    status              status_orgao  NOT NULL DEFAULT 'disponivel'
);

CREATE TABLE receptor (
    id             SERIAL  PRIMARY KEY,
    usuario_id     INT     NOT NULL UNIQUE,
    hospital_id    INT     NOT NULL REFERENCES hospital(id),
    data_cadastro  DATE    NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE fila_espera (
    id             SERIAL       PRIMARY KEY,
    receptor_id    INT          NOT NULL REFERENCES receptor(id),
    tipo_orgao_id  INT          NOT NULL REFERENCES tipo_orgao(id),
    data_entrada   TIMESTAMP    NOT NULL DEFAULT NOW(),
    urgencia       INT          NOT NULL CHECK (urgencia BETWEEN 1 AND 5),
    status         status_fila  NOT NULL DEFAULT 'aguardando'
);
CREATE UNIQUE INDEX uq_fila_ativa ON fila_espera (receptor_id, tipo_orgao_id)
    WHERE status = 'aguardando';

CREATE TABLE alocacao (
    id                SERIAL            PRIMARY KEY,
    orgao_id          INT               NOT NULL REFERENCES orgao_disponivel(id),
    fila_id           INT               NOT NULL REFERENCES fila_espera(id),
    data_hora         TIMESTAMP         NOT NULL DEFAULT NOW(),
    status_logistica  status_logistica  NOT NULL DEFAULT 'em_transporte'
);
CREATE UNIQUE INDEX uq_alocacao_orgao ON alocacao (orgao_id) WHERE status_logistica <> 'cancelado';
CREATE UNIQUE INDEX uq_alocacao_fila  ON alocacao (fila_id)  WHERE status_logistica <> 'cancelado';

CREATE TABLE bolsa_sangue (
    id             SERIAL        PRIMARY KEY,
    usuario_id     INT           NOT NULL,
    hospital_id    INT           NOT NULL REFERENCES hospital(id),
    data_coleta    DATE          NOT NULL DEFAULT CURRENT_DATE,
    data_validade  DATE          NOT NULL,
    volume_ml      INT           NOT NULL CHECK (volume_ml BETWEEN 200 AND 600),
    status         status_bolsa  NOT NULL DEFAULT 'disponivel',
    CONSTRAINT ck_validade CHECK (data_validade > data_coleta)
);

CREATE TABLE compatibilidade_abo (
    tipo_doador    tipo_sanguineo NOT NULL,
    tipo_receptor  tipo_sanguineo NOT NULL,
    PRIMARY KEY (tipo_doador, tipo_receptor)
);
INSERT INTO compatibilidade_abo VALUES
('O','O'), ('O','A'), ('O','B'), ('O','AB'),
('A','A'), ('A','AB'),
('B','B'), ('B','AB'),
('AB','AB');

CREATE INDEX idx_doador_hospital   ON doador(hospital_id);
CREATE INDEX idx_orgao_status      ON orgao_disponivel(status, tipo_orgao_id);
CREATE INDEX idx_orgao_doador      ON orgao_disponivel(doador_id);
CREATE INDEX idx_receptor_hospital ON receptor(hospital_id);
CREATE INDEX idx_fila_ordem        ON fila_espera(tipo_orgao_id, status, urgencia DESC, data_entrada);
CREATE INDEX idx_bolsa_status      ON bolsa_sangue(status, hospital_id);
CREATE INDEX idx_bolsa_usuario     ON bolsa_sangue(usuario_id);

CREATE FUNCTION fn_distancia_km(lat1 NUMERIC, lon1 NUMERIC, lat2 NUMERIC, lon2 NUMERIC)
RETURNS NUMERIC LANGUAGE sql IMMUTABLE AS $$
    SELECT ROUND((6371 * 2 * ASIN(SQRT(
             POWER(SIN(RADIANS(lat2 - lat1) / 2), 2) +
             COS(RADIANS(lat1)) * COS(RADIANS(lat2)) *
             POWER(SIN(RADIANS(lon2 - lon1) / 2), 2))))::NUMERIC, 1);
$$;

CREATE FUNCTION fn_modal_transporte(dist_km NUMERIC)
RETURNS TEXT LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE WHEN dist_km = 0    THEN 'mesmo hospital'
                WHEN dist_km <= 150 THEN 'terrestre'
                ELSE 'aéreo' END;
$$;

CREATE FUNCTION fn_tempo_transporte_h(dist_km NUMERIC)
RETURNS NUMERIC LANGUAGE sql IMMUTABLE AS $$
    SELECT ROUND(1 + CASE WHEN dist_km <= 150 THEN dist_km / 60.0
                          ELSE dist_km / 400.0 END, 2);
$$;

CREATE FUNCTION fn_abo_compativel(p_doador tipo_sanguineo, p_receptor tipo_sanguineo)
RETURNS BOOLEAN LANGUAGE sql STABLE AS $$
    SELECT EXISTS (SELECT 1 FROM compatibilidade_abo
                    WHERE tipo_doador = p_doador AND tipo_receptor = p_receptor);
$$;

CREATE FUNCTION fn_sangue_compativel(p_doador tipo_sanguineo, p_rh_doador fator_rh,
                                     p_receptor tipo_sanguineo, p_rh_receptor fator_rh)
RETURNS BOOLEAN LANGUAGE sql STABLE AS $$
    SELECT fn_abo_compativel(p_doador, p_receptor)
       AND (p_rh_receptor = 'positivo' OR p_rh_doador = 'negativo');
$$;

CREATE FUNCTION fn_candidatos_orgao(p_orgao_id INT)
RETURNS TABLE (
    fila_id               INT,
    receptor_id           INT,
    receptor_usuario_id   INT,
    doador_usuario_id     INT,
    hospital_receptor     VARCHAR,
    urgencia              INT,
    dias_espera           INT,
    distancia_km          NUMERIC,
    modal                 TEXT,
    tempo_transporte_h    NUMERIC,
    horas_restantes       NUMERIC,
    logisticamente_viavel BOOLEAN
) LANGUAGE sql STABLE AS $$
    WITH o AS (
        SELECT od.*, d.usuario_id AS doador_usuario_id, t.tempo_max_isquemia_horas,
               h.latitude, h.longitude,
               ROUND(EXTRACT(EPOCH FROM (od.data_hora_captacao
                     + t.tempo_max_isquemia_horas * INTERVAL '1 hour' - NOW())) / 3600, 2)
                   AS horas_restantes
          FROM orgao_disponivel od
          JOIN doador     d ON d.id = od.doador_id
          JOIN tipo_orgao t ON t.id = od.tipo_orgao_id
          JOIN hospital   h ON h.id = od.hospital_id
         WHERE od.id = p_orgao_id
    ), c AS (
        SELECT f.id AS fila_id, r.id AS receptor_id, r.usuario_id AS receptor_usuario_id,
               o.doador_usuario_id, hr.nome AS hospital_receptor, f.urgencia,
               (CURRENT_DATE - f.data_entrada::DATE) AS dias_espera,
               fn_distancia_km(o.latitude, o.longitude, hr.latitude, hr.longitude) AS distancia_km,
               o.horas_restantes, f.data_entrada
          FROM o
          JOIN fila_espera f  ON f.tipo_orgao_id = o.tipo_orgao_id
                             AND f.status = 'aguardando'
          JOIN receptor r     ON r.id = f.receptor_id
          JOIN hospital hr    ON hr.id = r.hospital_id
         WHERE o.status = 'disponivel'
           AND r.usuario_id <> o.doador_usuario_id
           AND NOT EXISTS (SELECT 1 FROM alocacao a
                            WHERE a.fila_id = f.id AND a.status_logistica <> 'cancelado')
    )
    SELECT fila_id, receptor_id, receptor_usuario_id, doador_usuario_id,
           hospital_receptor, urgencia, dias_espera, distancia_km,
           fn_modal_transporte(distancia_km),
           fn_tempo_transporte_h(distancia_km),
           horas_restantes,
           fn_tempo_transporte_h(distancia_km) <= horas_restantes
      FROM c
     ORDER BY urgencia DESC, data_entrada ASC, distancia_km ASC;
$$;

CREATE FUNCTION fn_alocar_orgao(p_orgao_id INT, p_fila_id INT)
RETURNS INT LANGUAGE plpgsql AS $$
DECLARE
    v_orgao  orgao_disponivel%ROWTYPE;
    v_fila   fila_espera%ROWTYPE;
    v_max_h  INT;
    v_id     INT;
BEGIN
    SELECT * INTO v_orgao FROM orgao_disponivel WHERE id = p_orgao_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'Órgão % não existe', p_orgao_id; END IF;
    IF v_orgao.status <> 'disponivel' THEN
        RAISE EXCEPTION 'Órgão % não está disponível (status: %)', p_orgao_id, v_orgao.status;
    END IF;

    SELECT * INTO v_fila FROM fila_espera WHERE id = p_fila_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'Fila % não existe', p_fila_id; END IF;
    IF v_fila.status <> 'aguardando' THEN
        RAISE EXCEPTION 'Receptor da fila % não está aguardando (status: %)', p_fila_id, v_fila.status;
    END IF;
    IF v_fila.tipo_orgao_id <> v_orgao.tipo_orgao_id THEN
        RAISE EXCEPTION 'Tipo de órgão incompatível com a fila %', p_fila_id;
    END IF;

    SELECT tempo_max_isquemia_horas INTO v_max_h FROM tipo_orgao WHERE id = v_orgao.tipo_orgao_id;
    IF NOW() > v_orgao.data_hora_captacao + v_max_h * INTERVAL '1 hour' THEN
        RAISE EXCEPTION 'Órgão % excedeu o tempo máximo de isquemia', p_orgao_id;
    END IF;

    INSERT INTO alocacao (orgao_id, fila_id) VALUES (p_orgao_id, p_fila_id)
    RETURNING id INTO v_id;

    UPDATE orgao_disponivel SET status = 'alocado' WHERE id = p_orgao_id;
    RETURN v_id;
END;
$$;

CREATE FUNCTION fn_registrar_entrega(p_alocacao_id INT)
RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    UPDATE alocacao SET status_logistica = 'entregue'
     WHERE id = p_alocacao_id AND status_logistica = 'em_transporte';
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Alocação % não está em transporte', p_alocacao_id;
    END IF;
END;
$$;

CREATE FUNCTION fn_concluir_transplante(p_alocacao_id INT)
RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE v_fila INT;
BEGIN
    UPDATE alocacao SET status_logistica = 'realizado'
     WHERE id = p_alocacao_id AND status_logistica IN ('em_transporte', 'entregue')
    RETURNING fila_id INTO v_fila;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Alocação % não pode ser concluída', p_alocacao_id;
    END IF;
    UPDATE fila_espera SET status = 'transplantado' WHERE id = v_fila;
END;
$$;

CREATE FUNCTION fn_cancelar_alocacao(p_alocacao_id INT)
RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE v_orgao INT;
BEGIN
    UPDATE alocacao SET status_logistica = 'cancelado'
     WHERE id = p_alocacao_id AND status_logistica IN ('em_transporte', 'entregue')
    RETURNING orgao_id INTO v_orgao;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Alocação % não pode ser cancelada', p_alocacao_id;
    END IF;
    UPDATE orgao_disponivel SET status = 'disponivel' WHERE id = v_orgao;
END;
$$;

CREATE FUNCTION fn_descartar_orgaos_expirados()
RETURNS INT LANGUAGE plpgsql AS $$
DECLARE n INT;
BEGIN
    UPDATE orgao_disponivel od SET status = 'descartado'
      FROM tipo_orgao t
     WHERE t.id = od.tipo_orgao_id
       AND od.status = 'disponivel'
       AND NOW() > od.data_hora_captacao + t.tempo_max_isquemia_horas * INTERVAL '1 hour';
    GET DIAGNOSTICS n = ROW_COUNT;
    RETURN n;
END;
$$;

CREATE FUNCTION fn_atualizar_bolsas_vencidas()
RETURNS INT LANGUAGE plpgsql AS $$
DECLARE n INT;
BEGIN
    UPDATE bolsa_sangue SET status = 'vencida'
     WHERE status = 'disponivel' AND data_validade < CURRENT_DATE;
    GET DIAGNOSTICS n = ROW_COUNT;
    RETURN n;
END;
$$;

CREATE FUNCTION fn_valida_orgao()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    v_doador doador%ROWTYPE;
    v_tipo   tipo_orgao%ROWTYPE;
BEGIN
    SELECT * INTO v_doador FROM doador     WHERE id = NEW.doador_id;
    SELECT * INTO v_tipo   FROM tipo_orgao WHERE id = NEW.tipo_orgao_id;

    IF v_doador.status = 'inapto' THEN
        RAISE EXCEPTION 'Doador % está INAPTO e não pode doar órgãos', NEW.doador_id;
    END IF;
    IF v_doador.tipo = 'vivo' AND NOT v_tipo.permite_doador_vivo THEN
        RAISE EXCEPTION 'O órgão "%" não pode ser doado por doador vivo', v_tipo.nome;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_valida_orgao
BEFORE INSERT ON orgao_disponivel
FOR EACH ROW EXECUTE FUNCTION fn_valida_orgao();

CREATE VIEW vw_fila_ativa AS
SELECT t.nome                                   AS orgao,
       ROW_NUMBER() OVER (PARTITION BY f.tipo_orgao_id
                          ORDER BY f.urgencia DESC, f.data_entrada) AS posicao,
       f.id                                     AS fila_id,
       r.usuario_id                             AS receptor_usuario_id,
       h.nome                                   AS hospital,
       h.uf,
       f.urgencia,
       f.data_entrada::DATE                     AS entrada,
       CURRENT_DATE - f.data_entrada::DATE      AS dias_espera
  FROM fila_espera f
  JOIN receptor   r ON r.id = f.receptor_id
  JOIN hospital   h ON h.id = r.hospital_id
  JOIN tipo_orgao t ON t.id = f.tipo_orgao_id
 WHERE f.status = 'aguardando'
   AND NOT EXISTS (SELECT 1 FROM alocacao a
                    WHERE a.fila_id = f.id AND a.status_logistica <> 'cancelado');

CREATE VIEW vw_orgaos_disponiveis AS
SELECT od.id                                     AS orgao_id,
       t.nome                                    AS orgao,
       d.usuario_id                              AS doador_usuario_id,
       d.tipo                                    AS tipo_doador,
       h.nome                                    AS hospital_origem,
       od.data_hora_captacao,
       od.data_hora_captacao + t.tempo_max_isquemia_horas * INTERVAL '1 hour' AS prazo_limite,
       ROUND(EXTRACT(EPOCH FROM (od.data_hora_captacao
             + t.tempo_max_isquemia_horas * INTERVAL '1 hour' - NOW())) / 3600, 1) AS horas_restantes
  FROM orgao_disponivel od
  JOIN tipo_orgao t ON t.id = od.tipo_orgao_id
  JOIN doador     d ON d.id = od.doador_id
  JOIN hospital   h ON h.id = od.hospital_id
 WHERE od.status = 'disponivel';

CREATE VIEW vw_processos AS
SELECT a.id                AS alocacao_id,
       t.nome              AS orgao,
       d.usuario_id        AS doador_usuario_id,
       r.usuario_id        AS receptor_usuario_id,
       ho.nome             AS hospital_origem,
       hd.nome             AS hospital_destino,
       fn_distancia_km(ho.latitude, ho.longitude, hd.latitude, hd.longitude) AS distancia_km,
       a.data_hora         AS alocado_em,
       a.status_logistica,
       f.status            AS status_fila
  FROM alocacao a
  JOIN orgao_disponivel od ON od.id = a.orgao_id
  JOIN tipo_orgao t        ON t.id  = od.tipo_orgao_id
  JOIN doador d            ON d.id  = od.doador_id
  JOIN hospital ho         ON ho.id = od.hospital_id
  JOIN fila_espera f       ON f.id  = a.fila_id
  JOIN receptor r          ON r.id  = f.receptor_id
  JOIN hospital hd         ON hd.id = r.hospital_id;
