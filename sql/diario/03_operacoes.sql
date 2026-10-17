SELECT id, nome, idade, sangue, cidade, uf, restricao_doacao, alergias
  FROM vw_ficha_usuario
 WHERE id = 10;

SELECT data, evento, descricao
  FROM vw_linha_do_tempo
 WHERE usuario_id = 10
 ORDER BY data;

SELECT data_hora::DATE                                        AS data,
       valor,
       unidade,
       valor - LAG(valor) OVER (ORDER BY data_hora)           AS variacao
  FROM metrica_saude
 WHERE usuario_id = 2 AND tipo = 'glicemia_jejum'
 ORDER BY data_hora;

SELECT DISTINCT ON (m.usuario_id, m.tipo)
       u.nome, m.tipo, m.valor, m.unidade, m.data_hora::DATE AS data
  FROM metrica_saude m
  JOIN usuario u ON u.id = m.usuario_id
 ORDER BY m.usuario_id, m.tipo, m.data_hora DESC;

SELECT v.nome AS vacina, v.fabricante, av.dose, av.data_aplicacao, av.lote
  FROM aplicacao_vacina av
  JOIN vacina v ON v.id = av.vacina_id
 WHERE av.usuario_id = 1
 ORDER BY av.data_aplicacao;

SELECT u.nome, d.nome AS doenca, d.cid, ud.status, ud.data_diagnostico
  FROM usuario_doenca ud
  JOIN usuario u ON u.id = ud.usuario_id
  JOIN doenca  d ON d.id = ud.doenca_id
 ORDER BY u.nome, ud.data_diagnostico;

SELECT u.id, u.nome, d.nome AS doenca, ud.status
  FROM usuario u
  JOIN usuario_doenca ud ON ud.usuario_id = u.id
  JOIN doenca d          ON d.id = ud.doenca_id
 WHERE d.impede_doacao
   AND ud.status <> 'curada';

SELECT u.nome, e.tipo, e.data, e.resultado,
       COALESCE(c.especialidade, '— exame avulso —') AS consulta_origem
  FROM exame e
  JOIN usuario u       ON u.id = e.usuario_id
  LEFT JOIN consulta c ON c.id = e.consulta_id
 ORDER BY u.nome, e.data;

SELECT COALESCE(sangue, 'não informado') AS tipo, COUNT(*) AS qtd
  FROM vw_ficha_usuario
 GROUP BY sangue
 ORDER BY qtd DESC;

SELECT id, nome FROM usuario WHERE tipo_sanguineo IS NULL;

BEGIN;

INSERT INTO usuario (nome, cpf, data_nascimento, sexo, tipo_sanguineo, fator_rh,
                     cidade, uf, email, telefone)
VALUES ('Wellington Dias Farias', '10000000021', '1991-02-02', 'masculino',
        'B', 'positivo', 'Fortaleza', 'CE', 'wellington.farias@exemplo.com',
        '(85) 90000-0021')
RETURNING id, nome, criado_em;

INSERT INTO alergia (usuario_id, substancia, gravidade)
SELECT id, 'Ibuprofeno', 'leve' FROM usuario WHERE cpf = '10000000021';

INSERT INTO metrica_saude (usuario_id, tipo, valor, unidade)
SELECT id, 'peso', 82.4, 'kg' FROM usuario WHERE cpf = '10000000021';

WITH nova_consulta AS (
    INSERT INTO consulta (usuario_id, data_hora, especialidade, profissional, local)
    VALUES (10, NOW(), 'Nefrologia', 'Dra. Sílvia Rangel', 'Clínica Rim Saudável')
    RETURNING id, usuario_id
)
INSERT INTO exame (usuario_id, consulta_id, tipo, data, resultado)
SELECT usuario_id, id, 'Creatinina sérica', CURRENT_DATE, '6,9 mg/dL'
  FROM nova_consulta;

INSERT INTO exame (usuario_id, tipo, data, resultado)
VALUES (16, 'Tipagem sanguínea ABO/Rh', CURRENT_DATE, 'B negativo');

UPDATE usuario
   SET tipo_sanguineo = 'B', fator_rh = 'negativo'
 WHERE id = 16
RETURNING id, nome, tipo_sanguineo, fator_rh;

UPDATE usuario_doenca
   SET status = 'controlada'
 WHERE usuario_id = 1 AND doenca_id = 7
RETURNING *;

DELETE FROM alergia
 WHERE usuario_id = 10 AND substancia = 'Sulfa'
RETURNING *;

SELECT id, nome, sangue, alergias FROM vw_ficha_usuario WHERE id IN (10, 16, 21);

ROLLBACK;
