# -*- coding: utf-8 -*-
"""Interface Tkinter da Central Hospitalar de Transplantes."""

from dataclasses import asdict
from tkinter import messagebox, simpledialog, ttk

from backend.central.servico import CentralService


def _texto(valor):
    return "" if valor is None else str(valor)


class AbaCentral(ttk.Frame):
    def __init__(self, master, servico=None):
        super().__init__(master, padding=10)
        self.servico = servico or CentralService()
        self._montar()
        self.recarregar()

    def _montar(self):
        ttk.Label(self, text="Central Hospitalar de Transplantes",
                  font=("TkDefaultFont", 16, "bold")).pack(anchor="w", pady=(0, 8))
        barra = ttk.Frame(self)
        barra.pack(fill="x", pady=(0, 8))
        for texto, comando in (
                ("Novo doador", self.novo_doador),
                ("Novo receptor", self.novo_receptor),
                ("Novo órgão", self.novo_orgao),
                ("Adicionar à fila", self.adicionar_fila),
                ("Atualizar", self.recarregar)):
            ttk.Button(barra, text=texto, command=comando).pack(side="left", padx=(0, 5))

        self.abas = ttk.Notebook(self)
        self.abas.pack(fill="both", expand=True)
        definicoes = {
            "Órgãos disponíveis": ("orgao_id", "orgao", "doador_nome",
                                   "doador_sangue", "hospital_origem", "horas_restantes"),
            "Fila ativa": ("fila_id", "orgao", "nome", "sangue", "urgencia",
                           "hospital", "dias_espera"),
            "Doadores": ("id", "usuario_id", "nome", "tipo", "hospital_id", "status"),
            "Receptores": ("id", "usuario_id", "nome", "hospital_id", "data_cadastro"),
            "Processos": ("alocacao_id", "orgao", "doador_nome", "receptor_nome",
                          "hospital_origem", "hospital_destino", "status_logistica"),
            "Candidatos": ("fila_id", "nome", "sangue", "urgencia", "dias_espera",
                           "distancia_km", "tempo_transporte_h", "motivo_exclusao"),
        }
        self.tabelas = {}
        for nome, colunas in definicoes.items():
            quadro = ttk.Frame(self.abas, padding=6)
            tabela = ttk.Treeview(quadro, columns=colunas, show="headings",
                                  selectmode="browse")
            for coluna in colunas:
                tabela.heading(coluna, text=coluna.replace("_", " ").title())
                tabela.column(coluna, width=140, anchor="w")
            tabela.pack(fill="both", expand=True)
            self.tabelas[nome] = tabela
            self.abas.add(quadro, text=nome)
            if nome == "Órgãos disponíveis":
                ttk.Button(quadro, text="Buscar receptores compatíveis",
                           command=self.buscar_compativeis).pack(anchor="w", pady=(6, 0))
            elif nome == "Candidatos":
                ttk.Button(quadro, text="Alocar ao receptor selecionado",
                           command=self.alocar).pack(anchor="w", pady=(6, 0))
            elif nome == "Fila ativa":
                botoes = ttk.Frame(quadro)
                botoes.pack(anchor="w", pady=(6, 0))
                ttk.Button(botoes, text="Alterar urgência",
                           command=self.alterar_urgencia).pack(side="left", padx=3)
                ttk.Button(botoes, text="Remover da fila",
                           command=self.remover_da_fila).pack(side="left", padx=3)
            elif nome == "Doadores":
                ttk.Button(quadro, text="Reavaliar doadores",
                           command=self.reavaliar_doadores).pack(anchor="w", pady=(6, 0))
            elif nome == "Processos":
                botoes = ttk.Frame(quadro)
                botoes.pack(anchor="w", pady=(6, 0))
                for texto, comando in (
                        ("Registrar entrega", self.registrar_entrega),
                        ("Concluir transplante", self.concluir_transplante),
                        ("Cancelar alocação", self.cancelar_alocacao)):
                    ttk.Button(botoes, text=texto, command=comando).pack(side="left", padx=3)

    def _perguntar(self, titulo, campos):
        dados = {}
        for nome, inicial in campos:
            valor = simpledialog.askstring(titulo, nome,
                                           initialvalue=_texto(inicial), parent=self)
            if valor is None:
                return None
            dados[nome] = valor.strip() or None
        return dados

    def _executar(self, funcao):
        try:
            funcao()
            self.recarregar()
        except Exception as erro:
            messagebox.showerror("Operação não concluída", str(erro), parent=self)

    def _preencher(self, nome, registros):
        tabela = self.tabelas[nome]
        tabela.delete(*tabela.get_children())
        for registro in registros:
            dados = asdict(registro) if hasattr(registro, "__dataclass_fields__") else registro
            if nome == "Candidatos":
                candidato = registro
                dados = asdict(candidato.pedido)
                dados.update({
                    "fila_id": candidato.pedido.fila_id,
                    "nome": candidato.pedido.nome,
                    "sangue": candidato.sangue,
                    "distancia_km": candidato.distancia_km,
                    "tempo_transporte_h": candidato.tempo_transporte_h,
                    "motivo_exclusao": candidato.motivo_exclusao,
                })
            colunas = tabela["columns"]
            tabela.insert("", "end", values=tuple(_texto(dados.get(c)) for c in colunas))

    def recarregar(self):
        try:
            self._preencher("Órgãos disponíveis", self.servico.orgaos_disponiveis())
            self._preencher("Fila ativa", self.servico.fila_ativa())
            self._preencher("Doadores", self.servico.listar_doadores())
            self._preencher("Receptores", self.servico.listar_receptores())
            self._preencher("Processos", self.servico.processos())
        except Exception as erro:
            messagebox.showerror("Falha ao carregar a Central", str(erro), parent=self)

    def _selecionado(self, aba, coluna=0):
        tabela = self.tabelas[aba]
        selecao = tabela.selection()
        if not selecao:
            messagebox.showinfo("Selecione um registro", "Escolha uma linha na tabela.",
                                parent=self)
            return None
        valor = tabela.item(selecao[0], "values")[coluna]
        return int(valor) if str(valor).isdigit() else None

    def novo_doador(self):
        hospitais = self.servico.listar_hospitais()
        dados = self._perguntar("Novo doador", [
            ("ID do usuário no Diário", None),
            ("Tipo (vivo/falecido)", "vivo"),
            ("ID do hospital: " + ", ".join(f"{h.id}={h.nome}" for h in hospitais), None)])
        if dados is not None:
            nome_hospital = next(k for k in dados if k.startswith("ID do hospital"))
            self._executar(lambda: self.servico.cadastrar_doador(
                int(dados["ID do usuário no Diário"]), dados["Tipo (vivo/falecido)"],
                int(dados[nome_hospital])))

    def novo_receptor(self):
        hospitais = self.servico.listar_hospitais()
        dados = self._perguntar("Novo receptor", [
            ("ID do usuário no Diário", None),
            ("ID do hospital: " + ", ".join(f"{h.id}={h.nome}" for h in hospitais), None)])
        if dados is not None:
            nome_hospital = next(k for k in dados if k.startswith("ID do hospital"))
            self._executar(lambda: self.servico.cadastrar_receptor(
                int(dados["ID do usuário no Diário"]), int(dados[nome_hospital])))

    def novo_orgao(self):
        doadores = self.servico.listar_doadores()
        tipos = self.servico.listar_tipos_orgao()
        dados = self._perguntar("Registrar órgão", [
            ("ID do doador: " + ", ".join(f"{d.id}={d.nome}" for d in doadores), None),
            ("ID do tipo: " + ", ".join(f"{t.id}={t.nome}" for t in tipos), None),
            ("ID do hospital (opcional)", None)])
        if dados is not None:
            doador_campo = next(k for k in dados if k.startswith("ID do doador"))
            tipo_campo = next(k for k in dados if k.startswith("ID do tipo"))
            hospital = dados["ID do hospital (opcional)"]
            self._executar(lambda: self.servico.registrar_orgao(
                int(dados[doador_campo]), int(dados[tipo_campo]),
                int(hospital) if hospital else None))

    def adicionar_fila(self):
        receptores = self.servico.listar_receptores()
        tipos = self.servico.listar_tipos_orgao()
        dados = self._perguntar("Adicionar à fila", [
            ("ID do receptor: " + ", ".join(f"{r.id}={r.nome}" for r in receptores), None),
            ("ID do tipo de órgão: " + ", ".join(f"{t.id}={t.nome}" for t in tipos), None),
            ("Urgência (1-5)", "3")])
        if dados is not None:
            receptor_campo = next(k for k in dados if k.startswith("ID do receptor"))
            tipo_campo = next(k for k in dados if k.startswith("ID do tipo"))
            self._executar(lambda: self.servico.incluir_na_fila(
                int(dados[receptor_campo]), int(dados[tipo_campo]),
                int(dados["Urgência (1-5)"])))

    def alterar_urgencia(self):
        fila_id = self._selecionado("Fila ativa")
        if fila_id is None:
            return
        urgencia = simpledialog.askinteger(
            "Alterar urgência", "Informe um valor de 1 a 5:", minvalue=1, maxvalue=5,
            parent=self)
        if urgencia is not None:
            self._executar(lambda: self.servico.atualizar_urgencia(fila_id, urgencia))

    def remover_da_fila(self):
        fila_id = self._selecionado("Fila ativa")
        if fila_id is not None:
            self._executar(lambda: self.servico.remover_da_fila(fila_id))

    def reavaliar_doadores(self):
        def reavaliar():
            alteracoes = self.servico.reavaliar_doadores()
            messagebox.showinfo(
                "Reavaliação concluída",
                f"{len(alteracoes)} cadastro(s) de doador tiveram o status alterado.",
                parent=self)
        self._executar(reavaliar)

    def buscar_compativeis(self):
        orgao_id = self._selecionado("Órgãos disponíveis")
        if orgao_id is None:
            return
        try:
            resultado = self.servico.selecionar_receptores(orgao_id)
            self._preencher("Candidatos", resultado.candidatos)
            for indice, candidato in enumerate(resultado.candidatos):
                if not candidato.elegivel:
                    iid = self.tabelas["Candidatos"].get_children()[indice]
                    self.tabelas["Candidatos"].item(iid, tags=("ineligivel",))
            self.tabelas["Candidatos"].tag_configure("ineligivel", foreground="#777777")
            self.abas.select(self.tabelas["Candidatos"].master)
            self.orgao_id_selecionado = orgao_id
        except Exception as erro:
            messagebox.showerror("Falha na compatibilidade", str(erro), parent=self)

    def alocar(self):
        if not getattr(self, "orgao_id_selecionado", None):
            messagebox.showinfo("Selecione um órgão",
                                "Busque candidatos para um órgão antes de alocar.", parent=self)
            return
        fila_id = self._selecionado("Candidatos")
        if fila_id is not None:
            self._executar(lambda: self.servico.alocar_orgao(
                self.orgao_id_selecionado, fila_id))

    def _etapa_processo(self, metodo):
        alocacao_id = self._selecionado("Processos")
        if alocacao_id is not None:
            self._executar(lambda: metodo(alocacao_id))

    def registrar_entrega(self):
        self._etapa_processo(self.servico.registrar_entrega)

    def concluir_transplante(self):
        self._etapa_processo(self.servico.concluir_transplante)

    def cancelar_alocacao(self):
        self._etapa_processo(self.servico.cancelar_alocacao)
