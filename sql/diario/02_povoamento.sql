TRUNCATE metrica_saude, exame, consulta, aplicacao_vacina, vacina,
         usuario_doenca, doenca, alergia, usuario
RESTART IDENTITY CASCADE;

INSERT INTO usuario (nome, cpf, data_nascimento, sexo, tipo_sanguineo, fator_rh, cidade, uf, email, telefone) VALUES
('Ana Beatriz Lima',        '10000000001', '1990-04-12', 'feminino',  'O',  'positivo', 'Fortaleza',          'CE', 'ana.lima@exemplo.com',       '(85) 90000-0001'),
('Bruno Carvalho Souza',    '10000000002', '1985-09-03', 'masculino', 'A',  'positivo', 'Fortaleza',          'CE', 'bruno.souza@exemplo.com',    '(85) 90000-0002'),
('Carlos Eduardo Menezes',  '10000000003', '1978-01-25', 'masculino', 'A',  'positivo', 'Fortaleza',          'CE', 'carlos.menezes@exemplo.com', '(85) 90000-0003'),
('Daniela Rocha Pinto',     '10000000004', '1995-07-18', 'feminino',  'A',  'negativo', 'Sobral',             'CE', 'daniela.pinto@exemplo.com',  '(88) 90000-0004'),
('Eduardo Nogueira Alves',  '10000000005', '1969-11-30', 'masculino', 'B',  'positivo', 'Juazeiro do Norte',  'CE', 'eduardo.alves@exemplo.com',  '(88) 90000-0005'),
('Fernanda Castro Lopes',   '10000000006', '1982-02-14', 'feminino',  'AB', 'positivo', 'Natal',              'RN', 'fernanda.lopes@exemplo.com', '(84) 90000-0006'),
('Gustavo Henrique Barros', '10000000007', '1974-06-08', 'masculino', 'O',  'positivo', 'Teresina',           'PI', 'gustavo.barros@exemplo.com', '(86) 90000-0007'),
('Helena Martins Freitas',  '10000000008', '2001-03-22', 'feminino',  'A',  'positivo', 'Fortaleza',          'CE', 'helena.freitas@exemplo.com', '(85) 90000-0008'),
('Igor Sampaio Teixeira',   '10000000009', '1988-12-05', 'masculino', 'B',  'negativo', 'Recife',             'PE', 'igor.teixeira@exemplo.com',  '(81) 90000-0009'),
('Juliana Araújo Mota',     '10000000010', '1979-08-19', 'feminino',  'O',  'negativo', 'Fortaleza',          'CE', 'juliana.mota@exemplo.com',   '(85) 90000-0010'),
('Lucas Ferreira Dantas',   '10000000011', '1993-05-27', 'masculino', 'AB', 'negativo', 'Caucaia',            'CE', 'lucas.dantas@exemplo.com',   '(85) 90000-0011'),
('Mariana Queiroz Holanda', '10000000012', '1965-10-02', 'feminino',  'A',  'positivo', 'Maracanaú',          'CE', 'mariana.holanda@exemplo.com','(85) 90000-0012'),
('Rafael Tavares Bezerra',  '10000000013', '1999-01-09', 'masculino', 'O',  'positivo', 'Fortaleza',          'CE', 'rafael.bezerra@exemplo.com', '(85) 90000-0013'),
('Patrícia Moura Costa',    '10000000014', '1987-04-04', 'feminino',  'B',  'positivo', 'Fortaleza',          'CE', 'patricia.costa@exemplo.com', '(85) 90000-0014'),
('Tiago Brandão Silva',     '10000000015', '1958-09-15', 'masculino', 'A',  'negativo', 'Sobral',             'CE', 'tiago.silva@exemplo.com',    '(88) 90000-0015'),
('Vanessa Pires Cunha',     '10000000016', '2004-12-21', 'feminino',  NULL, NULL,       'Fortaleza',          'CE', 'vanessa.cunha@exemplo.com',  '(85) 90000-0016'),
('Otávio Leite Prado',      '10000000017', '1971-07-07', 'masculino', 'O',  'positivo', 'Fortaleza',          'CE', 'otavio.prado@exemplo.com',   '(85) 90000-0017'),
('Sérgio Lemos Vieira',     '10000000018', '1980-03-11', 'masculino', 'A',  'positivo', 'Porto Alegre',       'RS', 'sergio.vieira@exemplo.com',  '(51) 90000-0018'),
('Paulo Henrique Rocha',    '10000000019', '1992-10-28', 'masculino', 'O',  'negativo', 'Fortaleza',          'CE', 'paulo.rocha@exemplo.com',    '(85) 90000-0019'),
('Larissa Gomes Oliveira',  '10000000020', '1997-06-16', 'feminino',  'AB', 'positivo', 'Eusébio',            'CE', 'larissa.oliveira@exemplo.com','(85) 90000-0020');

INSERT INTO alergia (usuario_id, substancia, gravidade, observacao) VALUES
(1,  'Penicilina',  'grave',    'Anafilaxia em 2015'),
(2,  'Dipirona',    'moderada', 'Urticária generalizada'),
(4,  'Látex',       'leve',     NULL),
(8,  'Amendoim',    'grave',    'Porta caneta de adrenalina'),
(10, 'Iodo (contraste)', 'moderada', 'Exige preparo antes de exames contrastados'),
(10, 'Sulfa',       'leve',     NULL),
(15, 'Ácido acetilsalicílico', 'moderada', NULL);

INSERT INTO doenca (nome, cid, impede_doacao) VALUES
('Hipertensão arterial',          'I10',   FALSE),
('Diabetes mellitus tipo 2',      'E11',   FALSE),
('Doença renal crônica',          'N18',   FALSE),
('Hepatite C crônica',            'B18.2', TRUE),
('Doença de Chagas',              'B57',   TRUE),
('Cirrose hepática',              'K74',   FALSE),
('Insuficiência cardíaca',        'I50',   FALSE),
('Asma',                          'J45',   FALSE),
('Neoplasia maligna em atividade','C80',   TRUE),
('COVID-19',                      'U07.1', FALSE);

INSERT INTO usuario_doenca (usuario_id, doenca_id, data_diagnostico, status) VALUES
(1,  7, '2023-02-10', 'ativa'),
(2,  3, '2022-08-01', 'ativa'),
(2,  2, '2015-05-20', 'controlada'),
(3,  1, '2018-03-14', 'controlada'),
(4,  3, '2021-06-30', 'ativa'),
(5,  3, '2022-12-12', 'ativa'),
(5,  1, '2010-01-08', 'controlada'),
(6,  3, '2023-09-09', 'ativa'),
(7,  6, '2023-04-17', 'ativa'),
(8,  8, '2010-05-05', 'controlada'),
(8, 10, '2022-01-15', 'curada'),
(9,  7, '2024-07-22', 'ativa'),
(10, 3, '2020-11-03', 'ativa'),
(10, 1, '2019-02-27', 'controlada'),
(11, 7, '2025-03-03', 'ativa'),
(12, 3, '2019-10-10', 'ativa'),
(12, 2, '2012-04-18', 'controlada'),
(13, 4, '2026-08-28', 'ativa'),
(14, 3, '2018-02-02', 'controlada'),
(15, 6, '2024-11-11', 'ativa'),
(18, 7, '2024-01-19', 'ativa'),
(20,10, '2023-07-01', 'curada');

INSERT INTO vacina (nome, fabricante) VALUES
('Hepatite B',     'Instituto Butantan'),
('Febre amarela',  'Bio-Manguinhos'),
('Tríplice viral', 'Bio-Manguinhos'),
('Influenza',      'Instituto Butantan'),
('COVID-19',       'Pfizer/BioNTech'),
('dT (difteria e tétano)', 'Instituto Butantan');

INSERT INTO aplicacao_vacina (usuario_id, vacina_id, data_aplicacao, dose, lote) VALUES
(1, 1, '2008-03-10', '1ª dose', 'HB0801'),
(1, 1, '2008-04-10', '2ª dose', 'HB0802'),
(1, 1, '2008-09-10', '3ª dose', 'HB0803'),
(1, 4, '2026-04-15', 'anual 2026', 'FLU26A'),
(2, 5, '2021-07-02', '1ª dose', 'PF2107'),
(2, 5, '2021-09-24', '2ª dose', 'PF2109'),
(2, 4, '2026-04-20', 'anual 2026', 'FLU26A'),
(8, 2, '2019-01-12', 'dose única', 'FA1901'),
(8, 3, '2002-03-22', '1ª dose', 'TV0203'),
(10,1, '2020-12-01', '1ª dose', 'HB2012'),
(10,1, '2021-01-05', '2ª dose', 'HB2101'),
(10,6, '2024-06-06', 'reforço', 'DT2406'),
(12,4, '2026-05-02', 'anual 2026', 'FLU26B'),
(13,5, '2022-02-14', '1ª dose', 'PF2202'),
(19,2, '2015-08-08', 'dose única', 'FA1508'),
(20,5, '2021-10-10', '1ª dose', 'PF2110');

INSERT INTO consulta (usuario_id, data_hora, especialidade, profissional, local, observacoes) VALUES
(10, '2026-03-12 09:00', 'Nefrologia',   'Dra. Sílvia Rangel',  'Clínica Rim Saudável',     'Função renal em queda, manter diálise 3x/semana'),
(10, '2026-06-18 10:30', 'Nefrologia',   'Dra. Sílvia Rangel',  'Clínica Rim Saudável',     'Indicação de transplante reforçada'),
(10, '2026-09-20 08:15', 'Nefrologia',   'Dra. Sílvia Rangel',  'Clínica Rim Saudável',     'Paciente estável na fila'),
(2,  '2026-02-05 14:00', 'Nefrologia',   'Dr. Marcos Feitosa',  'Hospital Central de Fortaleza', NULL),
(2,  '2026-07-07 15:00', 'Endocrinologia','Dra. Lia Cavalcante','Policlínica Centro',       'Glicemia controlada'),
(1,  '2026-05-10 11:00', 'Cardiologia',  'Dr. André Pontes',    'Hospital Central de Fortaleza', 'Fração de ejeção 25%'),
(15, '2026-08-01 09:45', 'Hepatologia',  'Dr. Renato Gadelha',  'Hospital Regional Norte',  'MELD elevado, prioridade alta'),
(8,  '2026-01-20 16:00', 'Clínica geral','Dr. João Batista',    'UBS Messejana',            'Check-up anual'),
(13, '2026-08-28 10:00', 'Infectologia', 'Dra. Paula Arruda',   'Hospital São José',        'Diagnóstico de hepatite C, iniciar tratamento'),
(19, '2026-04-04 08:00', 'Hematologia',  'Dra. Cecília Viana',  'Hemocentro',               'Apto para doação de sangue');

INSERT INTO exame (usuario_id, consulta_id, tipo, data, resultado) VALUES
(10, 1,    'Creatinina sérica',           '2026-03-12', '5,8 mg/dL'),
(10, 2,    'Creatinina sérica',           '2026-06-18', '6,4 mg/dL'),
(10, 3,    'Painel de anticorpos (PRA)',  '2026-09-20', '12%'),
(10, NULL, 'Tipagem sanguínea ABO/Rh',    '2020-11-03', 'O negativo'),
(2,  4,    'Taxa de filtração glomerular','2026-02-05', '13 mL/min'),
(2,  5,    'Hemoglobina glicada',         '2026-07-07', '6,8%'),
(1,  6,    'Ecocardiograma',              '2026-05-10', 'FE 25%, disfunção sistólica grave'),
(15, 7,    'Bilirrubina total',           '2026-08-01', '4,2 mg/dL'),
(8,  8,    'Hemograma completo',          '2026-01-20', 'Sem alterações'),
(8,  NULL, 'Tipagem sanguínea ABO/Rh',    '2019-05-05', 'A positivo'),
(13, 9,    'Anti-HCV',                    '2026-08-28', 'Reagente'),
(3,  NULL, 'Tipagem sanguínea ABO/Rh',    '2026-10-12', 'A positivo'),
(19, 10,   'Sorologias para doação',      '2026-04-04', 'Não reagentes');

INSERT INTO metrica_saude (usuario_id, tipo, valor, unidade, data_hora) VALUES
(10, 'peso',                64.0, 'kg',    '2026-01-10 08:00'),
(10, 'peso',                62.5, 'kg',    '2026-04-10 08:00'),
(10, 'peso',                61.2, 'kg',    '2026-07-10 08:00'),
(10, 'peso',                60.4, 'kg',    '2026-10-01 08:00'),
(10, 'pressao_sistolica',  150,   'mmHg',  '2026-01-10 08:05'),
(10, 'pressao_sistolica',  142,   'mmHg',  '2026-04-10 08:05'),
(10, 'pressao_sistolica',  138,   'mmHg',  '2026-07-10 08:05'),
(10, 'pressao_sistolica',  135,   'mmHg',  '2026-10-01 08:05'),
(2,  'glicemia_jejum',     148,   'mg/dL', '2026-02-01 07:00'),
(2,  'glicemia_jejum',     131,   'mg/dL', '2026-04-01 07:00'),
(2,  'glicemia_jejum',     118,   'mg/dL', '2026-06-01 07:00'),
(2,  'glicemia_jejum',     109,   'mg/dL', '2026-08-01 07:00'),
(1,  'frequencia_cardiaca', 96,   'bpm',   '2026-03-01 09:00'),
(1,  'frequencia_cardiaca', 102,  'bpm',   '2026-06-01 09:00'),
(1,  'frequencia_cardiaca', 108,  'bpm',   '2026-09-01 09:00'),
(8,  'peso',                58.0, 'kg',    '2026-01-20 16:10'),
(8,  'peso',                57.3, 'kg',    '2026-07-15 10:00');
