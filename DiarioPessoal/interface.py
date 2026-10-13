# -*- coding: utf-8 -*-
"""Interface grafica do Diario de Saude Pessoal (aba do aplicativo Tkinter).

Layout: lista de usuarios a esquerda; a direita, as abas do historico do
usuario selecionado (ficha, alergias, consultas, exames, vacinas) e um painel
de relatorios.
"""

import datetime
import os
import sys
from tkinter import messagebox, ttk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import widgets as w
from DiarioPessoal import repositorio as repo


def hoje():
    return datetime.date.today().isoformat()


class AbaDiario(ttk.Frame):

    def __init__(self, master, conexao):
        ttk.Frame.__init__(self, master)
        self.conexao = conexao
        self.id_usuario = None

        w.barra_titulo(self, "Diario de Saude Pessoal",
                       "Historico de saude: tipo sanguineo, alergias, consultas, "
                       "exames e vacinas").pack(fill="x")

        corpo = ttk.Frame(self, padding=10)
        corpo.pack(fill="both", expand=True)
        corpo.columnconfigure(0, weight=2, minsize=330)
        corpo.columnconfigure(1, weight=5)
        corpo.rowconfigure(0, weight=1)

        self._montar_lista(corpo)
        self._montar_detalhes(corpo)
        self.recarregar()

    # ------------------------------------------------------------------ lista
    def _montar_lista(self, corpo):
        painel = ttk.LabelFrame(corpo, text=" Usuarios ", padding=8)
        painel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        painel.rowconfigure(1, weight=1)
        painel.columnconfigure(0, weight=1)

        busca = ttk.Frame(painel)
        busca.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        busca.columnconfigure(0, weight=1)
        self.entrada_busca = ttk.Entry(busca)
        self.entrada_busca.grid(row=0, column=0, sticky="ew")
        self.entrada_busca.bind("<Return>", lambda e: self.recarregar())
        ttk.Button(busca, text="Buscar", width=8,
                   command=self.recarregar).grid(row=0, column=1, padx=(4, 0))
        ttk.Button(busca, text="Limpar", width=8,
                   command=self._limpar_busca).grid(row=0, column=2, padx=(4, 0))

        self.tabela_usuarios = w.Tabela(
            painel,
            colunas=["id_usuario", "nome", "sangue", "idade"],
            titulos=["ID", "NOME", "SANGUE", "IDADE"],
            larguras=[40, 170, 65, 55], altura=18)
        self.tabela_usuarios.grid(row=1, column=0, sticky="nsew")
        self.tabela_usuarios.ao_selecionar(self._selecionar_usuario)

        acoes = ttk.Frame(painel)
        acoes.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(acoes, text="Novo usuario",
                   command=self.novo_usuario).pack(side="left")
        ttk.Button(acoes, text="Editar contato",
                   command=self.editar_contato).pack(side="left", padx=4)
        ttk.Button(acoes, text="Atualizar",
                   command=self.recarregar).pack(side="left")

    # --------------------------------------------------------------- detalhes
    def _montar_detalhes(self, corpo):
        painel = ttk.Frame(corpo)
        painel.grid(row=0, column=1, sticky="nsew")
        painel.rowconfigure(1, weight=1)
        painel.columnconfigure(0, weight=1)

        self.cabecalho = ttk.LabelFrame(painel, text=" Ficha do usuario ", padding=10)
        self.cabecalho.grid(row=0, column=0, sticky="ew")
        self.rotulo_ficha = ttk.Label(
            self.cabecalho, text="Selecione um usuario na lista.",
            font=("TkDefaultFont", 11), justify="left")
        self.rotulo_ficha.pack(anchor="w")

        self.abas = ttk.Notebook(painel)
        self.abas.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

        self.abas.add(self._aba_linha_do_tempo(), text="Linha do tempo")
        self.abas.add(self._aba_alergias(), text="Alergias")
        self.abas.add(self._aba_consultas(), text="Consultas")
        self.abas.add(self._aba_exames(), text="Exames")
        self.abas.add(self._aba_vacinas(), text="Vacinas")
        self.abas.add(self._aba_relatorios(), text="Relatorios")

    def _quadro_com_acoes(self, tabela_args, botoes):
        quadro = ttk.Frame(self.abas, padding=8)
        tabela = w.Tabela(quadro, **tabela_args)
        tabela.pack(fill="both", expand=True)
        if botoes:
            barra = ttk.Frame(quadro)
            barra.pack(fill="x", pady=(8, 0))
            for texto, comando in botoes:
                ttk.Button(barra, text=texto, command=comando).pack(side="left", padx=(0, 6))
        return quadro, tabela

    def _aba_linha_do_tempo(self):
        quadro, self.tabela_tempo = self._quadro_com_acoes(
            {"colunas": ["data", "evento", "descricao", "detalhe"],
             "titulos": ["DATA", "EVENTO", "DESCRICAO", "DETALHE"],
             "larguras": [90, 90, 240, 280]}, [])
        return quadro

    def _aba_alergias(self):
        quadro, self.tabela_alergias = self._quadro_com_acoes(
            {"colunas": ["alergia", "categoria", "gravidade", "data_registro", "observacao"],
             "titulos": ["ALERGIA", "CATEGORIA", "GRAVIDADE", "REGISTRO", "OBSERVACAO"],
             "larguras": [130, 120, 95, 90, 240]},
            [("Registrar alergia", self.nova_alergia_usuario),
             ("Nova alergia no catalogo", self.nova_alergia_catalogo)])
        return quadro

    def _aba_consultas(self):
        quadro, self.tabela_consultas = self._quadro_com_acoes(
            {"colunas": ["id_consulta", "data_hora", "profissional", "especialidade",
                         "motivo", "diagnostico"],
             "titulos": ["ID", "DATA/HORA", "PROFISSIONAL", "ESPECIALIDADE",
                         "MOTIVO", "DIAGNOSTICO"],
             "larguras": [40, 120, 150, 120, 180, 180]},
            [("Nova consulta", self.nova_consulta),
             ("Atualizar diagnostico", self.atualizar_consulta),
             ("Novo profissional", self.novo_profissional)])
        return quadro

    def _aba_exames(self):
        quadro, self.tabela_exames = self._quadro_com_acoes(
            {"colunas": ["id_exame", "tipo", "data_realizacao", "laboratorio",
                         "status", "resultado"],
             "titulos": ["ID", "TIPO", "DATA", "LABORATORIO", "STATUS", "RESULTADO"],
             "larguras": [40, 170, 90, 140, 95, 230]},
            [("Novo exame", self.novo_exame),
             ("Lancar resultado", self.lancar_resultado)])
        return quadro

    def _aba_vacinas(self):
        quadro = ttk.Frame(self.abas, padding=8)
        ttk.Label(quadro, text="Carteira de vacinacao").pack(anchor="w")
        self.tabela_vacinas = w.Tabela(
            quadro,
            colunas=["vacina", "dose", "doses_recomendadas", "data_aplicacao",
                     "lote", "local_aplicacao"],
            titulos=["VACINA", "DOSE", "RECOMENDADAS", "APLICACAO", "LOTE", "LOCAL"],
            larguras=[150, 55, 110, 100, 100, 160], altura=8)
        self.tabela_vacinas.pack(fill="both", expand=True, pady=(4, 8))

        ttk.Label(quadro, text="Doses em aberto").pack(anchor="w")
        self.tabela_doses = w.Tabela(
            quadro,
            colunas=["vacina", "aplicadas", "doses_recomendadas", "faltam", "ultima_dose"],
            titulos=["VACINA", "APLICADAS", "RECOMENDADAS", "FALTAM", "ULTIMA DOSE"],
            larguras=[150, 90, 110, 70, 110], altura=5)
        self.tabela_doses.pack(fill="both", expand=True, pady=(4, 0))

        barra = ttk.Frame(quadro)
        barra.pack(fill="x", pady=(8, 0))
        ttk.Button(barra, text="Registrar dose",
                   command=self.nova_dose).pack(side="left")
        return quadro

    def _aba_relatorios(self):
        quadro = ttk.Frame(self.abas, padding=8)
        self.painel_indicadores = ttk.Frame(quadro)
        self.painel_indicadores.pack(fill="x", pady=(0, 10))

        colunas = ttk.Frame(quadro)
        colunas.pack(fill="both", expand=True)
        colunas.columnconfigure(0, weight=1)
        colunas.columnconfigure(1, weight=1)
        colunas.rowconfigure(0, weight=1)
        colunas.rowconfigure(1, weight=1)

        esquerda = ttk.LabelFrame(colunas, text=" Alergias graves e moderadas ", padding=6)
        esquerda.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=(0, 6))
        self.tabela_rel_alergias = w.Tabela(
            esquerda, colunas=["usuario", "alergia", "gravidade"],
            titulos=["USUARIO", "ALERGIA", "GRAVIDADE"],
            larguras=[150, 130, 95], altura=6)
        self.tabela_rel_alergias.pack(fill="both", expand=True)

        direita = ttk.LabelFrame(colunas, text=" Exames pendentes ", padding=6)
        direita.grid(row=0, column=1, sticky="nsew", pady=(0, 6))
        self.tabela_rel_exames = w.Tabela(
            direita, colunas=["usuario", "tipo", "data_realizacao"],
            titulos=["USUARIO", "EXAME", "DATA"],
            larguras=[150, 150, 90], altura=6)
        self.tabela_rel_exames.pack(fill="both", expand=True)

        inferior_esq = ttk.LabelFrame(colunas, text=" Esquemas vacinais incompletos ", padding=6)
        inferior_esq.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        self.tabela_rel_vacinas = w.Tabela(
            inferior_esq, colunas=["usuario", "vacina", "aplicadas", "faltam"],
            titulos=["USUARIO", "VACINA", "APLICADAS", "FALTAM"],
            larguras=[150, 120, 85, 65], altura=6)
        self.tabela_rel_vacinas.pack(fill="both", expand=True)

        inferior_dir = ttk.LabelFrame(colunas, text=" Consultas por especialidade ", padding=6)
        inferior_dir.grid(row=1, column=1, sticky="nsew")
        self.tabela_rel_especialidades = w.Tabela(
            inferior_dir, colunas=["especialidade", "total", "ultima"],
            titulos=["ESPECIALIDADE", "TOTAL", "ULTIMA"],
            larguras=[160, 60, 130], altura=6)
        self.tabela_rel_especialidades.pack(fill="both", expand=True)
        return quadro

    # ------------------------------------------------------------ carregamento
    def _limpar_busca(self):
        self.entrada_busca.delete(0, "end")
        self.recarregar()

    def recarregar(self):
        termo = self.entrada_busca.get().strip()
        if termo:
            usuarios = repo.buscar_usuarios_por_nome(self.conexao, termo)
        else:
            usuarios = repo.listar_usuarios(self.conexao)
        self.tabela_usuarios.preencher(usuarios)

        self._carregar_relatorios()
        if self.id_usuario is None:
            self.tabela_usuarios.selecionar_primeiro()
        else:
            self._carregar_detalhes()

    def _selecionar_usuario(self):
        novo = self.tabela_usuarios.selecionado_int("id_usuario")
        if novo is None:
            return
        self.id_usuario = novo
        self._carregar_detalhes()

    def _carregar_detalhes(self):
        if self.id_usuario is None:
            return
        usuario = repo.buscar_usuario(self.conexao, self.id_usuario)
        if usuario is None:
            self.id_usuario = None
            return
        self.rotulo_ficha.configure(text=(
            "{nome}\n"
            "CPF: {cpf}    Nascimento: {nasc}    Sangue: {sangue}\n"
            "Telefone: {tel}    E-mail: {mail}").format(
                nome=usuario["nome"], cpf=usuario["cpf"],
                nasc=usuario["data_nascimento"], sangue=usuario["sangue"],
                tel=usuario["telefone"] or "-", mail=usuario["email"] or "-"))

        self.tabela_tempo.preencher(repo.linha_do_tempo(self.conexao, self.id_usuario))
        self.tabela_alergias.preencher(
            repo.listar_alergias_usuario(self.conexao, self.id_usuario),
            destacar=lambda l: l["gravidade"] == "GRAVE")
        self.tabela_consultas.preencher(
            repo.listar_consultas_usuario(self.conexao, self.id_usuario))
        self.tabela_exames.preencher(
            repo.listar_exames_usuario(self.conexao, self.id_usuario),
            destacar=lambda l: l["status"] == "PENDENTE")
        self.tabela_vacinas.preencher(
            repo.carteira_vacinacao(self.conexao, self.id_usuario))
        self.tabela_doses.preencher(
            repo.doses_pendentes(self.conexao, self.id_usuario))

    def _carregar_relatorios(self):
        for filho in self.painel_indicadores.winfo_children():
            filho.destroy()
        resumo = repo.resumo_geral(self.conexao)
        indicadores = [
            ("Usuarios", resumo["usuarios"], False),
            ("Consultas", resumo["consultas"], False),
            ("Exames", resumo["exames"], False),
            ("Exames pendentes", resumo["exames_pendentes"], resumo["exames_pendentes"] > 0),
            ("Doses aplicadas", resumo["doses_aplicadas"], False),
            ("Alergias", resumo["alergias_registradas"], False),
        ]
        for rotulo, valor, destaque in indicadores:
            w.cartao_indicador(self.painel_indicadores, rotulo, valor,
                               destaque).pack(side="left", padx=(0, 8))

        self.tabela_rel_alergias.preencher(
            repo.alergias_graves(self.conexao),
            destacar=lambda l: l["gravidade"] == "GRAVE")
        self.tabela_rel_exames.preencher(repo.exames_pendentes(self.conexao))
        self.tabela_rel_vacinas.preencher(repo.doses_pendentes(self.conexao))
        self.tabela_rel_especialidades.preencher(
            repo.consultas_por_especialidade(self.conexao))

    # ---------------------------------------------------------------- acoes
    def _exige_usuario(self):
        if self.id_usuario is None:
            messagebox.showinfo("Selecione um usuario",
                                "Escolha um usuario na lista a esquerda.", parent=self)
            return False
        return True

    def _formulario(self, titulo, campos):
        dialogo = w.Formulario(self.winfo_toplevel(), titulo, campos)
        return dialogo.resultado

    def novo_usuario(self):
        dados = self._formulario("Novo usuario", [
            w.campo("nome", "Nome completo"),
            w.campo("cpf", "CPF"),
            w.campo("data_nascimento", "Nascimento (YYYY-MM-DD)", "data"),
            w.campo("sexo", "Sexo", "opcao", opcoes=("M", "F", "O")),
            w.campo("tipo_sanguineo", "Tipo sanguineo", "opcao", opcoes=w.TIPOS_SANGUINEOS),
            w.campo("fator_rh", "Fator RH", "opcao", opcoes=w.FATORES_RH),
            w.campo("telefone", "Telefone", obrigatorio=False),
            w.campo("email", "E-mail", obrigatorio=False),
        ])
        if not dados:
            return
        try:
            self.id_usuario = repo.inserir_usuario(self.conexao, dados)
        except Exception as erro:
            messagebox.showerror("Erro ao inserir", str(erro), parent=self)
            return
        self.recarregar()
        messagebox.showinfo("Cadastro", "Usuario cadastrado com sucesso.", parent=self)

    def editar_contato(self):
        if not self._exige_usuario():
            return
        atual = repo.buscar_usuario(self.conexao, self.id_usuario)
        dados = self._formulario("Atualizar contato", [
            w.campo("telefone", "Telefone", obrigatorio=False,
                    padrao=atual["telefone"]),
            w.campo("email", "E-mail", obrigatorio=False, padrao=atual["email"]),
        ])
        if not dados:
            return
        repo.atualizar_contato(self.conexao, self.id_usuario,
                               dados["telefone"], dados["email"])
        self._carregar_detalhes()

    def nova_alergia_catalogo(self):
        dados = self._formulario("Nova alergia no catalogo", [
            w.campo("nome", "Nome da alergia"),
            w.campo("categoria", "Categoria", "opcao",
                    opcoes=("MEDICAMENTO", "ALIMENTO", "AMBIENTAL", "OUTRO")),
        ])
        if not dados:
            return
        try:
            repo.inserir_alergia_catalogo(self.conexao, dados["nome"], dados["categoria"])
        except Exception as erro:
            messagebox.showerror("Erro ao inserir", str(erro), parent=self)

    def nova_alergia_usuario(self):
        if not self._exige_usuario():
            return
        catalogo = [(l["id_alergia"], "{0} ({1})".format(l["nome"], l["categoria"]))
                    for l in repo.listar_catalogo_alergias(self.conexao)]
        dados = self._formulario("Registrar alergia do usuario", [
            w.campo("id_alergia", "Alergia", "lista", itens=catalogo),
            w.campo("gravidade", "Gravidade", "opcao",
                    opcoes=("LEVE", "MODERADA", "GRAVE")),
            w.campo("observacao", "Observacao", "memo", obrigatorio=False),
        ])
        if not dados:
            return
        try:
            repo.vincular_alergia(self.conexao, self.id_usuario, dados["id_alergia"],
                                  dados["gravidade"], dados["observacao"])
        except Exception as erro:
            messagebox.showerror("Erro ao inserir",
                                 "Esta alergia ja esta registrada para o usuario.\n\n"
                                 + str(erro), parent=self)
            return
        self._carregar_detalhes()
        self._carregar_relatorios()

    def novo_profissional(self):
        dados = self._formulario("Novo profissional", [
            w.campo("nome", "Nome"),
            w.campo("especialidade", "Especialidade"),
            w.campo("registro", "Registro (CRM/COREN)"),
        ])
        if not dados:
            return
        try:
            repo.inserir_profissional(self.conexao, dados["nome"],
                                      dados["especialidade"], dados["registro"])
        except Exception as erro:
            messagebox.showerror("Erro ao inserir", str(erro), parent=self)

    def nova_consulta(self):
        if not self._exige_usuario():
            return
        profissionais = [(l["id_profissional"],
                          "{0} - {1}".format(l["nome"], l["especialidade"]))
                         for l in repo.listar_profissionais(self.conexao)]
        if not profissionais:
            messagebox.showinfo("Sem profissionais",
                                "Cadastre um profissional primeiro.", parent=self)
            return
        dados = self._formulario("Nova consulta", [
            w.campo("id_profissional", "Profissional", "lista", itens=profissionais),
            w.campo("data_hora", "Data e hora", "data_hora",
                    padrao=hoje() + " 09:00"),
            w.campo("motivo", "Motivo"),
            w.campo("diagnostico", "Diagnostico", "memo", obrigatorio=False),
            w.campo("prescricao", "Prescricao", "memo", obrigatorio=False),
        ])
        if not dados:
            return
        dados["id_usuario"] = self.id_usuario
        repo.inserir_consulta(self.conexao, dados)
        self._carregar_detalhes()
        self._carregar_relatorios()

    def atualizar_consulta(self):
        if not self._exige_usuario():
            return
        id_consulta = self.tabela_consultas.selecionado_int("id_consulta")
        if id_consulta is None:
            messagebox.showinfo("Selecione a consulta",
                                "Escolha uma consulta na tabela.", parent=self)
            return
        dados = self._formulario("Atualizar consulta {0}".format(id_consulta), [
            w.campo("diagnostico", "Diagnostico", "memo"),
            w.campo("prescricao", "Prescricao", "memo", obrigatorio=False),
        ])
        if not dados:
            return
        repo.atualizar_consulta(self.conexao, id_consulta,
                                dados["diagnostico"], dados["prescricao"])
        self._carregar_detalhes()

    def novo_exame(self):
        if not self._exige_usuario():
            return
        consultas = [(0, "(sem vinculo com consulta)")]
        consultas += [(l["id_consulta"],
                       "{0} - {1}".format(l["data_hora"], l["motivo"]))
                      for l in repo.listar_consultas_usuario(self.conexao, self.id_usuario)]
        dados = self._formulario("Novo exame", [
            w.campo("tipo", "Tipo de exame"),
            w.campo("data_realizacao", "Data (YYYY-MM-DD)", "data", padrao=hoje()),
            w.campo("laboratorio", "Laboratorio", obrigatorio=False),
            w.campo("status", "Status", "opcao",
                    opcoes=("PENDENTE", "CONCLUIDO", "CANCELADO")),
            w.campo("resultado", "Resultado", "memo", obrigatorio=False),
            w.campo("id_consulta", "Consulta de origem", "lista", itens=consultas),
        ])
        if not dados:
            return
        if not dados["id_consulta"]:
            dados["id_consulta"] = None
        dados["id_usuario"] = self.id_usuario
        repo.inserir_exame(self.conexao, dados)
        self._carregar_detalhes()
        self._carregar_relatorios()

    def lancar_resultado(self):
        if not self._exige_usuario():
            return
        id_exame = self.tabela_exames.selecionado_int("id_exame")
        if id_exame is None:
            messagebox.showinfo("Selecione o exame",
                                "Escolha um exame na tabela.", parent=self)
            return
        if self.tabela_exames.selecionado("status") != "PENDENTE":
            if not messagebox.askyesno("Exame nao pendente",
                                       "Este exame nao esta pendente. Deseja "
                                       "sobrescrever o resultado?", parent=self):
                return
        dados = self._formulario("Lancar resultado do exame {0}".format(id_exame), [
            w.campo("resultado", "Resultado", "memo"),
        ])
        if not dados:
            return
        repo.lancar_resultado_exame(self.conexao, id_exame, dados["resultado"])
        self._carregar_detalhes()
        self._carregar_relatorios()

    def nova_dose(self):
        if not self._exige_usuario():
            return
        vacinas = [(l["id_vacina"], "{0} ({1} dose(s))".format(
            l["nome"], l["doses_recomendadas"]))
            for l in repo.listar_catalogo_vacinas(self.conexao)]
        dados = self._formulario("Registrar dose de vacina", [
            w.campo("id_vacina", "Vacina", "lista", itens=vacinas),
            w.campo("dose", "Numero da dose", "inteiro", padrao=1),
            w.campo("data_aplicacao", "Data (YYYY-MM-DD)", "data", padrao=hoje()),
            w.campo("lote", "Lote", obrigatorio=False),
            w.campo("local_aplicacao", "Local de aplicacao", obrigatorio=False),
        ])
        if not dados:
            return
        dados["id_usuario"] = self.id_usuario
        try:
            repo.inserir_vacinacao(self.conexao, dados)
        except Exception as erro:
            messagebox.showerror("Erro ao inserir",
                                 "Esta dose ja foi registrada para o usuario.\n\n"
                                 + str(erro), parent=self)
            return
        self._carregar_detalhes()
        self._carregar_relatorios()
