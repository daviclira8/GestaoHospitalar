# -*- coding: utf-8 -*-
"""Interface Tkinter do Diário de Saúde Pessoal."""

from dataclasses import asdict
from datetime import date
from tkinter import messagebox, simpledialog, ttk

from backend.diario.servico import DiarioService


def _texto(valor):
    return "" if valor is None else str(valor)


class AbaDiario(ttk.Frame):
    COLECOES = {
        "Alergias": ("id", "substancia", "gravidade", "observacao"),
        "Diagnósticos": ("id", "doenca", "data_diagnostico", "status",
                         "impede_doacao"),
        "Consultas": ("id", "data_hora", "especialidade", "profissional", "local"),
        "Exames": ("id", "tipo", "data", "resultado", "consulta_id"),
        "Vacinas": ("id", "vacina", "data_aplicacao", "dose", "lote"),
        "Métricas": ("id", "tipo", "valor", "unidade", "data_hora"),
        "Linha do tempo": ("data", "evento", "descricao"),
    }

    def __init__(self, master, servico=None):
        super().__init__(master, padding=10)
        self.servico = servico or DiarioService()
        self.usuario_id = None
        self._montar()
        self.recarregar()

    def _montar(self):
        ttk.Label(self, text="Diário de Saúde Pessoal",
                  font=("TkDefaultFont", 16, "bold")).pack(anchor="w", pady=(0, 8))
        conteudo = ttk.Panedwindow(self, orient="horizontal")
        conteudo.pack(fill="both", expand=True)
        lista = ttk.Frame(conteudo, padding=(0, 0, 8, 0))
        detalhe = ttk.Frame(conteudo)
        conteudo.add(lista, weight=1)
        conteudo.add(detalhe, weight=3)

        busca = ttk.Frame(lista)
        busca.pack(fill="x", pady=(0, 5))
        self.busca = ttk.Entry(busca)
        self.busca.pack(side="left", fill="x", expand=True)
        self.busca.bind("<Return>", lambda _evento: self.recarregar())
        ttk.Button(busca, text="Buscar", command=self.recarregar).pack(side="left", padx=4)
        ttk.Button(lista, text="Novo usuário", command=self.novo_usuario).pack(fill="x")
        self.usuarios = ttk.Treeview(
            lista, columns=("id", "nome", "cpf", "sangue"), show="headings",
            selectmode="browse")
        for coluna, titulo, largura in (
                ("id", "ID", 45), ("nome", "Nome", 170),
                ("cpf", "CPF", 105), ("sangue", "Sangue", 75)):
            self.usuarios.heading(coluna, text=titulo)
            self.usuarios.column(coluna, width=largura, anchor="w")
        self.usuarios.pack(fill="both", expand=True, pady=5)
        self.usuarios.bind("<<TreeviewSelect>>", self._selecionar_usuario)
        botoes = ttk.Frame(lista)
        botoes.pack(fill="x")
        ttk.Button(botoes, text="Contato", command=self.editar_contato).pack(side="left")
        ttk.Button(botoes, text="Tipagem", command=self.editar_tipagem).pack(side="left", padx=4)

        self.ficha = ttk.Label(detalhe, text="Selecione um usuário.",
                               justify="left", wraplength=900)
        self.ficha.pack(fill="x", pady=(0, 8))
        self.abas = ttk.Notebook(detalhe)
        self.abas.pack(fill="both", expand=True)
        self.tabelas = {}
        for nome, colunas in self.COLECOES.items():
            quadro = ttk.Frame(self.abas, padding=6)
            tabela = ttk.Treeview(quadro, columns=colunas, show="headings",
                                  selectmode="browse")
            for coluna in colunas:
                tabela.heading(coluna, text=coluna.replace("_", " ").title())
                tabela.column(coluna, width=130, anchor="w")
            tabela.pack(fill="both", expand=True)
            self.tabelas[nome] = tabela
            self.abas.add(quadro, text=nome)
            if nome != "Linha do tempo":
                ttk.Button(quadro, text="Adicionar / atualizar",
                           command=lambda categoria=nome: self.acao(categoria)
                           ).pack(anchor="w", pady=(6, 0))
        catalogo = ttk.Frame(self.abas, padding=8)
        ttk.Label(catalogo, text="Cadastros de doenças e vacinas").pack(anchor="w")
        ttk.Button(catalogo, text="Cadastrar doença", command=self.nova_doenca).pack(
            anchor="w", pady=(8, 0))
        ttk.Button(catalogo, text="Cadastrar vacina", command=self.nova_vacina).pack(
            anchor="w", pady=(6, 0))
        self.abas.add(catalogo, text="Catálogos")
        self.abas.bind("<<NotebookTabChanged>>", lambda _evento: self._carregar_detalhes())

    def _perguntar(self, titulo, campos):
        valores = {}
        for nome, inicial in campos:
            valor = simpledialog.askstring(titulo, nome, initialvalue=_texto(inicial),
                                           parent=self)
            if valor is None:
                return None
            valores[nome] = valor.strip() or None
        return valores

    def _executar(self, funcao):
        try:
            funcao()
            self.recarregar()
            self._carregar_detalhes()
        except Exception as erro:
            messagebox.showerror("Operação não concluída", str(erro), parent=self)

    def recarregar(self):
        try:
            usuarios = self.servico.listar_usuarios(self.busca.get().strip() or None)
        except Exception as erro:
            messagebox.showerror("Falha ao carregar o Diário", str(erro), parent=self)
            return
        for item in self.usuarios.get_children():
            self.usuarios.delete(item)
        selecionado = None
        for usuario in usuarios:
            iid = str(usuario.id)
            self.usuarios.insert("", "end", iid=iid, values=(
                usuario.id, usuario.nome, usuario.cpf, usuario.sangue))
            if usuario.id == self.usuario_id:
                selecionado = iid
        if selecionado:
            self.usuarios.selection_set(selecionado)
        elif usuarios:
            self.usuarios.selection_set(str(usuarios[0].id))
            self.usuario_id = usuarios[0].id
        else:
            self.usuario_id = None
        self._carregar_detalhes()

    def _selecionar_usuario(self, _evento=None):
        selecao = self.usuarios.selection()
        self.usuario_id = int(selecao[0]) if selecao else None
        self._carregar_detalhes()

    def _carregar_detalhes(self):
        if self.usuario_id is None:
            self.ficha.configure(text="Selecione um usuário.")
            for tabela in self.tabelas.values():
                tabela.delete(*tabela.get_children())
            return
        try:
            usuario = self.servico.buscar_usuario(self.usuario_id)
            ficha = (f"{usuario.nome} | CPF {usuario.cpf} | {usuario.idade} anos | "
                     f"{usuario.sangue} | {usuario.cidade or '-'} / {usuario.uf or '-'} | "
                     f"{usuario.telefone or '-'} | {usuario.email or '-'}")
            self.ficha.configure(text=ficha)
            valores = {
                "Alergias": self.servico.listar_alergias(usuario.id),
                "Diagnósticos": self.servico.listar_diagnosticos(usuario.id),
                "Consultas": self.servico.listar_consultas(usuario.id),
                "Exames": self.servico.listar_exames(usuario.id),
                "Vacinas": self.servico.cartao_vacinacao(usuario.id),
                "Métricas": [registro for serie in
                             self.servico.metricas_por_tipo(usuario.id).values()
                             for registro in serie],
                "Linha do tempo": self.servico.linha_do_tempo(usuario.id),
            }
            for nome, registros in valores.items():
                tabela = self.tabelas[nome]
                tabela.delete(*tabela.get_children())
                for registro in registros:
                    linha = asdict(registro)
                    if nome == "Diagnósticos":
                        linha["doenca"] = registro.doenca
                        linha["impede_doacao"] = registro.impede_doacao
                    if nome == "Vacinas":
                        linha["vacina"] = registro.vacina
                    tabela.insert("", "end", values=tuple(
                        _texto(linha.get(coluna)) for coluna in self.COLECOES[nome]))
        except Exception as erro:
            messagebox.showerror("Falha ao carregar o prontuário", str(erro), parent=self)

    def novo_usuario(self):
        dados = self._perguntar("Novo usuário", [
            ("Nome", None), ("CPF", None), ("Nascimento (AAAA-MM-DD)", None),
            ("Sexo (masculino/feminino/outro)", None),
            ("Tipo sanguíneo (A/B/AB/O)", None),
            ("Fator RH (positivo/negativo)", None), ("Cidade", None), ("UF", None),
            ("E-mail", None), ("Telefone", None)])
        if dados is None:
            return
        def criar():
            usuario = self.servico.cadastrar_usuario(
                dados["Nome"], dados["CPF"], dados["Nascimento (AAAA-MM-DD)"],
                dados["Sexo"], dados["Tipo sanguíneo (A/B/AB/O)"],
                dados["Fator RH (positivo/negativo)"], dados["Cidade"], dados["UF"],
                dados["E-mail"], dados["Telefone"])
            self.usuario_id = usuario.id
        self._executar(criar)

    def editar_contato(self):
        if self.usuario_id is None:
            return
        usuario = self.servico.buscar_usuario(self.usuario_id)
        dados = self._perguntar("Contato", [("Telefone", usuario.telefone),
                                             ("E-mail", usuario.email),
                                             ("Cidade", usuario.cidade), ("UF", usuario.uf)])
        if dados is not None:
            self._executar(lambda: self.servico.atualizar_usuario(
                self.usuario_id, telefone=dados["Telefone"], email=dados["E-mail"],
                cidade=dados["Cidade"], uf=dados["UF"]))

    def editar_tipagem(self):
        if self.usuario_id is None:
            return
        usuario = self.servico.buscar_usuario(self.usuario_id)
        dados = self._perguntar("Tipagem sanguínea", [
            ("Tipo (A/B/AB/O)", usuario.tipo_sanguineo),
            ("Fator RH (positivo/negativo)", usuario.fator_rh)])
        if dados is not None:
            self._executar(lambda: self.servico.atualizar_usuario(
                self.usuario_id, tipo_sanguineo=dados["Tipo (A/B/AB/O)"],
                fator_rh=dados["Fator RH (positivo/negativo)"]))

    def acao(self, categoria):
        if self.usuario_id is None:
            messagebox.showinfo("Selecione um usuário", "Escolha um usuário primeiro.",
                                parent=self)
            return
        tabela = self.tabelas[categoria]
        selecao = tabela.selection()
        item = tabela.item(selecao[0], "values") if selecao else ()
        ident = int(item[0]) if item and str(item[0]).isdigit() else None
        if categoria == "Alergias":
            if ident is None:
                dados = self._perguntar("Nova alergia", [("Substância", None),
                    ("Gravidade (leve/moderada/grave)", None), ("Observação", None)])
                if dados is not None:
                    self._executar(lambda: self.servico.adicionar_alergia(
                        self.usuario_id, dados["Substância"],
                        dados["Gravidade (leve/moderada/grave)"], dados["Observação"]))
            else:
                gravidade = simpledialog.askstring("Gravidade", "Nova gravidade:",
                                                   parent=self)
                if gravidade:
                    self._executar(lambda: self.servico.atualizar_gravidade_alergia(
                        ident, gravidade))
        elif categoria == "Diagnósticos":
            if ident is not None:
                status = simpledialog.askstring("Diagnóstico", "Novo status:",
                                                initialvalue=item[3], parent=self)
                if status:
                    self._executar(lambda: self.servico.atualizar_status_doenca(
                        ident, status))
            else:
                catalogo = self.servico.listar_catalogo_doencas()
                dados = self._perguntar("Novo diagnóstico", [
                    ("ID da doença: " + ", ".join(
                        f"{d.id}={d.nome}" for d in catalogo), None),
                    ("Data (AAAA-MM-DD)", date.today().isoformat()), ("Status", "ativa")])
                if dados is not None:
                    self._executar(lambda: self.servico.registrar_diagnostico(
                        self.usuario_id, int(dados[next(iter(dados))]),
                        dados["Data (AAAA-MM-DD)"], dados["Status"]))
        elif categoria == "Consultas":
            if ident is not None:
                observacoes = simpledialog.askstring("Consulta", "Observações:", parent=self)
                if observacoes is not None:
                    self._executar(lambda: self.servico.atualizar_consulta(ident, observacoes))
            else:
                dados = self._perguntar("Nova consulta", [
                    ("Data/hora (AAAA-MM-DD HH:MM)", None), ("Especialidade", None),
                    ("Profissional", None), ("Local", None), ("Observações", None)])
                if dados is not None:
                    self._executar(lambda: self.servico.registrar_consulta(
                        self.usuario_id, dados["Data/hora (AAAA-MM-DD HH:MM)"],
                        dados["Especialidade"], dados["Profissional"], dados["Local"],
                        dados["Observações"]))
        elif categoria == "Exames":
            if ident is not None:
                resultado = simpledialog.askstring("Resultado do exame", "Resultado:",
                                                   parent=self)
                if resultado:
                    self._executar(lambda: self.servico.atualizar_resultado_exame(
                        ident, resultado))
            else:
                dados = self._perguntar("Novo exame", [
                    ("Tipo", None), ("Data (AAAA-MM-DD)", date.today().isoformat()),
                    ("Resultado", None), ("ID da consulta (opcional)", None)])
                if dados is not None:
                    consulta_id = dados["ID da consulta (opcional)"]
                    self._executar(lambda: self.servico.registrar_exame(
                        self.usuario_id, dados["Tipo"], dados["Data (AAAA-MM-DD)"],
                        dados["Resultado"], int(consulta_id) if consulta_id else None))
        elif categoria == "Vacinas":
            catalogo = self.servico.listar_catalogo_vacinas()
            dados = self._perguntar("Registrar dose", [
                ("ID da vacina: " + ", ".join(f"{v.id}={v.nome}" for v in catalogo), None),
                ("Data (AAAA-MM-DD)", date.today().isoformat()), ("Dose", None), ("Lote", None)])
            if dados is not None:
                id_campo = next(iter(dados))
                self._executar(lambda: self.servico.registrar_vacina(
                    self.usuario_id, int(dados[id_campo]), dados["Data (AAAA-MM-DD)"],
                    dados["Dose"], dados["Lote"]))
        elif categoria == "Métricas":
            dados = self._perguntar("Nova métrica", [
                ("Tipo (ex.: peso)", None), ("Valor", None), ("Unidade", None),
                ("Data/hora (opcional)", None)])
            if dados is not None:
                self._executar(lambda: self.servico.registrar_metrica(
                    self.usuario_id, dados["Tipo (ex.: peso)"], dados["Valor"],
                    dados["Unidade"], dados["Data/hora (opcional)"]))

    def nova_doenca(self):
        dados = self._perguntar("Cadastrar doença", [
            ("Nome", None), ("CID (opcional)", None), ("Impede doação? (s/n)", "n")])
        if dados is not None:
            self._executar(lambda: self.servico.cadastrar_doenca(
                dados["Nome"], dados["CID (opcional)"],
                str(dados["Impede doação? (s/n)"]).lower() == "s"))

    def nova_vacina(self):
        dados = self._perguntar("Cadastrar vacina", [("Nome", None), ("Fabricante", None)])
        if dados is not None:
            self._executar(lambda: self.servico.cadastrar_vacina(
                dados["Nome"], dados["Fabricante"]))
