# -*- coding: utf-8 -*-
"""Ponto de entrada do projeto.

Escolhe entre as tres interfaces, todas sobre o mesmo backend PostgreSQL:

    menus de terminal   terminal/
    interface grafica   gui.py
    front web           API/api.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.erros import ErroDeConexao
from terminal import ui


@ui.submenu
def abrir_diario():
    from terminal import diario
    diario.principal()


@ui.submenu
def abrir_central():
    from terminal import central
    central.principal()


@ui.submenu
def abrir_interface_grafica():
    os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")
    try:
        import tkinter  # noqa: F401
    except ImportError:
        from terminal.tk_ausente import explicar
        explicar()
        ui.pausar()
        return
    import gui
    gui.principal()


@ui.submenu
def abrir_front_web():
    ui.secao("Front web")
    porta = ui.ler_inteiro("Porta", minimo=1024, maximo=65535, padrao=8000)
    print("\n  Abra http://localhost:{0} no navegador.".format(porta))
    print("  Encerre o servidor com Ctrl+C para voltar ao menu.\n")
    from API import api
    try:
        api.principal(porta)
    except KeyboardInterrupt:
        pass


def verificar_bancos():
    ui.secao("Conexao com o PostgreSQL")
    from backend.conexao import (BANCO_CENTRAL, BANCO_DIARIO, conectar_central,
                                 conectar_diario)
    for nome, abrir in (("Diario de Saude", conectar_diario),
                        ("Central de Transplantes", conectar_central)):
        try:
            conexao = abrir()
            with conexao.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) AS total FROM information_schema.tables
                     WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """)
                total = cursor.fetchone()["total"]
            conexao.close()
            print("\n  {0:26} OK ({1} tabelas)".format(nome, total))
        except ErroDeConexao as erro:
            ui.aviso("{0}: {1}".format(nome, erro))
            print("\n  Crie os bancos com:  python criar_bancos.py")
            return
    print("\n  Bancos: {0} e {1}".format(BANCO_DIARIO, BANCO_CENTRAL))
    ui.sucesso("Tudo pronto para uso.")


def principal():
    ui.executar_menu("GESTAO HOSPITALAR", [
        ("Diario de Saude Pessoal (terminal)", abrir_diario),
        ("Central Hospitalar de Transplantes (terminal)", abrir_central),
        ("Interface grafica (Tkinter)", abrir_interface_grafica),
        ("Front web (navegador)", abrir_front_web),
        ("Verificar conexao com os bancos", verificar_bancos),
    ], subtitulo="Trabalho de Banco de Dados - PostgreSQL", rotulo_saida="Sair")
    print("\n  Encerrado.\n")


if __name__ == "__main__":
    try:
        principal()
    except ErroDeConexao as erro:
        print("\n  {0}\n".format(erro))
        print("  Crie os bancos com:  python criar_bancos.py\n")
        raise SystemExit(1)
