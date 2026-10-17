CREATE EXTENSION IF NOT EXISTS postgres_fdw;

DROP SERVER IF EXISTS srv_diario CASCADE;
CREATE SERVER srv_diario
    FOREIGN DATA WRAPPER postgres_fdw
    OPTIONS (host 'localhost', port '5432', dbname 'diario_saude');

CREATE USER MAPPING FOR CURRENT_USER
    SERVER srv_diario
    OPTIONS (user 'postgres', password 'SUA_SENHA_AQUI');

CREATE SCHEMA IF NOT EXISTS diario;
CREATE FOREIGN TABLE diario.ficha_usuario (
    id                INT,
    nome              VARCHAR(120),
    idade             INT,
    tipo_sanguineo    tipo_sanguineo,
    fator_rh          fator_rh,
    sangue            TEXT,
    cidade            VARCHAR(80),
    uf                CHAR(2),
    restricao_doacao  BOOLEAN
) SERVER srv_diario OPTIONS (schema_name 'public', table_name 'vw_ficha_usuario');

SELECT c.fila_id,
       ur.nome                                   AS receptor,
       ud.sangue || ' → ' || ur.sangue           AS abo,
       c.urgencia, c.dias_espera, c.distancia_km, c.modal, c.tempo_transporte_h,
       fn_abo_compativel(ud.tipo_sanguineo, ur.tipo_sanguineo) AS abo_ok,
       c.logisticamente_viavel                                 AS logistica_ok
  FROM fn_candidatos_orgao(3) c
  JOIN diario.ficha_usuario ud ON ud.id = c.doador_usuario_id
  JOIN diario.ficha_usuario ur ON ur.id = c.receptor_usuario_id
 WHERE fn_abo_compativel(ud.tipo_sanguineo, ur.tipo_sanguineo)
   AND c.logisticamente_viavel
 ORDER BY c.urgencia DESC,
          (ud.tipo_sanguineo = ur.tipo_sanguineo) DESC,
          c.dias_espera DESC,
          c.distancia_km;

SELECT f.orgao, f.posicao, u.nome, u.sangue, u.idade, f.hospital, f.urgencia, f.dias_espera
  FROM vw_fila_ativa f
  JOIN diario.ficha_usuario u ON u.id = f.receptor_usuario_id
 ORDER BY f.orgao, f.posicao;

SELECT d.id AS doador_id, u.nome, d.status AS status_central,
       u.restricao_doacao AS restricao_no_diario,
       CASE WHEN u.restricao_doacao AND d.status = 'apto'
            THEN 'ATENÇÃO: deveria estar INAPTO' ELSE 'ok' END AS verificacao
  FROM doador d
  JOIN diario.ficha_usuario u ON u.id = d.usuario_id;

SELECT u.sangue, COUNT(*) AS bolsas, SUM(b.volume_ml) AS volume_total_ml
  FROM bolsa_sangue b
  JOIN diario.ficha_usuario u ON u.id = b.usuario_id
 WHERE b.status = 'disponivel' AND b.data_validade >= CURRENT_DATE
 GROUP BY u.sangue
 ORDER BY u.sangue;

SELECT 'doador' AS origem, usuario_id FROM doador
 WHERE usuario_id NOT IN (SELECT id FROM diario.ficha_usuario)
UNION ALL
SELECT 'receptor', usuario_id FROM receptor
 WHERE usuario_id NOT IN (SELECT id FROM diario.ficha_usuario)
UNION ALL
SELECT 'bolsa_sangue', usuario_id FROM bolsa_sangue
 WHERE usuario_id NOT IN (SELECT id FROM diario.ficha_usuario);
