SELECT orgao, posicao, fila_id, receptor_usuario_id, hospital, uf,
       urgencia, entrada, dias_espera
  FROM vw_fila_ativa
 ORDER BY orgao, posicao;

SELECT orgao_id, orgao, hospital_origem, prazo_limite, horas_restantes
  FROM vw_orgaos_disponiveis
 ORDER BY horas_restantes;

SELECT * FROM fn_candidatos_orgao(6);

WITH tipos_do_diario (usuario_id, tipo) AS (
    VALUES (3, 'A'::tipo_sanguineo),
           (9, 'B'), (18, 'A'), (1, 'O'), (11, 'AB')
), c AS (
    SELECT cand.*,
           td.tipo AS tipo_doador,
           tr.tipo AS tipo_receptor
      FROM fn_candidatos_orgao(6) cand
      JOIN tipos_do_diario td ON td.usuario_id = cand.doador_usuario_id
      JOIN tipos_do_diario tr ON tr.usuario_id = cand.receptor_usuario_id
)
SELECT fila_id, receptor_usuario_id, tipo_doador || ' → ' || tipo_receptor AS abo,
       fn_abo_compativel(tipo_doador, tipo_receptor)   AS abo_ok,
       logisticamente_viavel                           AS logistica_ok,
       urgencia, dias_espera, distancia_km, tempo_transporte_h,
       CASE WHEN fn_abo_compativel(tipo_doador, tipo_receptor) AND logisticamente_viavel
            THEN 'ELEGÍVEL' ELSE 'descartado' END     AS resultado
  FROM c
 ORDER BY (fn_abo_compativel(tipo_doador, tipo_receptor) AND logisticamente_viavel) DESC,
          urgencia DESC,
          (tipo_doador = tipo_receptor) DESC,
          dias_espera DESC,
          distancia_km;

SELECT tipo_receptor AS receptor,
       STRING_AGG(tipo_doador::TEXT, ', ' ORDER BY tipo_doador) AS recebe_de
  FROM compatibilidade_abo
 GROUP BY tipo_receptor
 ORDER BY tipo_receptor;

SELECT * FROM vw_processos ORDER BY alocado_em DESC;

SELECT t.nome AS orgao,
       COUNT(*) FILTER (WHERE f.status = 'aguardando')    AS aguardando,
       COUNT(*) FILTER (WHERE f.status = 'transplantado') AS transplantados,
       ROUND(AVG(CURRENT_DATE - f.data_entrada::DATE)
             FILTER (WHERE f.status = 'aguardando'))      AS media_dias_espera
  FROM tipo_orgao t
  LEFT JOIN fila_espera f ON f.tipo_orgao_id = t.id
 GROUP BY t.nome
 ORDER BY aguardando DESC;

SELECT d.id AS doador_id, d.usuario_id, d.tipo, d.status,
       COUNT(od.id)                                         AS orgaos,
       COUNT(od.id) FILTER (WHERE od.status = 'disponivel') AS disponiveis,
       COUNT(od.id) FILTER (WHERE od.status = 'alocado')    AS alocados,
       COUNT(od.id) FILTER (WHERE od.status = 'descartado') AS descartados
  FROM doador d
  LEFT JOIN orgao_disponivel od ON od.doador_id = d.id
 GROUP BY d.id
 ORDER BY d.id;

SELECT h.nome AS hospital, b.id AS bolsa_id, b.usuario_id AS doador_usuario_id,
       b.volume_ml, b.data_validade, b.data_validade - CURRENT_DATE AS dias_ate_vencer, b.status
  FROM bolsa_sangue b
  JOIN hospital h ON h.id = b.hospital_id
 ORDER BY h.nome, b.data_validade;

WITH tipos_do_diario (usuario_id, tipo, rh) AS (
    VALUES (19, 'O'::tipo_sanguineo, 'negativo'::fator_rh),
           (8,  'A', 'positivo'),
           (20, 'AB','positivo')
)
SELECT b.id AS bolsa_id, t.tipo::TEXT || CASE t.rh WHEN 'positivo' THEN '+' ELSE '-' END AS sangue,
       b.data_validade,
       fn_sangue_compativel(t.tipo, t.rh, 'O', 'negativo') AS serve_para_O_negativo
  FROM bolsa_sangue b
  JOIN tipos_do_diario t ON t.usuario_id = b.usuario_id
 WHERE b.status = 'disponivel' AND b.data_validade >= CURRENT_DATE
 ORDER BY serve_para_O_negativo DESC, b.data_validade;

BEGIN;

SELECT fn_atualizar_bolsas_vencidas()  AS bolsas_marcadas_como_vencidas;
SELECT fn_descartar_orgaos_expirados() AS orgaos_descartados;

UPDATE doador SET status = 'inapto'
 WHERE usuario_id = 13
RETURNING id, usuario_id, tipo, status;

DO $$
BEGIN
    INSERT INTO orgao_disponivel (doador_id, tipo_orgao_id, hospital_id) VALUES (3, 1, 1);
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Bloqueado pelo banco → %', SQLERRM;
END $$;

WITH novo AS (
    INSERT INTO receptor (usuario_id, hospital_id) VALUES (16, 1)
    RETURNING id
)
INSERT INTO fila_espera (receptor_id, tipo_orgao_id, urgencia)
SELECT id, 6, 2 FROM novo
RETURNING id AS fila_id, receptor_id, tipo_orgao_id, urgencia, status;

UPDATE fila_espera SET urgencia = 5 WHERE id = 1
RETURNING id, urgencia;

SELECT fn_alocar_orgao(6, 12) AS alocacao_coracao_lucas;
SELECT fn_alocar_orgao(3, 4)  AS alocacao_rim_fernanda;
SELECT fn_alocar_orgao(4, 3)  AS alocacao_rim_daniela;
SELECT fn_alocar_orgao(5, 7)  AS alocacao_figado_tiago;

DO $$
BEGIN
    PERFORM fn_alocar_orgao(6, 9);
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Bloqueado pelo banco → %', SQLERRM;
END $$;

SELECT fn_registrar_entrega(a.id), fn_concluir_transplante(a.id)
  FROM alocacao a WHERE a.orgao_id = 6 AND a.status_logistica = 'em_transporte';

SELECT fn_cancelar_alocacao(a.id)
  FROM alocacao a WHERE a.orgao_id = 4 AND a.status_logistica = 'em_transporte';
SELECT fn_alocar_orgao(4, 5) AS realocacao_rim_mariana;

SELECT alocacao_id, orgao, receptor_usuario_id, hospital_destino,
       distancia_km, status_logistica, status_fila
  FROM vw_processos ORDER BY alocacao_id;

SELECT orgao, posicao, receptor_usuario_id, urgencia FROM vw_fila_ativa ORDER BY orgao, posicao;

SELECT id, status, data_validade FROM bolsa_sangue WHERE id = 2;

ROLLBACK;
