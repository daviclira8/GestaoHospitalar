# -*- coding: utf-8 -*-
"""Consultas e comandos SQL do Diario de Saude Pessoal.

Todo o SQL do sistema fica concentrado aqui; os menus do terminal
(DiarioPessoal.py) e a interface grafica (gui.py) apenas chamam estas funcoes.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import db

NOME_BANCO = "diario"


def conectar():
    return db.conectar(NOME_BANCO)


# ---------------------------------------------------------------------------
# USUARIOS
# ---------------------------------------------------------------------------
def listar_usuarios(conexao):
    return db.consultar(conexao, """
        SELECT id_usuario,
               nome,
               cpf,
               tipo_sanguineo || fator_rh AS sangue,
               data_nascimento,
               CAST((julianday('now') - julianday(data_nascimento)) / 365.25 AS INTEGER) AS idade,
               telefone
          FROM usuario
         ORDER BY nome
    """)


def buscar_usuario(conexao, id_usuario):
    return db.consultar_um(conexao, """
        SELECT id_usuario, nome, cpf, data_nascimento, sexo,
               tipo_sanguineo, fator_rh,
               tipo_sanguineo || fator_rh AS sangue,
               telefone, email
          FROM usuario
         WHERE id_usuario = ?
    """, (id_usuario,))


def buscar_usuarios_por_nome(conexao, termo):
    return db.consultar(conexao, """
        SELECT id_usuario,
               nome,
               cpf,
               tipo_sanguineo || fator_rh AS sangue,
               data_nascimento,
               CAST((julianday('now') - julianday(data_nascimento)) / 365.25 AS INTEGER) AS idade,
               telefone
          FROM usuario
         WHERE nome LIKE ? OR cpf LIKE ?
         ORDER BY nome
    """, ("%" + termo + "%", "%" + termo + "%"))


def inserir_usuario(conexao, dados):
    cursor = db.executar(conexao, """
        INSERT INTO usuario (nome, cpf, data_nascimento, sexo,
                             tipo_sanguineo, fator_rh, telefone, email)
        VALUES (:nome, :cpf, :data_nascimento, :sexo,
                :tipo_sanguineo, :fator_rh, :telefone, :email)
    """, dados)
    return cursor.lastrowid


def atualizar_contato(conexao, id_usuario, telefone, email):
    cursor = db.executar(conexao, """
        UPDATE usuario SET telefone = ?, email = ? WHERE id_usuario = ?
    """, (telefone, email, id_usuario))
    return cursor.rowcount


def atualizar_tipo_sanguineo(conexao, id_usuario, tipo_sanguineo, fator_rh):
    cursor = db.executar(conexao, """
        UPDATE usuario SET tipo_sanguineo = ?, fator_rh = ? WHERE id_usuario = ?
    """, (tipo_sanguineo, fator_rh, id_usuario))
    return cursor.rowcount


def distribuicao_sanguinea(conexao):
    return db.consultar(conexao, """
        SELECT tipo_sanguineo || fator_rh AS sangue, COUNT(*) AS usuarios
          FROM usuario
         GROUP BY tipo_sanguineo, fator_rh
         ORDER BY usuarios DESC, sangue
    """)


# ---------------------------------------------------------------------------
# ALERGIAS (relacionamento N:N)
# ---------------------------------------------------------------------------
def listar_catalogo_alergias(conexao):
    return db.consultar(conexao, """
        SELECT a.id_alergia, a.nome, a.categoria,
               COUNT(ua.id_usuario) AS usuarios_afetados
          FROM alergia a
          LEFT JOIN usuario_alergia ua ON ua.id_alergia = a.id_alergia
         GROUP BY a.id_alergia
         ORDER BY a.categoria, a.nome
    """)


def listar_alergias_usuario(conexao, id_usuario):
    return db.consultar(conexao, """
        SELECT a.nome AS alergia, a.categoria, ua.gravidade,
               ua.data_registro, ua.observacao
          FROM usuario_alergia ua
          JOIN alergia a ON a.id_alergia = ua.id_alergia
         WHERE ua.id_usuario = ?
         ORDER BY CASE ua.gravidade
                      WHEN 'GRAVE' THEN 1 WHEN 'MODERADA' THEN 2 ELSE 3 END
    """, (id_usuario,))


def inserir_alergia_catalogo(conexao, nome, categoria):
    cursor = db.executar(conexao,
                         "INSERT INTO alergia (nome, categoria) VALUES (?, ?)",
                         (nome, categoria))
    return cursor.lastrowid


def vincular_alergia(conexao, id_usuario, id_alergia, gravidade, observacao):
    cursor = db.executar(conexao, """
        INSERT INTO usuario_alergia (id_usuario, id_alergia, gravidade, observacao)
        VALUES (?, ?, ?, ?)
    """, (id_usuario, id_alergia, gravidade, observacao))
    return cursor.lastrowid


def atualizar_gravidade_alergia(conexao, id_usuario, id_alergia, gravidade):
    cursor = db.executar(conexao, """
        UPDATE usuario_alergia SET gravidade = ?
         WHERE id_usuario = ? AND id_alergia = ?
    """, (gravidade, id_usuario, id_alergia))
    return cursor.rowcount


def alergias_graves(conexao):
    return db.consultar(conexao, """
        SELECT u.nome AS usuario, u.tipo_sanguineo || u.fator_rh AS sangue,
               a.nome AS alergia, a.categoria, ua.gravidade, ua.observacao
          FROM usuario_alergia ua
          JOIN usuario u ON u.id_usuario = ua.id_usuario
          JOIN alergia a ON a.id_alergia = ua.id_alergia
         WHERE ua.gravidade IN ('GRAVE', 'MODERADA')
         ORDER BY CASE ua.gravidade WHEN 'GRAVE' THEN 1 ELSE 2 END, u.nome
    """)


# ---------------------------------------------------------------------------
# PROFISSIONAIS E CONSULTAS
# ---------------------------------------------------------------------------
def listar_profissionais(conexao):
    return db.consultar(conexao, """
        SELECT p.id_profissional, p.nome, p.especialidade, p.registro,
               COUNT(c.id_consulta) AS consultas
          FROM profissional p
          LEFT JOIN consulta c ON c.id_profissional = p.id_profissional
         GROUP BY p.id_profissional
         ORDER BY p.nome
    """)


def inserir_profissional(conexao, nome, especialidade, registro):
    cursor = db.executar(conexao, """
        INSERT INTO profissional (nome, especialidade, registro) VALUES (?, ?, ?)
    """, (nome, especialidade, registro))
    return cursor.lastrowid


def listar_consultas_usuario(conexao, id_usuario):
    return db.consultar(conexao, """
        SELECT c.id_consulta, c.data_hora, p.nome AS profissional,
               p.especialidade, c.motivo, c.diagnostico, c.prescricao
          FROM consulta c
          JOIN profissional p ON p.id_profissional = c.id_profissional
         WHERE c.id_usuario = ?
         ORDER BY c.data_hora DESC
    """, (id_usuario,))


def inserir_consulta(conexao, dados):
    cursor = db.executar(conexao, """
        INSERT INTO consulta (id_usuario, id_profissional, data_hora,
                              motivo, diagnostico, prescricao)
        VALUES (:id_usuario, :id_profissional, :data_hora,
                :motivo, :diagnostico, :prescricao)
    """, dados)
    return cursor.lastrowid


def atualizar_consulta(conexao, id_consulta, diagnostico, prescricao):
    cursor = db.executar(conexao, """
        UPDATE consulta SET diagnostico = ?, prescricao = ? WHERE id_consulta = ?
    """, (diagnostico, prescricao, id_consulta))
    return cursor.rowcount


def consultas_por_especialidade(conexao):
    return db.consultar(conexao, """
        SELECT p.especialidade, COUNT(*) AS total,
               MIN(c.data_hora) AS primeira, MAX(c.data_hora) AS ultima
          FROM consulta c
          JOIN profissional p ON p.id_profissional = c.id_profissional
         GROUP BY p.especialidade
         ORDER BY total DESC
    """)


# ---------------------------------------------------------------------------
# EXAMES
# ---------------------------------------------------------------------------
def listar_exames_usuario(conexao, id_usuario):
    return db.consultar(conexao, """
        SELECT e.id_exame, e.tipo, e.data_realizacao, e.laboratorio,
               e.status, e.resultado, c.motivo AS consulta_origem
          FROM exame e
          LEFT JOIN consulta c ON c.id_consulta = e.id_consulta
         WHERE e.id_usuario = ?
         ORDER BY e.data_realizacao DESC
    """, (id_usuario,))


def inserir_exame(conexao, dados):
    cursor = db.executar(conexao, """
        INSERT INTO exame (id_usuario, id_consulta, tipo, data_realizacao,
                           laboratorio, resultado, status)
        VALUES (:id_usuario, :id_consulta, :tipo, :data_realizacao,
                :laboratorio, :resultado, :status)
    """, dados)
    return cursor.lastrowid


def lancar_resultado_exame(conexao, id_exame, resultado):
    cursor = db.executar(conexao, """
        UPDATE exame SET resultado = ?, status = 'CONCLUIDO' WHERE id_exame = ?
    """, (resultado, id_exame))
    return cursor.rowcount


def exames_pendentes(conexao):
    return db.consultar(conexao, """
        SELECT e.id_exame, u.nome AS usuario, e.tipo, e.data_realizacao,
               e.laboratorio, c.motivo AS consulta_origem
          FROM exame e
          JOIN usuario u ON u.id_usuario = e.id_usuario
          LEFT JOIN consulta c ON c.id_consulta = e.id_consulta
         WHERE e.status = 'PENDENTE'
         ORDER BY e.data_realizacao
    """)


# ---------------------------------------------------------------------------
# VACINAS
# ---------------------------------------------------------------------------
def listar_catalogo_vacinas(conexao):
    return db.consultar(conexao, """
        SELECT id_vacina, nome, doses_recomendadas, fabricante
          FROM vacina ORDER BY nome
    """)


def carteira_vacinacao(conexao, id_usuario):
    return db.consultar(conexao, """
        SELECT v.nome AS vacina, vc.dose, v.doses_recomendadas,
               vc.data_aplicacao, vc.lote, vc.local_aplicacao
          FROM vacinacao vc
          JOIN vacina v ON v.id_vacina = vc.id_vacina
         WHERE vc.id_usuario = ?
         ORDER BY v.nome, vc.dose
    """, (id_usuario,))


def inserir_vacinacao(conexao, dados):
    cursor = db.executar(conexao, """
        INSERT INTO vacinacao (id_usuario, id_vacina, dose, data_aplicacao,
                               lote, local_aplicacao)
        VALUES (:id_usuario, :id_vacina, :dose, :data_aplicacao,
                :lote, :local_aplicacao)
    """, dados)
    return cursor.lastrowid


def doses_pendentes(conexao, id_usuario=None):
    """Vacinas iniciadas em que o numero de doses aplicadas e insuficiente."""
    sql = """
        SELECT u.nome AS usuario, v.nome AS vacina,
               COUNT(*) AS aplicadas, v.doses_recomendadas,
               v.doses_recomendadas - COUNT(*) AS faltam,
               MAX(vc.data_aplicacao) AS ultima_dose
          FROM vacinacao vc
          JOIN usuario u ON u.id_usuario = vc.id_usuario
          JOIN vacina  v ON v.id_vacina  = vc.id_vacina
         {filtro}
         GROUP BY vc.id_usuario, vc.id_vacina
        HAVING COUNT(*) < v.doses_recomendadas
         ORDER BY u.nome, v.nome
    """
    if id_usuario is None:
        return db.consultar(conexao, sql.format(filtro=""))
    return db.consultar(conexao, sql.format(filtro="WHERE vc.id_usuario = ?"),
                        (id_usuario,))


# ---------------------------------------------------------------------------
# HISTORICO CONSOLIDADO (linha do tempo)
# ---------------------------------------------------------------------------
def linha_do_tempo(conexao, id_usuario):
    """Une consultas, exames e vacinas em um unico historico cronologico."""
    return db.consultar(conexao, """
        SELECT substr(c.data_hora, 1, 10) AS data, 'CONSULTA' AS evento,
               c.motivo AS descricao,
               COALESCE(c.diagnostico, '-') AS detalhe
          FROM consulta c WHERE c.id_usuario = ?
        UNION ALL
        SELECT e.data_realizacao, 'EXAME', e.tipo,
               COALESCE(e.resultado, e.status)
          FROM exame e WHERE e.id_usuario = ?
        UNION ALL
        SELECT vc.data_aplicacao, 'VACINA',
               v.nome || ' (dose ' || vc.dose || ')',
               COALESCE(vc.local_aplicacao, '-')
          FROM vacinacao vc
          JOIN vacina v ON v.id_vacina = vc.id_vacina
         WHERE vc.id_usuario = ?
         ORDER BY data DESC
    """, (id_usuario, id_usuario, id_usuario))


def resumo_geral(conexao):
    return db.consultar_um(conexao, """
        SELECT (SELECT COUNT(*) FROM usuario)         AS usuarios,
               (SELECT COUNT(*) FROM consulta)        AS consultas,
               (SELECT COUNT(*) FROM exame)           AS exames,
               (SELECT COUNT(*) FROM exame WHERE status = 'PENDENTE') AS exames_pendentes,
               (SELECT COUNT(*) FROM vacinacao)       AS doses_aplicadas,
               (SELECT COUNT(*) FROM usuario_alergia) AS alergias_registradas
    """)
