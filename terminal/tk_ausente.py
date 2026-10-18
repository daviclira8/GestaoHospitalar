# -*- coding: utf-8 -*-
"""Mensagem de ajuda quando o Python em uso nao possui Tkinter.

O Tkinter faz parte da biblioteca padrao, mas depende da biblioteca grafica
Tk, que nem sempre e instalada junto com o interpretador. No macOS, o Python
do Homebrew distribui o Tk em um pacote separado (python-tk); em distribuicoes
Linux, no pacote python3-tk.

Importante: apenas a interface grafica depende do Tkinter. Os menus de
terminal e o front web funcionam em qualquer instalacao do Python 3.
"""

import os
import subprocess
import sys


def _python_com_tkinter():
    """Procura outro interpretador instalado que tenha Tkinter."""
    candidatos = [
        "/usr/bin/python3",
        "/usr/local/bin/python3",
        "/opt/homebrew/bin/python3",
        "/usr/bin/python3.9",
    ]
    atual = os.path.realpath(sys.executable)
    for caminho in candidatos:
        if not os.path.exists(caminho) or os.path.realpath(caminho) == atual:
            continue
        try:
            subprocess.check_output([caminho, "-c", "import tkinter"],
                                    stderr=subprocess.STDOUT, timeout=15)
            return caminho
        except Exception:
            continue
    return None


def _comando_de_instalacao():
    if sys.platform == "darwin":
        versao = "{0}.{1}".format(*sys.version_info[:2])
        return "brew install python-tk@{0}".format(versao)
    if sys.platform.startswith("linux"):
        return "sudo apt install python3-tk"
    return None


def explicar(saida=None):
    """Imprime o diagnostico e as alternativas disponiveis."""
    escrever = (saida or sys.stdout).write
    linha = "=" * 70

    escrever("\n{0}\n".format(linha))
    escrever("  INTERFACE GRAFICA INDISPONIVEL: este Python nao possui Tkinter\n")
    escrever("{0}\n\n".format(linha))
    escrever("  Interpretador em uso:\n    {0}  (Python {1}.{2})\n\n".format(
        sys.executable, *sys.version_info[:2]))
    escrever("  O Tkinter depende da biblioteca grafica Tk, que nao foi\n"
             "  instalada junto com este interpretador.\n\n")

    escrever("  Como resolver (qualquer uma das opcoes):\n\n")

    outro = _python_com_tkinter()
    if outro:
        escrever("  1. Rodar com o outro Python ja instalado, que tem Tkinter:\n")
        escrever("       {0} gui.py\n\n".format(outro))

    comando = _comando_de_instalacao()
    if comando:
        escrever("  {0}. Instalar o Tk para este Python:\n".format(2 if outro else 1))
        escrever("       {0}\n\n".format(comando))

    escrever("  {0}. Usar o front web, que nao depende de Tkinter:\n".format(
        3 if (outro and comando) else 2))
    escrever("       {0} API/api.py\n".format(sys.executable))
    escrever("       e abrir http://localhost:8000 no navegador\n\n")
    escrever("  Os menus de terminal tambem funcionam normalmente:\n")
    escrever("       {0} main.py\n\n".format(sys.executable))
