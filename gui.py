# -*- coding: utf-8 -*-
"""GESTAO HOSPITALAR - interface grafica (Tkinter).

Reune os dois sistemas em uma unica janela, cada um em sua aba:
    - Diario de Saude Pessoal        (data/diario_saude.db)
    - Central Hospitalar de Transplantes (data/central_transplantes.db)

Execucao:
    python3 gui.py
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import db, widgets as w
from CentralHospitalar.interface import AbaCentral
from DiarioPessoal.interface import AbaDiario


class Aplicacao(tk.Tk):

    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Gestao Hospitalar - Diario de Saude e Central de Transplantes")
        self.geometry("1180x720")
        self.minsize(960, 600)
        self.configure(bg=w.CORES["fundo"])

        self._configurar_estilo()
        self.conexao_diario = db.conectar("diario")
        self.conexao_central = db.conectar("central")

        self._montar_menu()

        self.abas = ttk.Notebook(self)
        self.abas.pack(fill="both", expand=True, padx=8, pady=8)

        self.aba_diario = AbaDiario(self.abas, self.conexao_diario)
        self.aba_central = AbaCentral(self.abas, self.conexao_central)
        self.abas.add(self.aba_diario, text="  Diario de Saude Pessoal  ")
        self.abas.add(self.aba_central, text="  Central de Transplantes  ")

        self.barra_status = ttk.Label(
            self, relief="sunken", anchor="w", padding=(8, 4),
            text="SQLite 3  |  {0}  |  {1}".format(
                db.caminho_banco("diario"), db.caminho_banco("central")))
        self.barra_status.pack(fill="x", side="bottom")

        self.protocol("WM_DELETE_WINDOW", self.encerrar)

    def _configurar_estilo(self):
        estilo = ttk.Style(self)
        if "clam" in estilo.theme_names():
            estilo.theme_use("clam")
        estilo.configure("TNotebook.Tab", padding=(14, 7))
        estilo.configure("Treeview", rowheight=22)
        estilo.configure("Treeview.Heading", font=("TkDefaultFont", 9, "bold"))
        estilo.configure("TLabelframe.Label", foreground=w.CORES["destaque"],
                         font=("TkDefaultFont", 10, "bold"))

    def _montar_menu(self):
        barra = tk.Menu(self)

        arquivo = tk.Menu(barra, tearoff=0)
        arquivo.add_command(label="Atualizar dados (F5)", command=self.recarregar)
        arquivo.add_separator()
        arquivo.add_command(label="Recriar banco do Diario",
                            command=lambda: self.recriar("diario"))
        arquivo.add_command(label="Recriar banco da Central",
                            command=lambda: self.recriar("central"))
        arquivo.add_separator()
        arquivo.add_command(label="Sair", command=self.encerrar)
        barra.add_cascade(label="Arquivo", menu=arquivo)

        ajuda = tk.Menu(barra, tearoff=0)
        ajuda.add_command(label="Sobre o projeto", command=self.sobre)
        barra.add_cascade(label="Ajuda", menu=ajuda)

        self.config(menu=barra)
        self.bind("<F5>", lambda evento: self.recarregar())

    # ------------------------------------------------------------------ acoes
    def recarregar(self):
        self.aba_diario.recarregar()
        self.aba_central.recarregar()

    def recriar(self, nome):
        rotulos = {"diario": "Diario de Saude Pessoal",
                   "central": "Central Hospitalar de Transplantes"}
        if not messagebox.askyesno(
                "Recriar banco",
                "Apagar e recriar o banco do {0}?\n\n"
                "Todos os registros inseridos serao perdidos e o script SQL "
                "original sera executado novamente.".format(rotulos[nome]),
                parent=self):
            return
        if nome == "diario":
            self.conexao_diario.close()
            self.conexao_diario = db.recriar("diario")
            self.aba_diario.conexao = self.conexao_diario
            self.aba_diario.id_usuario = None
        else:
            self.conexao_central.close()
            self.conexao_central = db.recriar("central")
            self.aba_central.conexao = self.conexao_central
        self.recarregar()
        messagebox.showinfo("Banco recriado",
                            "Banco do {0} recriado com os dados ficticios "
                            "originais.".format(rotulos[nome]), parent=self)

    def sobre(self):
        messagebox.showinfo("Sobre o projeto", (
            "Gestao Hospitalar\n\n"
            "Sistema 1 - Diario de Saude Pessoal\n"
            "Sistema 2 - Central Hospitalar de Transplantes\n\n"
            "SGBD: SQLite 3\n"
            "Interface grafica: Tkinter\n"
            "Menus de terminal: DiarioPessoal.py e CentralHospitalar.py\n\n"
            "Scripts SQL (DDL + DML):\n"
            "  DiarioPessoal/bdDiarioPessoal.sql\n"
            "  CentralHospitalar/bdCentralHospitalar.sql"), parent=self)

    def encerrar(self):
        try:
            self.conexao_diario.close()
            self.conexao_central.close()
        finally:
            self.destroy()


def principal():
    Aplicacao().mainloop()


if __name__ == "__main__":
    principal()
