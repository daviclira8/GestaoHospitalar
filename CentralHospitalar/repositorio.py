# -*- coding: utf-8 -*-
"""Consultas e comandos SQL da Central Hospitalar de Transplantes.

A compatibilidade entre doador e receptor e resolvida dentro do banco pela
view vw_compatibilidade, que cruza o tipo de orgao com as tabelas de dominio
compat_abo e compat_rh.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import db

NOME_BANCO = "central"

# Ordenacao clinica: emergencia primeiro, depois alta, depois normal
ORDEM_PRIORIDADE = ("CASE prioridade WHEN 'EMERGENCIA' THEN 1 "
                    "WHEN 'ALTA' THEN 2 ELSE 3 END")


def conectar():
    return db.conectar(NOME_BANCO)


# ---------------------------------------------------------------------------
# CADASTROS BASICOS
# ---------------------------------------------------------------------------
def listar_hospitais(conexao):
    return db.consultar(conexao, """
        SELECT id_hospital, nome, cidade, uf, cnes FROM hospital ORDER BY nome
    """)


def listar_tipos_orgao(conexao):
    return db.consultar(conexao, """
        SELECT t.id_tipo_orgao, t.nome, t.tempo_isquemia_horas,
               (SELECT COUNT(*) FROM orgao_disponivel o
                 WHERE o.id_tipo_orgao = t.id_tipo_orgao AND o.status = 'DISPONIVEL') AS disponiveis,
               (SELECT COUNT(*) FROM fila_espera f
                 WHERE f.id_tipo_orgao = t.id_tipo_orgao AND f.status = 'AGUARDANDO') AS na_fila
          FROM tipo_orgao t
         ORDER BY t.nome
    """)


# ---------------------------------------------------------------------------
# DOADORES
# ---------------------------------------------------------------------------
def listar_doadores(conexao):
    return db.consultar(conexao, """
        SELECT d.id_doador, d.nome,
               d.tipo_sanguineo || d.fator_rh AS sangue,
               d.tipo_doador, h.nome AS hospital, d.data_registro,
               COUNT(o.id_orgao) AS orgaos
          FROM doador d
          JOIN hospital h ON h.id_hospital = d.id_hospital
          LEFT JOIN orgao_disponivel o ON o.id_doador = d.id_doador
         GROUP BY d.id_doador
         ORDER BY d.nome
    """)


def inserir_doador(conexao, dados):
    cursor = db.executar(conexao, """
        INSERT INTO doador (nome, cpf, data_nascimento, tipo_sanguineo,
                            fator_rh, tipo_doador, id_hospital, data_registro)
        VALUES (:nome, :cpf, :data_nascimento, :tipo_sanguineo,
                :fator_rh, :tipo_doador, :id_hospital, :data_registro)
    """, dados)
    return cursor.lastrowid


# ---------------------------------------------------------------------------
# RECEPTORES
# ---------------------------------------------------------------------------
def listar_receptores(conexao):
    return db.consultar(conexao, """
        SELECT r.id_receptor, r.nome,
               r.tipo_sanguineo || r.fator_rh AS sangue,
               h.nome AS hospital, r.contato,
               (SELECT COUNT(*) FROM fila_espera f
                 WHERE f.id_receptor = r.id_receptor AND f.status = 'AGUARDANDO') AS filas_ativas
          FROM receptor r
          JOIN hospital h ON h.id_hospital = r.id_hospital
         ORDER BY r.nome
    """)


def inserir_receptor(conexao, dados):
    cursor = db.executar(conexao, """
        INSERT INTO receptor (nome, cpf, data_nascimento, tipo_sanguineo,
                              fator_rh, id_hospital, contato)
        VALUES (:nome, :cpf, :data_nascimento, :tipo_sanguineo,
                :fator_rh, :id_hospital, :contato)
    """, dados)
    return cursor.lastrowid


def atualizar_contato_receptor(conexao, id_receptor, contato):
    cursor = db.executar(conexao,
                         "UPDATE receptor SET contato = ? WHERE id_receptor = ?",
                         (contato, id_receptor))
    return cursor.rowcount


# ---------------------------------------------------------------------------
# ORGAOS
# ---------------------------------------------------------------------------
def listar_orgaos(conexao, status=None):
    sql = """
        SELECT o.id_orgao, t.nome AS orgao, d.nome AS doador,
               d.tipo_sanguineo || d.fator_rh AS sangue, d.tipo_doador,
               o.data_captacao, o.status, h.nome AS hospital,
               t.tempo_isquemia_horas AS isquemia_h,
               CAST((julianday('now') - julianday(o.data_captacao)) * 24 AS INTEGER) AS horas_desde_captacao
          FROM orgao_disponivel o
          JOIN doador     d ON d.id_doador     = o.id_doador
          JOIN tipo_orgao t ON t.id_tipo_orgao = o.id_tipo_orgao
          JOIN hospital   h ON h.id_hospital   = o.id_hospital
         {filtro}
         ORDER BY o.data_captacao DESC
    """
    if status:
        return db.consultar(conexao, sql.format(filtro="WHERE o.status = ?"), (status,))
    return db.consultar(conexao, sql.format(filtro=""))


def inserir_orgao(conexao, dados):
    cursor = db.executar(conexao, """
        INSERT INTO orgao_disponivel (id_doador, id_tipo_orgao, id_hospital,
                                      data_captacao, status, observacao)
        VALUES (:id_doador, :id_tipo_orgao, :id_hospital,
                :data_captacao, :status, :observacao)
    """, dados)
    return cursor.lastrowid


def atualizar_status_orgao(conexao, id_orgao, status):
    cursor = db.executar(conexao,
                         "UPDATE orgao_disponivel SET status = ? WHERE id_orgao = ?",
                         (status, id_orgao))
    return cursor.rowcount


def buscar_orgao(conexao, id_orgao):
    return db.consultar_um(conexao, """
        SELECT o.id_orgao, t.nome AS orgao, o.id_tipo_orgao, o.status,
               o.id_hospital, d.nome AS doador,
               d.tipo_sanguineo || d.fator_rh AS sangue
          FROM orgao_disponivel o
          JOIN doador     d ON d.id_doador     = o.id_doador
          JOIN tipo_orgao t ON t.id_tipo_orgao = o.id_tipo_orgao
         WHERE o.id_orgao = ?
    """, (id_orgao,))


# ---------------------------------------------------------------------------
# FILA DE ESPERA
# ---------------------------------------------------------------------------
def listar_fila(conexao, status="AGUARDANDO", id_tipo_orgao=None):
    condicoes = []
    parametros = []
    if status:
        condicoes.append("status = ?")
        parametros.append(status)
    if id_tipo_orgao:
        condicoes.append("""id_fila IN (SELECT id_fila FROM fila_espera
                                         WHERE id_tipo_orgao = ?)""")
        parametros.append(id_tipo_orgao)
    filtro = ("WHERE " + " AND ".join(condicoes)) if condicoes else ""
    return db.consultar(conexao, """
        SELECT id_fila, receptor, sangue, orgao, prioridade,
               data_entrada, dias_na_fila, status, hospital
          FROM vw_fila_detalhada
         {filtro}
         ORDER BY {ordem}, data_entrada
    """.format(filtro=filtro, ordem=ORDEM_PRIORIDADE), tuple(parametros))


def inserir_na_fila(conexao, dados):
    cursor = db.executar(conexao, """
        INSERT INTO fila_espera (id_receptor, id_tipo_orgao, prioridade,
                                 data_entrada, status)
        VALUES (:id_receptor, :id_tipo_orgao, :prioridade, :data_entrada, 'AGUARDANDO')
    """, dados)
    return cursor.lastrowid


def atualizar_prioridade(conexao, id_fila, prioridade):
    cursor = db.executar(conexao,
                         "UPDATE fila_espera SET prioridade = ? WHERE id_fila = ?",
                         (prioridade, id_fila))
    return cursor.rowcount


def atualizar_status_fila(conexao, id_fila, status):
    cursor = db.executar(conexao,
                         "UPDATE fila_espera SET status = ? WHERE id_fila = ?",
                         (status, id_fila))
    return cursor.rowcount


def buscar_item_fila(conexao, id_fila):
    return db.consultar_um(conexao, """
        SELECT f.id_fila, f.id_receptor, f.id_tipo_orgao, f.prioridade, f.status,
               r.nome AS receptor, t.nome AS orgao
          FROM fila_espera f
          JOIN receptor   r ON r.id_receptor   = f.id_receptor
          JOIN tipo_orgao t ON t.id_tipo_orgao = f.id_tipo_orgao
         WHERE f.id_fila = ?
    """, (id_fila,))


# ---------------------------------------------------------------------------
# COMPATIBILIDADE (requisito central do sistema)
# ---------------------------------------------------------------------------
def compatibilidade_geral(conexao):
    """Todos os cruzamentos orgao disponivel x receptor na fila."""
    return db.consultar(conexao, """
        SELECT id_orgao, orgao, doador, sangue_doador, hospital_orgao,
               receptor, sangue_receptor, prioridade, dias_na_fila,
               hospital_receptor
          FROM vw_compatibilidade
         ORDER BY orgao, {ordem}, dias_na_fila DESC
    """.format(ordem=ORDEM_PRIORIDADE))


def compativeis_para_orgao(conexao, id_orgao):
    """Candidatos compativeis com um orgao, em ordem de alocacao."""
    return db.consultar(conexao, """
        SELECT id_fila, id_receptor, receptor, sangue_receptor, prioridade,
               data_entrada, dias_na_fila, hospital_receptor
          FROM vw_compatibilidade
         WHERE id_orgao = ?
         ORDER BY {ordem}, dias_na_fila DESC
    """.format(ordem=ORDEM_PRIORIDADE), (id_orgao,))


def candidatos_por_orgao(conexao):
    """Quantos candidatos compativeis cada orgao disponivel possui."""
    return db.consultar(conexao, """
        SELECT o.id_orgao, t.nome AS orgao,
               d.tipo_sanguineo || d.fator_rh AS sangue_doador,
               o.data_captacao, h.nome AS hospital,
               (SELECT COUNT(*) FROM vw_compatibilidade v
                 WHERE v.id_orgao = o.id_orgao) AS candidatos
          FROM orgao_disponivel o
          JOIN doador     d ON d.id_doador     = o.id_doador
          JOIN tipo_orgao t ON t.id_tipo_orgao = o.id_tipo_orgao
          JOIN hospital   h ON h.id_hospital   = o.id_hospital
         WHERE o.status = 'DISPONIVEL'
         ORDER BY candidatos DESC, o.data_captacao
    """)


def sem_compatibilidade(conexao):
    """Receptores aguardando sem nenhum orgao compativel disponivel hoje."""
    return db.consultar(conexao, """
        SELECT receptor, sangue, orgao, prioridade, dias_na_fila, hospital
          FROM vw_fila_detalhada
         WHERE status = 'AGUARDANDO'
           AND id_fila NOT IN (SELECT id_fila FROM vw_compatibilidade)
         ORDER BY {ordem}, dias_na_fila DESC
    """.format(ordem=ORDEM_PRIORIDADE))


def regras_compatibilidade(conexao):
    return db.consultar(conexao, """
        SELECT ca.abo_doador || cr.rh_doador     AS doador,
               ca.abo_receptor || cr.rh_receptor AS receptor
          FROM compat_abo ca
         CROSS JOIN compat_rh cr
         ORDER BY doador, receptor
    """)


# ---------------------------------------------------------------------------
# TRANSPLANTES
# ---------------------------------------------------------------------------
def listar_transplantes(conexao):
    return db.consultar(conexao, """
        SELECT tr.id_transplante, t.nome AS orgao, d.nome AS doador,
               r.nome AS receptor, tr.data_cirurgia, tr.cirurgiao,
               tr.resultado, h.nome AS hospital
          FROM transplante tr
          JOIN orgao_disponivel o ON o.id_orgao      = tr.id_orgao
          JOIN tipo_orgao  t ON t.id_tipo_orgao = o.id_tipo_orgao
          JOIN doador      d ON d.id_doador     = o.id_doador
          JOIN receptor    r ON r.id_receptor   = tr.id_receptor
          JOIN hospital    h ON h.id_hospital   = tr.id_hospital
         ORDER BY tr.data_cirurgia DESC
    """)


def registrar_transplante(conexao, id_orgao, id_fila, dados):
    """Efetiva um transplante em uma unica transacao:

    1) INSERT em transplante
    2) UPDATE do orgao  -> TRANSPLANTADO
    3) UPDATE da fila   -> TRANSPLANTADO
    """
    try:
        cursor = conexao.execute("""
            INSERT INTO transplante (id_orgao, id_receptor, id_hospital,
                                     data_cirurgia, cirurgiao, resultado)
            VALUES (:id_orgao, :id_receptor, :id_hospital,
                    :data_cirurgia, :cirurgiao, 'EM_ACOMPANHAMENTO')
        """, dados)
        novo = cursor.lastrowid
        conexao.execute("UPDATE orgao_disponivel SET status = 'TRANSPLANTADO' "
                        "WHERE id_orgao = ?", (id_orgao,))
        conexao.execute("UPDATE fila_espera SET status = 'TRANSPLANTADO' "
                        "WHERE id_fila = ?", (id_fila,))
        conexao.commit()
        return novo
    except Exception:
        conexao.rollback()
        raise


def atualizar_resultado_transplante(conexao, id_transplante, resultado):
    cursor = db.executar(conexao,
                         "UPDATE transplante SET resultado = ? WHERE id_transplante = ?",
                         (resultado, id_transplante))
    return cursor.rowcount


# ---------------------------------------------------------------------------
# INDICADORES
# ---------------------------------------------------------------------------
def painel(conexao):
    return db.consultar_um(conexao, """
        SELECT (SELECT COUNT(*) FROM doador)   AS doadores,
               (SELECT COUNT(*) FROM receptor) AS receptores,
               (SELECT COUNT(*) FROM orgao_disponivel WHERE status = 'DISPONIVEL') AS orgaos_disponiveis,
               (SELECT COUNT(*) FROM orgao_disponivel WHERE status = 'RESERVADO')  AS orgaos_reservados,
               (SELECT COUNT(*) FROM fila_espera WHERE status = 'AGUARDANDO')      AS na_fila,
               (SELECT COUNT(*) FROM fila_espera WHERE status = 'AGUARDANDO'
                                                   AND prioridade = 'EMERGENCIA')  AS emergencias,
               (SELECT COUNT(*) FROM transplante) AS transplantes,
               (SELECT COUNT(*) FROM vw_compatibilidade) AS cruzamentos_compativeis
    """)


def fila_por_orgao(conexao):
    return db.consultar(conexao, """
        SELECT t.nome AS orgao,
               COUNT(f.id_fila) AS aguardando,
               SUM(CASE WHEN f.prioridade = 'EMERGENCIA' THEN 1 ELSE 0 END) AS emergencias,
               CAST(AVG(julianday('now') - julianday(f.data_entrada)) AS INTEGER) AS media_dias,
               (SELECT COUNT(*) FROM orgao_disponivel o
                 WHERE o.id_tipo_orgao = t.id_tipo_orgao AND o.status = 'DISPONIVEL') AS disponiveis
          FROM fila_espera f
          JOIN tipo_orgao t ON t.id_tipo_orgao = f.id_tipo_orgao
         WHERE f.status = 'AGUARDANDO'
         GROUP BY t.id_tipo_orgao
         ORDER BY aguardando DESC
    """)


def transplantes_por_hospital(conexao):
    return db.consultar(conexao, """
        SELECT h.nome AS hospital, COUNT(tr.id_transplante) AS transplantes,
               SUM(CASE WHEN tr.resultado = 'SUCESSO' THEN 1 ELSE 0 END) AS sucessos
          FROM hospital h
          LEFT JOIN transplante tr ON tr.id_hospital = h.id_hospital
         GROUP BY h.id_hospital
         ORDER BY transplantes DESC
    """)
