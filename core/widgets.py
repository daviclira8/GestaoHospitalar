# -*- coding: utf-8 -*-
"""Componentes reutilizaveis da interface grafica (Tkinter/ttk).

Tabela     -> Treeview com barras de rolagem e preenchimento a partir de
              linhas sqlite3.Row.
Formulario -> janela modal que monta um formulario a partir de uma lista de
              campos e devolve um dicionario com os valores digitados.
"""

import re
import tkinter as tk
from tkinter import messagebox, ttk

TIPOS_SANGUINEOS = ("A", "B", "AB", "O")
FATORES_RH = ("+", "-")

CORES = {
    "fundo": "#f4f6f8",
    "destaque": "#1f6f8b",
    "texto_claro": "#ffffff",
    "alerta": "#b3261e",
}


class Tabela(ttk.Frame):
    """Treeview com rolagem vertical/horizontal e linhas zebradas."""

    def __init__(self, master, colunas, titulos=None, larguras=None, altura=12):
        ttk.Frame.__init__(self, master)
        self.colunas = list(colunas)
        titulos = titulos or [c.replace("_", " ").upper() for c in colunas]

        self.tree = ttk.Treeview(self, columns=self.colunas, show="headings",
                                 height=altura, selectmode="browse")
        for indice, coluna in enumerate(self.colunas):
            self.tree.heading(coluna, text=titulos[indice])
            largura = larguras[indice] if larguras else 120
            self.tree.column(coluna, width=largura, anchor="w", stretch=True)

        vertical = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        horizontal = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self._callback_selecao = None
        self.tree.tag_configure("par", background="#eef2f5")
        self.tree.tag_configure("impar", background="#ffffff")
        self.tree.tag_configure("urgente", foreground=CORES["alerta"])

    # -- dados ---------------------------------------------------------------
    def preencher(self, linhas, destacar=None):
        """Recarrega a tabela. 'destacar' recebe a linha e devolve True/False."""
        self.limpar()
        for indice, linha in enumerate(linhas):
            valores = []
            for coluna in self.colunas:
                valor = linha[coluna] if coluna in linha.keys() else ""
                valores.append("" if valor is None else valor)
            tags = ["par" if indice % 2 else "impar"]
            if destacar is not None and destacar(linha):
                tags.append("urgente")
            self.tree.insert("", "end", values=valores, tags=tuple(tags))

    def limpar(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def selecionado(self, coluna):
        """Valor de uma coluna na linha selecionada (ou None)."""
        selecao = self.tree.selection()
        if not selecao:
            return None
        valores = self.tree.item(selecao[0], "values")
        return valores[self.colunas.index(coluna)]

    def selecionado_int(self, coluna):
        valor = self.selecionado(coluna)
        return int(valor) if valor not in (None, "") else None

    def ao_selecionar(self, funcao):
        self._callback_selecao = funcao
        self.tree.bind("<<TreeviewSelect>>", lambda evento: funcao())

    def ao_clique_duplo(self, funcao):
        self.tree.bind("<Double-1>", lambda evento: funcao())

    def selecionar_primeiro(self):
        """Seleciona a primeira linha e dispara o callback de selecao."""
        itens = self.tree.get_children()
        if not itens:
            return False
        self.tree.selection_set(itens[0])
        self.tree.focus(itens[0])
        if self._callback_selecao is not None:
            self._callback_selecao()
        return True


class Formulario(tk.Toplevel):
    """Janela modal de formulario.

    campos: lista de dicionarios
        {"chave": "nome", "rotulo": "Nome", "tipo": "texto"}
        tipos: texto | memo | data | data_hora | inteiro | opcao | lista
        "opcoes"  -> tupla de valores (tipo opcao)
        "itens"   -> lista de (id, descricao) (tipo lista)
        "padrao"  -> valor inicial
        "obrigatorio" -> default True
    Apos a janela fechar, 'resultado' contem o dicionario ou None.
    """

    def __init__(self, master, titulo, campos):
        tk.Toplevel.__init__(self, master)
        self.title(titulo)
        self.resizable(False, False)
        self.campos = campos
        self.resultado = None
        self._entradas = {}

        quadro = ttk.Frame(self, padding=16)
        quadro.pack(fill="both", expand=True)
        ttk.Label(quadro, text=titulo, font=("TkDefaultFont", 13, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        for indice, campo in enumerate(campos, start=1):
            rotulo = campo["rotulo"]
            if campo.get("obrigatorio", True):
                rotulo += " *"
            ttk.Label(quadro, text=rotulo).grid(row=indice, column=0, sticky="w",
                                                padx=(0, 10), pady=4)
            self._entradas[campo["chave"]] = self._criar_entrada(quadro, campo, indice)

        botoes = ttk.Frame(quadro)
        botoes.grid(row=len(campos) + 1, column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(botoes, text="Cancelar", command=self.destroy).pack(side="left", padx=4)
        ttk.Button(botoes, text="Salvar", command=self._salvar).pack(side="left")

        self.bind("<Return>", lambda evento: self._salvar())
        self.bind("<Escape>", lambda evento: self.destroy())
        self.transient(master)
        self.grab_set()
        self.update_idletasks()
        self._centralizar(master)
        if campos:
            primeiro = self._entradas[campos[0]["chave"]]
            try:
                primeiro.focus_set()
            except tk.TclError:
                pass
        self.wait_window(self)

    # -- construcao ----------------------------------------------------------
    def _criar_entrada(self, quadro, campo, linha):
        tipo = campo.get("tipo", "texto")
        padrao = campo.get("padrao")

        if tipo == "opcao":
            variavel = tk.StringVar(value=padrao or campo["opcoes"][0])
            combo = ttk.Combobox(quadro, textvariable=variavel, state="readonly",
                                 values=list(campo["opcoes"]), width=32)
            combo.grid(row=linha, column=1, sticky="ew", pady=4)
            combo.variavel = variavel
            return combo

        if tipo == "lista":
            itens = campo["itens"]
            descricoes = ["{0} - {1}".format(i[0], i[1]) for i in itens]
            variavel = tk.StringVar(value=descricoes[0] if descricoes else "")
            combo = ttk.Combobox(quadro, textvariable=variavel, state="readonly",
                                 values=descricoes, width=32)
            combo.grid(row=linha, column=1, sticky="ew", pady=4)
            combo.variavel = variavel
            return combo

        if tipo == "memo":
            texto = tk.Text(quadro, width=34, height=3)
            if padrao:
                texto.insert("1.0", padrao)
            texto.grid(row=linha, column=1, sticky="ew", pady=4)
            return texto

        entrada = ttk.Entry(quadro, width=34)
        if padrao is not None:
            entrada.insert(0, str(padrao))
        entrada.grid(row=linha, column=1, sticky="ew", pady=4)
        return entrada

    def _centralizar(self, master):
        try:
            x = master.winfo_rootx() + (master.winfo_width() - self.winfo_width()) // 2
            y = master.winfo_rooty() + (master.winfo_height() - self.winfo_height()) // 3
            self.geometry("+{0}+{1}".format(max(x, 0), max(y, 0)))
        except tk.TclError:
            pass

    # -- validacao -----------------------------------------------------------
    def _valor(self, campo):
        componente = self._entradas[campo["chave"]]
        tipo = campo.get("tipo", "texto")
        if tipo in ("opcao", "lista"):
            return componente.variavel.get().strip()
        if tipo == "memo":
            return componente.get("1.0", "end").strip()
        return componente.get().strip()

    def _salvar(self):
        dados = {}
        for campo in self.campos:
            chave = campo["chave"]
            tipo = campo.get("tipo", "texto")
            valor = self._valor(campo)
            obrigatorio = campo.get("obrigatorio", True)

            if not valor:
                if obrigatorio:
                    messagebox.showwarning(
                        "Campo obrigatorio",
                        "Preencha o campo '{0}'.".format(campo["rotulo"]), parent=self)
                    return
                dados[chave] = None
                continue

            if tipo == "lista":
                dados[chave] = int(valor.split(" - ")[0])
                continue
            if tipo == "inteiro":
                try:
                    dados[chave] = int(valor)
                except ValueError:
                    messagebox.showwarning("Valor invalido",
                                           "'{0}' deve ser um numero inteiro.".format(
                                               campo["rotulo"]), parent=self)
                    return
                continue
            if tipo == "data" and not re.match(r"^\d{4}-\d{2}-\d{2}$", valor):
                messagebox.showwarning("Data invalida",
                                       "Use o formato YYYY-MM-DD em '{0}'.".format(
                                           campo["rotulo"]), parent=self)
                return
            if tipo == "data_hora" and not re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", valor):
                messagebox.showwarning("Data/hora invalida",
                                       "Use o formato YYYY-MM-DD HH:MM em '{0}'.".format(
                                           campo["rotulo"]), parent=self)
                return
            dados[chave] = valor

        self.resultado = dados
        self.destroy()


def campo(chave, rotulo, tipo="texto", obrigatorio=True, opcoes=None,
          itens=None, padrao=None):
    """Atalho para montar a definicao de um campo de formulario."""
    definicao = {"chave": chave, "rotulo": rotulo, "tipo": tipo,
                 "obrigatorio": obrigatorio}
    if opcoes is not None:
        definicao["opcoes"] = opcoes
    if itens is not None:
        definicao["itens"] = itens
    if padrao is not None:
        definicao["padrao"] = padrao
    return definicao


def barra_titulo(master, texto, subtitulo=None):
    """Faixa de titulo usada no topo das abas."""
    quadro = tk.Frame(master, bg=CORES["destaque"])
    tk.Label(quadro, text=texto, bg=CORES["destaque"], fg=CORES["texto_claro"],
             font=("TkDefaultFont", 14, "bold")).pack(anchor="w", padx=14, pady=(10, 0))
    if subtitulo:
        tk.Label(quadro, text=subtitulo, bg=CORES["destaque"], fg="#d7e6ec",
                 font=("TkDefaultFont", 10)).pack(anchor="w", padx=14, pady=(0, 10))
    return quadro


def cartao_indicador(master, rotulo, valor, destaque=False):
    """Pequeno cartao com um numero para os paineis de indicadores."""
    cor = CORES["alerta"] if destaque else CORES["destaque"]
    quadro = tk.Frame(master, bg="white", highlightbackground="#cbd5da",
                      highlightthickness=1)
    tk.Label(quadro, text=str(valor), bg="white", fg=cor,
             font=("TkDefaultFont", 22, "bold")).pack(padx=18, pady=(12, 0))
    tk.Label(quadro, text=rotulo, bg="white", fg="#4a5a63",
             font=("TkDefaultFont", 9)).pack(padx=18, pady=(0, 12))
    return quadro
