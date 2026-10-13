# -*- coding: utf-8 -*-
"""Interface grafica da Central Hospitalar de Transplantes (aba Tkinter).

Sub-abas: Painel, Doadores, Receptores, Orgaos, Fila de espera,
Compatibilidade (busca doador x receptor) e Transplantes.
"""

import datetime
import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import widgets as w
from CentralHospitalar import repositorio as repo

STATUS_ORGAO = ("DISPONIVEL", "RESERVADO", "TRANSPLANTADO", "DESCARTADO")
PRIORIDADES = ("EMERGENCIA", "ALTA", "NORMAL")
SITUACOES_FILA = ("AGUARDANDO", "TRANSPLANTADO", "SUSPENSO", "OBITO")
RESULTADOS = ("EM_ACOMPANHAMENTO", "SUCESSO", "REJEICAO", "OBITO")


def hoje():
    return datetime.date.today().isoformat()


class AbaCentral(ttk.Frame):

    def __init__(self, master, conexao):
        ttk.Frame.__init__(self, master)
        self.conexao = conexao

        w.barra_titulo(self, "Central Hospitalar de Transplantes",
                       "Doadores, receptores, orgaos disponiveis, filas de espera "
                       "e compatibilidade").pack(fill="x")

        self.abas = ttk.Notebook(self, padding=8)
        self.abas.pack(fill="both", expand=True)
        self.abas.add(self._aba_painel(), text="Painel")
        self.abas.add(self._aba_compatibilidade(), text="Compatibilidade")
        self.abas.add(self._aba_orgaos(), text="Orgaos")
        self.abas.add(self._aba_fila(), text="Fila de espera")
        self.abas.add(self._aba_doadores(), text="Doadores")
        self.abas.add(self._aba_receptores(), text="Receptores")
        self.abas.add(self._aba_transplantes(), text="Transplantes")
        self.recarregar()

    # ----------------------------------------------------------------- painel
    def _aba_painel(self):
        quadro = ttk.Frame(self.abas, padding=8)
        self.painel_indicadores = ttk.Frame(quadro)
        self.painel_indicadores.pack(fill="x", pady=(0, 10))

        colunas = ttk.Frame(quadro)
        colunas.pack(fill="both", expand=True)
        colunas.columnconfigure(0, weight=1)
        colunas.columnconfigure(1, weight=1)
        colunas.rowconfigure(0, weight=1)
        colunas.rowconfigure(1, weight=1)

        esq = ttk.LabelFrame(colunas, text=" Demanda por tipo de orgao ", padding=6)
        esq.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=(0, 6))
        self.tabela_demanda = w.Tabela(
            esq, colunas=["orgao", "aguardando", "emergencias", "media_dias", "disponiveis"],
            titulos=["ORGAO", "AGUARDANDO", "EMERGENCIAS", "MEDIA DIAS", "DISPONIVEIS"],
            larguras=[110, 100, 110, 100, 100], altura=7)
        self.tabela_demanda.pack(fill="both", expand=True)

        dir_ = ttk.LabelFrame(colunas, text=" Candidatos compativeis por orgao ", padding=6)
        dir_.grid(row=0, column=1, sticky="nsew", pady=(0, 6))
        self.tabela_resumo_compat = w.Tabela(
            dir_, colunas=["id_orgao", "orgao", "sangue_doador", "candidatos"],
            titulos=["ID", "ORGAO", "SANGUE", "CANDIDATOS"],
            larguras=[40, 110, 80, 100], altura=7)
        self.tabela_resumo_compat.pack(fill="both", expand=True)

        inf_esq = ttk.LabelFrame(colunas, text=" Receptores sem opcao compativel hoje ", padding=6)
        inf_esq.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        self.tabela_sem_opcao = w.Tabela(
            inf_esq, colunas=["receptor", "sangue", "orgao", "prioridade", "dias_na_fila"],
            titulos=["RECEPTOR", "SANGUE", "ORGAO", "PRIORIDADE", "DIAS"],
            larguras=[150, 70, 100, 100, 60], altura=7)
        self.tabela_sem_opcao.pack(fill="both", expand=True)

        inf_dir = ttk.LabelFrame(colunas, text=" Transplantes por hospital ", padding=6)
        inf_dir.grid(row=1, column=1, sticky="nsew")
        self.tabela_hospitais = w.Tabela(
            inf_dir, colunas=["hospital", "transplantes", "sucessos"],
            titulos=["HOSPITAL", "TRANSPLANTES", "SUCESSOS"],
            larguras=[220, 110, 90], altura=7)
        self.tabela_hospitais.pack(fill="both", expand=True)
        return quadro

    # -------------------------------------------------------- compatibilidade
    def _aba_compatibilidade(self):
        quadro = ttk.Frame(self.abas, padding=8)

        topo = ttk.LabelFrame(quadro, text=" Buscar receptores compativeis ", padding=8)
        topo.pack(fill="x")
        ttk.Label(topo, text="Orgao disponivel:").grid(row=0, column=0, sticky="w")
        self.combo_orgao = ttk.Combobox(topo, state="readonly", width=70)
        self.combo_orgao.grid(row=0, column=1, sticky="ew", padx=8)
        self.combo_orgao.bind("<<ComboboxSelected>>", lambda e: self._buscar_compativeis())
        topo.columnconfigure(1, weight=1)
        ttk.Button(topo, text="Buscar",
                   command=self._buscar_compativeis).grid(row=0, column=2)
        ttk.Label(topo, text="Criterio: mesmo tipo de orgao + compatibilidade ABO e RH. "
                             "Ordem: emergencia, alta, normal e maior tempo de espera.",
                  foreground="#4a5a63").grid(row=1, column=0, columnspan=3,
                                             sticky="w", pady=(8, 0))

        meio = ttk.LabelFrame(quadro, text=" Candidatos em ordem de alocacao ", padding=6)
        meio.pack(fill="both", expand=True, pady=(8, 0))
        self.tabela_compativeis = w.Tabela(
            meio, colunas=["id_fila", "receptor", "sangue_receptor", "prioridade",
                           "data_entrada", "dias_na_fila", "hospital_receptor"],
            titulos=["FILA", "RECEPTOR", "SANGUE", "PRIORIDADE", "ENTRADA",
                     "DIAS", "HOSPITAL"],
            larguras=[50, 170, 70, 110, 100, 60, 220], altura=8)
        self.tabela_compativeis.pack(fill="both", expand=True)

        barra = ttk.Frame(meio)
        barra.pack(fill="x", pady=(8, 0))
        ttk.Button(barra, text="Efetivar transplante",
                   command=self.efetivar_transplante).pack(side="left")
        ttk.Button(barra, text="Reservar orgao",
                   command=self.reservar_orgao).pack(side="left", padx=6)
        ttk.Button(barra, text="Regras de compatibilidade",
                   command=self.mostrar_regras).pack(side="left")

        baixo = ttk.LabelFrame(quadro, text=" Todos os cruzamentos compativeis ", padding=6)
        baixo.pack(fill="both", expand=True, pady=(8, 0))
        self.tabela_todos_cruzamentos = w.Tabela(
            baixo, colunas=["orgao", "doador", "sangue_doador", "receptor",
                            "sangue_receptor", "prioridade", "dias_na_fila"],
            titulos=["ORGAO", "DOADOR", "SANGUE DOADOR", "RECEPTOR",
                     "SANGUE RECEPTOR", "PRIORIDADE", "DIAS"],
            larguras=[100, 150, 110, 150, 120, 100, 60], altura=6)
        self.tabela_todos_cruzamentos.pack(fill="both", expand=True)
        return quadro

    # ----------------------------------------------------------------- orgaos
    def _aba_orgaos(self):
        quadro = ttk.Frame(self.abas, padding=8)

        filtro = ttk.Frame(quadro)
        filtro.pack(fill="x", pady=(0, 6))
        ttk.Label(filtro, text="Status:").pack(side="left")
        self.filtro_status = ttk.Combobox(filtro, state="readonly", width=16,
                                          values=("TODOS",) + STATUS_ORGAO)
        self.filtro_status.set("DISPONIVEL")
        self.filtro_status.pack(side="left", padx=6)
        self.filtro_status.bind("<<ComboboxSelected>>", lambda e: self._carregar_orgaos())

        self.tabela_orgaos = w.Tabela(
            quadro, colunas=["id_orgao", "orgao", "doador", "sangue", "tipo_doador",
                             "data_captacao", "horas_desde_captacao", "isquemia_h",
                             "status", "hospital"],
            titulos=["ID", "ORGAO", "DOADOR", "SANGUE", "DOACAO", "CAPTACAO",
                     "H. DECORRIDAS", "ISQUEMIA", "STATUS", "HOSPITAL"],
            larguras=[40, 90, 150, 70, 80, 120, 110, 80, 110, 200], altura=14)
        self.tabela_orgaos.pack(fill="both", expand=True)

        barra = ttk.Frame(quadro)
        barra.pack(fill="x", pady=(8, 0))
        ttk.Button(barra, text="Registrar orgao captado",
                   command=self.novo_orgao).pack(side="left")
        ttk.Button(barra, text="Alterar status",
                   command=self.alterar_status_orgao).pack(side="left", padx=6)
        ttk.Button(barra, text="Ver compativeis",
                   command=self._ir_para_compatibilidade).pack(side="left")
        return quadro

    # ------------------------------------------------------------------- fila
    def _aba_fila(self):
        quadro = ttk.Frame(self.abas, padding=8)

        filtro = ttk.Frame(quadro)
        filtro.pack(fill="x", pady=(0, 6))
        ttk.Label(filtro, text="Situacao:").pack(side="left")
        self.filtro_fila = ttk.Combobox(filtro, state="readonly", width=16,
                                        values=("TODAS",) + SITUACOES_FILA)
        self.filtro_fila.set("AGUARDANDO")
        self.filtro_fila.pack(side="left", padx=6)
        self.filtro_fila.bind("<<ComboboxSelected>>", lambda e: self._carregar_fila())

        self.tabela_fila = w.Tabela(
            quadro, colunas=["id_fila", "receptor", "sangue", "orgao", "prioridade",
                             "data_entrada", "dias_na_fila", "status", "hospital"],
            titulos=["ID", "RECEPTOR", "SANGUE", "ORGAO", "PRIORIDADE", "ENTRADA",
                     "DIAS", "SITUACAO", "HOSPITAL"],
            larguras=[40, 170, 70, 100, 110, 100, 60, 110, 200], altura=14)
        self.tabela_fila.pack(fill="both", expand=True)

        barra = ttk.Frame(quadro)
        barra.pack(fill="x", pady=(8, 0))
        ttk.Button(barra, text="Inserir receptor na fila",
                   command=self.inserir_na_fila).pack(side="left")
        ttk.Button(barra, text="Alterar prioridade",
                   command=self.alterar_prioridade).pack(side="left", padx=6)
        ttk.Button(barra, text="Alterar situacao",
                   command=self.alterar_situacao_fila).pack(side="left")
        return quadro

    # --------------------------------------------------------------- doadores
    def _aba_doadores(self):
        quadro = ttk.Frame(self.abas, padding=8)
        self.tabela_doadores = w.Tabela(
            quadro, colunas=["id_doador", "nome", "sangue", "tipo_doador",
                             "hospital", "data_registro", "orgaos"],
            titulos=["ID", "NOME", "SANGUE", "TIPO", "HOSPITAL", "REGISTRO", "ORGAOS"],
            larguras=[40, 190, 70, 90, 220, 100, 70], altura=16)
        self.tabela_doadores.pack(fill="both", expand=True)
        barra = ttk.Frame(quadro)
        barra.pack(fill="x", pady=(8, 0))
        ttk.Button(barra, text="Cadastrar doador",
                   command=self.novo_doador).pack(side="left")
        ttk.Button(barra, text="Registrar orgao do doador",
                   command=self.novo_orgao).pack(side="left", padx=6)
        return quadro

    # -------------------------------------------------------------- receptores
    def _aba_receptores(self):
        quadro = ttk.Frame(self.abas, padding=8)
        self.tabela_receptores = w.Tabela(
            quadro, colunas=["id_receptor", "nome", "sangue", "hospital",
                             "contato", "filas_ativas"],
            titulos=["ID", "NOME", "SANGUE", "HOSPITAL", "CONTATO", "FILAS ATIVAS"],
            larguras=[40, 190, 70, 220, 130, 100], altura=16)
        self.tabela_receptores.pack(fill="both", expand=True)
        barra = ttk.Frame(quadro)
        barra.pack(fill="x", pady=(8, 0))
        ttk.Button(barra, text="Cadastrar receptor",
                   command=self.novo_receptor).pack(side="left")
        ttk.Button(barra, text="Atualizar contato",
                   command=self.atualizar_contato_receptor).pack(side="left", padx=6)
        ttk.Button(barra, text="Inserir na fila",
                   command=self.inserir_na_fila_do_receptor).pack(side="left")
        return quadro

    # ------------------------------------------------------------ transplantes
    def _aba_transplantes(self):
        quadro = ttk.Frame(self.abas, padding=8)
        self.tabela_transplantes = w.Tabela(
            quadro, colunas=["id_transplante", "orgao", "doador", "receptor",
                             "data_cirurgia", "cirurgiao", "resultado", "hospital"],
            titulos=["ID", "ORGAO", "DOADOR", "RECEPTOR", "CIRURGIA", "CIRURGIAO",
                     "RESULTADO", "HOSPITAL"],
            larguras=[40, 90, 150, 150, 120, 150, 140, 200], altura=16)
        self.tabela_transplantes.pack(fill="both", expand=True)
        barra = ttk.Frame(quadro)
        barra.pack(fill="x", pady=(8, 0))
        ttk.Button(barra, text="Atualizar desfecho",
                   command=self.atualizar_resultado).pack(side="left")
        return quadro

    # ------------------------------------------------------------ carregamento
    def recarregar(self):
        self._carregar_painel()
        self._carregar_orgaos()
        self._carregar_fila()
        self.tabela_doadores.preencher(repo.listar_doadores(self.conexao))
        self.tabela_receptores.preencher(repo.listar_receptores(self.conexao))
        self.tabela_transplantes.preencher(repo.listar_transplantes(self.conexao))
        self._carregar_combo_orgaos()
        self.tabela_todos_cruzamentos.preencher(
            repo.compatibilidade_geral(self.conexao),
            destacar=lambda l: l["prioridade"] == "EMERGENCIA")

    def _carregar_painel(self):
        for filho in self.painel_indicadores.winfo_children():
            filho.destroy()
        dados = repo.painel(self.conexao)
        indicadores = [
            ("Doadores", dados["doadores"], False),
            ("Receptores", dados["receptores"], False),
            ("Orgaos disponiveis", dados["orgaos_disponiveis"], False),
            ("Reservados", dados["orgaos_reservados"], False),
            ("Na fila", dados["na_fila"], False),
            ("Emergencias", dados["emergencias"], dados["emergencias"] > 0),
            ("Transplantes", dados["transplantes"], False),
            ("Cruzamentos", dados["cruzamentos_compativeis"], False),
        ]
        for rotulo, valor, destaque in indicadores:
            w.cartao_indicador(self.painel_indicadores, rotulo, valor,
                               destaque).pack(side="left", padx=(0, 6))

        self.tabela_demanda.preencher(repo.fila_por_orgao(self.conexao))
        self.tabela_resumo_compat.preencher(
            repo.candidatos_por_orgao(self.conexao),
            destacar=lambda l: l["candidatos"] == 0)
        self.tabela_sem_opcao.preencher(
            repo.sem_compatibilidade(self.conexao),
            destacar=lambda l: l["prioridade"] == "EMERGENCIA")
        self.tabela_hospitais.preencher(repo.transplantes_por_hospital(self.conexao))

    def _carregar_orgaos(self):
        status = self.filtro_status.get()
        linhas = repo.listar_orgaos(self.conexao,
                                    status=None if status == "TODOS" else status)
        self.tabela_orgaos.preencher(
            linhas,
            destacar=lambda l: (l["status"] == "DISPONIVEL"
                                and l["horas_desde_captacao"] > l["isquemia_h"]))

    def _carregar_fila(self):
        situacao = self.filtro_fila.get()
        linhas = repo.listar_fila(self.conexao,
                                  status=None if situacao == "TODAS" else situacao)
        self.tabela_fila.preencher(
            linhas, destacar=lambda l: l["prioridade"] == "EMERGENCIA")

    def _carregar_combo_orgaos(self):
        self.orgaos_disponiveis = repo.listar_orgaos(self.conexao, status="DISPONIVEL")
        descricoes = ["{0} - {1} | doador {2} ({3}) | {4}".format(
            l["id_orgao"], l["orgao"], l["doador"], l["sangue"], l["hospital"])
            for l in self.orgaos_disponiveis]
        self.combo_orgao.configure(values=descricoes)
        if descricoes:
            atual = self.combo_orgao.get()
            if atual not in descricoes:
                self.combo_orgao.set(descricoes[0])
            self._buscar_compativeis()
        else:
            self.combo_orgao.set("")
            self.tabela_compativeis.limpar()

    def _orgao_selecionado(self):
        texto = self.combo_orgao.get()
        if not texto:
            return None
        return int(texto.split(" - ")[0])

    def _buscar_compativeis(self):
        id_orgao = self._orgao_selecionado()
        if id_orgao is None:
            self.tabela_compativeis.limpar()
            return
        candidatos = repo.compativeis_para_orgao(self.conexao, id_orgao)
        self.tabela_compativeis.preencher(
            candidatos, destacar=lambda l: l["prioridade"] == "EMERGENCIA")
        self.tabela_compativeis.selecionar_primeiro()

    def _ir_para_compatibilidade(self):
        id_orgao = self.tabela_orgaos.selecionado_int("id_orgao")
        if id_orgao is None:
            messagebox.showinfo("Selecione um orgao",
                                "Escolha um orgao na tabela.", parent=self)
            return
        for descricao in self.combo_orgao.cget("values"):
            if descricao.startswith("{0} - ".format(id_orgao)):
                self.combo_orgao.set(descricao)
                self._buscar_compativeis()
                self.abas.select(1)
                return
        messagebox.showinfo("Orgao indisponivel",
                            "A busca de compativeis considera apenas orgaos "
                            "com status DISPONIVEL.", parent=self)

    # ------------------------------------------------------------------ acoes
    def _formulario(self, titulo, campos):
        dialogo = w.Formulario(self.winfo_toplevel(), titulo, campos)
        return dialogo.resultado

    def _itens_hospitais(self):
        return [(l["id_hospital"], "{0} ({1}/{2})".format(l["nome"], l["cidade"], l["uf"]))
                for l in repo.listar_hospitais(self.conexao)]

    def _itens_tipos_orgao(self):
        return [(l["id_tipo_orgao"], "{0} - isquemia {1}h".format(
            l["nome"], l["tempo_isquemia_horas"]))
            for l in repo.listar_tipos_orgao(self.conexao)]

    def novo_doador(self):
        dados = self._formulario("Cadastrar doador", [
            w.campo("nome", "Nome completo"),
            w.campo("cpf", "CPF"),
            w.campo("data_nascimento", "Nascimento (YYYY-MM-DD)", "data"),
            w.campo("tipo_sanguineo", "Tipo sanguineo", "opcao", opcoes=w.TIPOS_SANGUINEOS),
            w.campo("fator_rh", "Fator RH", "opcao", opcoes=w.FATORES_RH),
            w.campo("tipo_doador", "Tipo de doador", "opcao", opcoes=("VIVO", "FALECIDO")),
            w.campo("id_hospital", "Hospital", "lista", itens=self._itens_hospitais()),
        ])
        if not dados:
            return
        dados["data_registro"] = hoje()
        try:
            repo.inserir_doador(self.conexao, dados)
        except Exception as erro:
            messagebox.showerror("Erro ao inserir", str(erro), parent=self)
            return
        self.recarregar()

    def novo_receptor(self):
        dados = self._formulario("Cadastrar receptor", [
            w.campo("nome", "Nome completo"),
            w.campo("cpf", "CPF"),
            w.campo("data_nascimento", "Nascimento (YYYY-MM-DD)", "data"),
            w.campo("tipo_sanguineo", "Tipo sanguineo", "opcao", opcoes=w.TIPOS_SANGUINEOS),
            w.campo("fator_rh", "Fator RH", "opcao", opcoes=w.FATORES_RH),
            w.campo("contato", "Contato", obrigatorio=False),
            w.campo("id_hospital", "Hospital", "lista", itens=self._itens_hospitais()),
        ])
        if not dados:
            return
        try:
            novo = repo.inserir_receptor(self.conexao, dados)
        except Exception as erro:
            messagebox.showerror("Erro ao inserir", str(erro), parent=self)
            return
        self.recarregar()
        if messagebox.askyesno("Fila de espera",
                               "Inserir o receptor em uma fila de espera agora?",
                               parent=self):
            self._inserir_na_fila(novo)

    def atualizar_contato_receptor(self):
        id_receptor = self.tabela_receptores.selecionado_int("id_receptor")
        if id_receptor is None:
            messagebox.showinfo("Selecione um receptor",
                                "Escolha um receptor na tabela.", parent=self)
            return
        dados = self._formulario("Atualizar contato", [
            w.campo("contato", "Contato",
                    padrao=self.tabela_receptores.selecionado("contato")),
        ])
        if not dados:
            return
        repo.atualizar_contato_receptor(self.conexao, id_receptor, dados["contato"])
        self.recarregar()

    def novo_orgao(self):
        doadores = [(l["id_doador"], "{0} ({1}, {2})".format(
            l["nome"], l["sangue"], l["hospital"]))
            for l in repo.listar_doadores(self.conexao)]
        if not doadores:
            messagebox.showinfo("Sem doadores", "Cadastre um doador primeiro.", parent=self)
            return
        dados = self._formulario("Registrar orgao captado", [
            w.campo("id_doador", "Doador", "lista", itens=doadores),
            w.campo("id_tipo_orgao", "Tipo de orgao", "lista", itens=self._itens_tipos_orgao()),
            w.campo("id_hospital", "Hospital do orgao", "lista", itens=self._itens_hospitais()),
            w.campo("data_captacao", "Captacao (YYYY-MM-DD HH:MM)", "data_hora",
                    padrao=hoje() + " 08:00"),
            w.campo("status", "Status", "opcao", opcoes=STATUS_ORGAO),
            w.campo("observacao", "Observacao", "memo", obrigatorio=False),
        ])
        if not dados:
            return
        try:
            repo.inserir_orgao(self.conexao, dados)
        except Exception as erro:
            messagebox.showerror("Erro ao inserir", str(erro), parent=self)
            return
        self.recarregar()

    def alterar_status_orgao(self):
        id_orgao = self.tabela_orgaos.selecionado_int("id_orgao")
        if id_orgao is None:
            messagebox.showinfo("Selecione um orgao",
                                "Escolha um orgao na tabela.", parent=self)
            return
        dados = self._formulario("Alterar status do orgao {0}".format(id_orgao), [
            w.campo("status", "Novo status", "opcao", opcoes=STATUS_ORGAO,
                    padrao=self.tabela_orgaos.selecionado("status")),
        ])
        if not dados:
            return
        repo.atualizar_status_orgao(self.conexao, id_orgao, dados["status"])
        self.recarregar()

    def reservar_orgao(self):
        id_orgao = self._orgao_selecionado()
        if id_orgao is None:
            return
        repo.atualizar_status_orgao(self.conexao, id_orgao, "RESERVADO")
        self.recarregar()
        messagebox.showinfo("Orgao reservado",
                            "Orgao {0} marcado como RESERVADO.".format(id_orgao),
                            parent=self)

    def inserir_na_fila(self):
        self._inserir_na_fila(None)

    def inserir_na_fila_do_receptor(self):
        self._inserir_na_fila(self.tabela_receptores.selecionado_int("id_receptor"))

    def _inserir_na_fila(self, id_receptor):
        campos = []
        if id_receptor is None:
            receptores = [(l["id_receptor"], "{0} ({1})".format(l["nome"], l["sangue"]))
                          for l in repo.listar_receptores(self.conexao)]
            if not receptores:
                messagebox.showinfo("Sem receptores",
                                    "Cadastre um receptor primeiro.", parent=self)
                return
            campos.append(w.campo("id_receptor", "Receptor", "lista", itens=receptores))
        campos += [
            w.campo("id_tipo_orgao", "Orgao aguardado", "lista",
                    itens=self._itens_tipos_orgao()),
            w.campo("prioridade", "Prioridade", "opcao", opcoes=PRIORIDADES,
                    padrao="NORMAL"),
            w.campo("data_entrada", "Entrada (YYYY-MM-DD)", "data", padrao=hoje()),
        ]
        dados = self._formulario("Inserir receptor na fila de espera", campos)
        if not dados:
            return
        if id_receptor is not None:
            dados["id_receptor"] = id_receptor
        try:
            repo.inserir_na_fila(self.conexao, dados)
        except Exception as erro:
            messagebox.showerror("Erro ao inserir",
                                 "O receptor ja aguarda por este tipo de orgao.\n\n"
                                 + str(erro), parent=self)
            return
        self.recarregar()

    def alterar_prioridade(self):
        id_fila = self.tabela_fila.selecionado_int("id_fila")
        if id_fila is None:
            messagebox.showinfo("Selecione a fila",
                                "Escolha um registro na fila.", parent=self)
            return
        dados = self._formulario("Alterar prioridade (fila {0})".format(id_fila), [
            w.campo("prioridade", "Prioridade", "opcao", opcoes=PRIORIDADES,
                    padrao=self.tabela_fila.selecionado("prioridade")),
        ])
        if not dados:
            return
        repo.atualizar_prioridade(self.conexao, id_fila, dados["prioridade"])
        self.recarregar()

    def alterar_situacao_fila(self):
        id_fila = self.tabela_fila.selecionado_int("id_fila")
        if id_fila is None:
            messagebox.showinfo("Selecione a fila",
                                "Escolha um registro na fila.", parent=self)
            return
        dados = self._formulario("Alterar situacao (fila {0})".format(id_fila), [
            w.campo("status", "Situacao", "opcao", opcoes=SITUACOES_FILA,
                    padrao=self.tabela_fila.selecionado("status")),
        ])
        if not dados:
            return
        repo.atualizar_status_fila(self.conexao, id_fila, dados["status"])
        self.recarregar()

    def efetivar_transplante(self):
        id_orgao = self._orgao_selecionado()
        if id_orgao is None:
            messagebox.showinfo("Sem orgao", "Nenhum orgao disponivel selecionado.",
                                parent=self)
            return
        id_fila = self.tabela_compativeis.selecionado_int("id_fila")
        if id_fila is None:
            messagebox.showinfo("Selecione o receptor",
                                "Escolha um candidato compativel na tabela.", parent=self)
            return
        item = repo.buscar_item_fila(self.conexao, id_fila)
        dados = self._formulario("Efetivar transplante - {0}".format(item["receptor"]), [
            w.campo("id_hospital", "Hospital da cirurgia", "lista",
                    itens=self._itens_hospitais()),
            w.campo("data_cirurgia", "Cirurgia (YYYY-MM-DD HH:MM)", "data_hora",
                    padrao=hoje() + " 08:00"),
            w.campo("cirurgiao", "Cirurgiao responsavel", obrigatorio=False),
        ])
        if not dados:
            return
        if not messagebox.askyesno(
                "Confirmar transplante",
                "Confirmar o transplante do orgao {0} para {1}?\n\n"
                "O orgao e a fila serao marcados como TRANSPLANTADO.".format(
                    id_orgao, item["receptor"]), parent=self):
            return
        dados["id_orgao"] = id_orgao
        dados["id_receptor"] = item["id_receptor"]
        try:
            novo = repo.registrar_transplante(self.conexao, id_orgao, id_fila, dados)
        except Exception as erro:
            messagebox.showerror("Erro ao registrar", str(erro), parent=self)
            return
        self.recarregar()
        self.abas.select(6)
        messagebox.showinfo("Transplante registrado",
                            "Transplante {0} registrado com sucesso.".format(novo),
                            parent=self)

    def atualizar_resultado(self):
        id_transplante = self.tabela_transplantes.selecionado_int("id_transplante")
        if id_transplante is None:
            messagebox.showinfo("Selecione o transplante",
                                "Escolha um transplante na tabela.", parent=self)
            return
        dados = self._formulario("Atualizar desfecho", [
            w.campo("resultado", "Resultado", "opcao", opcoes=RESULTADOS,
                    padrao=self.tabela_transplantes.selecionado("resultado")),
        ])
        if not dados:
            return
        repo.atualizar_resultado_transplante(self.conexao, id_transplante,
                                             dados["resultado"])
        self.recarregar()

    def mostrar_regras(self):
        janela = tk.Toplevel(self.winfo_toplevel())
        janela.title("Regras de compatibilidade sanguinea")
        quadro = ttk.Frame(janela, padding=14)
        quadro.pack(fill="both", expand=True)
        ttk.Label(quadro, text="Compatibilidade doador -> receptor",
                  font=("TkDefaultFont", 12, "bold")).pack(anchor="w", pady=(0, 8))

        regras = {}
        for regra in repo.regras_compatibilidade(self.conexao):
            regras.setdefault(regra["doador"], []).append(regra["receptor"])
        for doador in sorted(regras):
            ttk.Label(quadro, text="Doador {0:>3}  ->  {1}".format(
                doador, ", ".join(sorted(regras[doador])))).pack(anchor="w")

        ttk.Label(quadro, foreground="#4a5a63", justify="left", text=(
            "\nRegra ABO: O doa para todos | A -> A e AB | B -> B e AB | AB -> AB\n"
            "Regra RH : negativo doa para ambos | positivo somente para positivo\n"
            "As regras estao nas tabelas compat_abo e compat_rh e sao aplicadas\n"
            "pela view vw_compatibilidade.")).pack(anchor="w")
        ttk.Button(quadro, text="Fechar", command=janela.destroy).pack(anchor="e", pady=(10, 0))
        janela.transient(self.winfo_toplevel())
        janela.grab_set()
