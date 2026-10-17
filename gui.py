# -*- coding: utf-8 -*-
"""Interface gráfica integrada do Diário de Saúde e da Central."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except ImportError:
    print("Tkinter não está disponível neste Python. Instale o suporte a Tk.")
    raise SystemExit(1)

from backend.central.servico import CentralService
from backend.diario.servico import DiarioService
from backend.central.interface import AbaCentral
from backend.diario.interface import AbaDiario


class Aplicacao(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestão Hospitalar")
        self.geometry("1180x740")
        self.minsize(900, 560)
        self.diario = DiarioService()
        try:
            self.central = CentralService()
        except Exception:
            self.diario.fechar()
            raise

        estilo = ttk.Style(self)
        if "clam" in estilo.theme_names():
            estilo.theme_use("clam")
        estilo.configure("TNotebook.Tab", padding=(14, 7))
        estilo.configure("Treeview", rowheight=24)

        abas = ttk.Notebook(self)
        abas.pack(fill="both", expand=True, padx=8, pady=8)
        abas.add(AbaDiario(abas, self.diario), text="Diário de Saúde")
        abas.add(AbaCentral(abas, self.central), text="Central Hospitalar")
        ttk.Label(self, text="PostgreSQL | API web: python API/api.py",
                  relief="sunken", anchor="w", padding=(8, 4)).pack(fill="x", side="bottom")
        self.protocol("WM_DELETE_WINDOW", self.encerrar)

    def encerrar(self):
        try:
            self.central.fechar()
            self.diario.fechar()
        except Exception as erro:
            messagebox.showerror("Falha ao encerrar conexões", str(erro), parent=self)
        finally:
            self.destroy()


def principal():
    Aplicacao().mainloop()


if __name__ == "__main__":
    principal()
