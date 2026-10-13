# -*- coding: utf-8 -*-
"""GESTAO HOSPITALAR - ponto de entrada do projeto.

Menu inicial para escolher entre os menus de terminal dos dois sistemas e a
interface grafica.

Execucao:
    python3 main.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import db, ui


@ui.submenu
def abrir_diario():
    from DiarioPessoal import DiarioPessoal
    DiarioPessoal.principal()


@ui.submenu
def abrir_central():
    from CentralHospitalar import CentralHospitalar
    CentralHospitalar.principal()


@ui.submenu
def abrir_interface_grafica():
    try:
        import tkinter  # noqa: F401
    except ImportError:
        ui.aviso("Tkinter nao esta disponivel nesta instalacao do Python.")
        ui.pausar()
        return
    import gui
    gui.principal()


def criar_bancos():
    ui.secao("Criacao dos bancos de dados")
    for nome in ("diario", "central"):
        conexao = db.conectar(nome)
        tabelas = db.consultar(conexao, """
            SELECT COUNT(*) AS total FROM sqlite_master WHERE type = 'table'
        """)[0]["total"]
        print("\n  {0:8} -> {1}".format(nome, db.caminho_banco(nome)))
        print("  {0:8}    script: {1}".format("", os.path.basename(db.caminho_script(nome))))
        print("  {0:8}    tabelas: {1}".format("", tabelas))
        conexao.close()
    ui.sucesso("Bancos prontos para uso.")


def principal():
    ui.executar_menu("GESTAO HOSPITALAR", [
        ("Diario de Saude Pessoal (terminal)", abrir_diario),
        ("Central Hospitalar de Transplantes (terminal)", abrir_central),
        ("Interface grafica (Tkinter)", abrir_interface_grafica),
        ("Criar / verificar os bancos de dados", criar_bancos),
    ], subtitulo="Trabalho de Banco de Dados - SQLite 3", rotulo_saida="Sair")
    print("\n  Encerrado.\n")


if __name__ == "__main__":
    principal()
