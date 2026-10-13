# -*- coding: utf-8 -*-
"""Camada de acesso ao banco de dados (SQLite).

Cada sistema tem o seu proprio arquivo de banco, criado a partir do script SQL
correspondente:

    DiarioPessoal/bdDiarioPessoal.sql        -> data/diario_saude.db
    CentralHospitalar/bdCentralHospitalar.sql -> data/central_transplantes.db
"""

import os
import sqlite3

# Raiz do projeto (pasta que contem este arquivo esta um nivel abaixo)
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_DADOS = os.path.join(RAIZ, "data")

# nome logico -> (script SQL de criacao, arquivo do banco)
BANCOS = {
    "diario": (
        os.path.join(RAIZ, "DiarioPessoal", "bdDiarioPessoal.sql"),
        os.path.join(PASTA_DADOS, "diario_saude.db"),
    ),
    "central": (
        os.path.join(RAIZ, "CentralHospitalar", "bdCentralHospitalar.sql"),
        os.path.join(PASTA_DADOS, "central_transplantes.db"),
    ),
}


def caminho_banco(nome):
    return BANCOS[nome][1]


def caminho_script(nome):
    return BANCOS[nome][0]


def conectar(nome):
    """Abre uma conexao, criando o banco a partir do .sql na primeira vez."""
    script, arquivo = BANCOS[nome]
    if not os.path.isdir(PASTA_DADOS):
        os.makedirs(PASTA_DADOS)
    precisa_criar = not os.path.exists(arquivo)

    conexao = sqlite3.connect(arquivo)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")

    if precisa_criar:
        _executar_script(conexao, script)
    return conexao


def recriar(nome):
    """Apaga e recria o banco, voltando aos dados ficticios originais."""
    script, arquivo = BANCOS[nome]
    if os.path.exists(arquivo):
        os.remove(arquivo)
    return conectar(nome)


def _executar_script(conexao, script):
    with open(script, "r", encoding="utf-8") as arq:
        conexao.executescript(arq.read())
    conexao.commit()


def consultar(conexao, sql, parametros=()):
    """Executa um SELECT e devolve a lista de linhas (sqlite3.Row)."""
    return conexao.execute(sql, parametros).fetchall()


def consultar_um(conexao, sql, parametros=()):
    """Executa um SELECT e devolve a primeira linha ou None."""
    return conexao.execute(sql, parametros).fetchone()


def executar(conexao, sql, parametros=()):
    """Executa INSERT/UPDATE/DELETE, confirma a transacao e devolve o cursor.

    cursor.lastrowid  -> id gerado no INSERT
    cursor.rowcount   -> linhas afetadas no UPDATE/DELETE
    """
    cursor = conexao.execute(sql, parametros)
    conexao.commit()
    return cursor
