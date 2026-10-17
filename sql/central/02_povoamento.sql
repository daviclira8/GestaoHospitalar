TRUNCATE alocacao, fila_espera, receptor, orgao_disponivel, doador,
         bolsa_sangue, tipo_orgao, hospital
RESTART IDENTITY CASCADE;

INSERT INTO hospital (nome, cidade, uf, latitude, longitude) VALUES
('Hospital Central de Fortaleza',      'Fortaleza',         'CE',  -3.731900, -38.526700),
('Hospital Regional do Cariri',        'Juazeiro do Norte', 'CE',  -7.213000, -39.315000),
('Hospital Regional Norte',            'Sobral',            'CE',  -3.688000, -40.349700),
('Hospital Universitário Potiguar',    'Natal',             'RN',  -5.794500, -35.211000),
('Hospital Metropolitano de Teresina', 'Teresina',          'PI',  -5.091900, -42.803400),
('Hospital Geral do Recife',           'Recife',            'PE',  -8.047600, -34.877000),
('Hospital Sul de Porto Alegre',       'Porto Alegre',      'RS', -30.034600, -51.217700);

INSERT INTO tipo_orgao (nome, tempo_max_isquemia_horas, permite_doador_vivo) VALUES
('Rim',       36, TRUE),
('Fígado',    12, TRUE),
('Coração',    4, FALSE),
('Pulmão',     6, TRUE),
('Pâncreas',  12, FALSE),
('Córnea',   168, FALSE);

INSERT INTO doador (usuario_id, tipo, hospital_id, data_cadastro, status) VALUES
(17, 'falecido', 1, '2026-08-05',   'apto'),
(3,  'falecido', 1, CURRENT_DATE,   'apto'),
(13, 'vivo',     1, '2026-09-20',   'apto');

INSERT INTO orgao_disponivel (doador_id, tipo_orgao_id, hospital_id, data_hora_captacao, status) VALUES
(1, 1, 1, '2026-08-05 08:00',              'alocado'),
(1, 6, 1, '2026-08-05 08:30',              'descartado'),
(2, 1, 1, NOW() - INTERVAL '2 hours',      'disponivel'),
(2, 1, 1, NOW() - INTERVAL '2 hours',      'disponivel'),
(2, 2, 1, NOW() - INTERVAL '90 minutes',   'disponivel'),
(2, 3, 1, NOW() - INTERVAL '1 hour',       'disponivel'),
(2, 6, 1, NOW() - INTERVAL '1 hour',       'disponivel');

INSERT INTO receptor (usuario_id, hospital_id, data_cadastro) VALUES
(10, 1, '2023-03-10'),
(2,  1, '2024-05-20'),
(4,  3, '2022-11-02'),
(6,  4, '2025-01-15'),
(12, 1, '2021-08-30'),
(5,  2, '2023-07-07'),
(15, 3, '2025-09-01'),
(7,  5, '2024-12-12'),
(9,  6, '2026-01-10'),
(1,  1, '2025-06-18'),
(18, 7, '2026-03-05'),
(11, 1, '2026-02-01'),
(14, 1, '2022-04-01');

INSERT INTO fila_espera (receptor_id, tipo_orgao_id, data_entrada, urgencia, status) VALUES
(1,  1, '2023-03-10 10:00', 3, 'aguardando'),
(2,  1, '2024-05-20 09:00', 2, 'aguardando'),
(3,  1, '2022-11-02 14:00', 3, 'aguardando'),
(4,  1, '2025-01-15 11:00', 4, 'aguardando'),
(5,  1, '2021-08-30 08:00', 2, 'aguardando'),
(6,  1, '2023-07-07 16:00', 5, 'aguardando'),
(7,  2, '2025-09-01 09:30', 5, 'aguardando'),
(8,  2, '2024-12-12 13:00', 4, 'aguardando'),
(9,  3, '2026-01-10 07:00', 5, 'aguardando'),
(10, 3, '2025-06-18 10:00', 4, 'aguardando'),
(11, 3, '2026-03-05 12:00', 5, 'aguardando'),
(12, 3, '2026-02-01 15:00', 3, 'aguardando'),
(13, 1, '2022-04-01 09:00', 3, 'transplantado');

INSERT INTO alocacao (orgao_id, fila_id, data_hora, status_logistica) VALUES
(1, 13, '2026-08-05 12:00', 'realizado');

INSERT INTO bolsa_sangue (usuario_id, hospital_id, data_coleta, data_validade, volume_ml, status) VALUES
(19, 1, CURRENT_DATE - 10,  CURRENT_DATE + 32, 450, 'disponivel'),
(19, 1, CURRENT_DATE - 75,  CURRENT_DATE - 33, 450, 'disponivel'),
(8,  1, CURRENT_DATE - 5,   CURRENT_DATE + 37, 450, 'disponivel'),
(8,  3, CURRENT_DATE - 120, CURRENT_DATE - 78, 450, 'utilizada'),
(20, 1, CURRENT_DATE - 3,   CURRENT_DATE + 39, 450, 'disponivel'),
(20, 2, CURRENT_DATE - 100, CURRENT_DATE - 58, 450, 'utilizada');
