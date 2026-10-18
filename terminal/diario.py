# -*- coding: utf-8 -*-
"""DIARIO DE SAUDE PESSOAL - menus interativos de terminal.

Toda leitura e escrita passa pelo backend (DiarioService); esta camada so
cuida da conversa com o usuario. As opcoes de sexo, tipo sanguineo, fator RH,
gravidade e status de doenca vem dos ENUMs do proprio banco.
"""

from backend.diario.servico import DiarioService
from backend.erros import ErroDeNegocio
from terminal import ui
from terminal.ui import agora, hoje, valor_do_campo
from terminal.enums import enums_do_banco, sangue

CABECALHO = "DIARIO DE SAUDE PESSOAL"

SERVICO = None
ENUM = {}


# ---------------------------------------------------------------------------
# Selecao de registros
# ---------------------------------------------------------------------------
def escolher(linhas, campo_id, rotulo, colunas=None, titulos=None,
             vazio="Nenhum registro encontrado."):
    ui.tabela(linhas, colunas=colunas, titulos=titulos, vazio=vazio)
    if not linhas:
        return None
    validos = [valor_do_campo(l, campo_id) for l in linhas]
    while True:
        escolha = ui.ler_inteiro("\n  " + rotulo + " (0 cancela)", minimo=0)
        if escolha == 0:
            return None
        if escolha in validos:
            return escolha
        ui.aviso("ID inexistente.")


def escolher_usuario():
    return escolher(SERVICO.listar_usuarios(), "id", "ID do usuario",
                    colunas=["id", "nome", "cpf", "tipo_sanguineo", "fator_rh", "cidade"],
                    titulos=["ID", "NOME", "CPF", "ABO", "RH", "CIDADE"])


# ---------------------------------------------------------------------------
# 1. USUARIOS
# ---------------------------------------------------------------------------
COLUNAS_USUARIO = ["id", "nome", "cpf", "data_nascimento", "sexo",
                   "tipo_sanguineo", "fator_rh", "cidade", "uf"]
TITULOS_USUARIO = ["ID", "NOME", "CPF", "NASCIMENTO", "SEXO", "ABO", "RH",
                   "CIDADE", "UF"]


def usuarios_listar():
    ui.secao("Usuarios cadastrados")
    ui.tabela(SERVICO.listar_usuarios(), colunas=COLUNAS_USUARIO,
              titulos=TITULOS_USUARIO)


def usuarios_buscar():
    ui.secao("Busca por nome ou CPF")
    termo = ui.ler_texto("Termo de busca")
    ui.tabela(SERVICO.listar_usuarios(termo), colunas=COLUNAS_USUARIO,
              titulos=TITULOS_USUARIO, vazio="Nenhum usuario encontrado.")


def usuarios_cadastrar():
    ui.secao("Cadastro de usuario (INSERT)")
    dados = {
        "nome": ui.ler_texto("Nome completo"),
        "cpf": ui.ler_texto("CPF (11 digitos)"),
        "data_nascimento": ui.ler_data("Data de nascimento"),
        "sexo": ui.ler_opcao("Sexo", ENUM["sexo"]),
        "cidade": ui.ler_texto("Cidade", obrigatorio=False),
        "uf": ui.ler_texto("UF", obrigatorio=False),
        "email": ui.ler_texto("E-mail", obrigatorio=False),
        "telefone": ui.ler_texto("Telefone", obrigatorio=False),
    }
    if ui.confirmar("Informar o tipo sanguineo agora?"):
        dados["tipo_sanguineo"] = ui.ler_opcao("Tipo sanguineo", ENUM["tipo_sanguineo"])
        dados["fator_rh"] = ui.ler_opcao("Fator RH", ENUM["fator_rh"])
    if dados["uf"]:
        dados["uf"] = dados["uf"].upper()
    novo = SERVICO.cadastrar_usuario(**dados)
    ui.sucesso("Usuario cadastrado com o ID {0}.".format(novo.id))


def usuarios_atualizar():
    ui.secao("Atualizar dados do usuario (UPDATE)")
    usuario_id = escolher_usuario()
    if usuario_id is None:
        return
    atual = SERVICO.buscar_usuario(usuario_id)
    campos = {
        "telefone": ui.ler_texto("Telefone", obrigatorio=False, padrao=atual.telefone),
        "email": ui.ler_texto("E-mail", obrigatorio=False, padrao=atual.email),
        "cidade": ui.ler_texto("Cidade", obrigatorio=False, padrao=atual.cidade),
        "uf": ui.ler_texto("UF", obrigatorio=False, padrao=atual.uf),
    }
    campos = {c: v for c, v in campos.items() if v is not None}
    if campos.get("uf"):
        campos["uf"] = campos["uf"].upper()
    SERVICO.atualizar_usuario(usuario_id, **campos)
    ui.sucesso("Dados atualizados.")


def usuarios_tipagem():
    ui.secao("Registrar/corrigir tipagem sanguinea (UPDATE)")
    usuario_id = escolher_usuario()
    if usuario_id is None:
        return
    atual = SERVICO.buscar_usuario(usuario_id)
    print("\n  Tipagem atual: {0}".format(sangue(atual.tipo_sanguineo, atual.fator_rh)))
    tipo = ui.ler_opcao("Tipo sanguineo", ENUM["tipo_sanguineo"],
                        padrao=atual.tipo_sanguineo)
    fator = ui.ler_opcao("Fator RH", ENUM["fator_rh"], padrao=atual.fator_rh)
    SERVICO.registrar_tipagem(usuario_id, tipo, fator)
    ui.sucesso("Tipagem registrada: {0}.".format(sangue(tipo, fator)))


def usuarios_ficha():
    ui.secao("Ficha / prontuario completo")
    usuario_id = escolher_usuario()
    if usuario_id is None:
        return
    prontuario = SERVICO.prontuario(usuario_id)
    ficha = SERVICO.ficha(usuario_id)      # traz idade, sangue e restricao
    ui.limpar()
    ui.titulo("PRONTUARIO", ficha.nome)
    print("\n  CPF............: {0}".format(ficha.cpf))
    print("  Nascimento.....: {0} ({1} anos)".format(ficha.data_nascimento, ficha.idade))
    print("  Sexo...........: {0}".format(ficha.sexo))
    print("  Tipo sanguineo.: {0}".format(ficha.sangue or "nao informado"))
    print("  Cidade/UF......: {0}/{1}".format(ficha.cidade or "-", ficha.uf or "-"))
    if ficha.restricao_doacao:
        ui.aviso("Possui doenca ativa que impede a doacao de orgaos.")
    if ficha.alergias:
        print("\n  Alergias.......: {0}".format(ficha.alergias))

    ui.secao("Diagnosticos")
    ui.tabela(prontuario.diagnosticos,
              colunas=["id", "doenca", "cid", "data_diagnostico", "status", "impede_doacao"],
              titulos=["ID", "DOENCA", "CID", "DIAGNOSTICO", "STATUS", "IMPEDE DOACAO"],
              vazio="Nenhum diagnostico registrado.")
    ui.secao("Consultas")
    ui.tabela(prontuario.consultas,
              colunas=["data_hora", "especialidade", "profissional", "local"],
              titulos=["DATA/HORA", "ESPECIALIDADE", "PROFISSIONAL", "LOCAL"],
              vazio="Nenhuma consulta registrada.")
    ui.secao("Exames")
    ui.tabela(prontuario.exames, colunas=["tipo", "data", "resultado"],
              titulos=["TIPO", "DATA", "RESULTADO"],
              vazio="Nenhum exame registrado.")
    ui.secao("Cartao de vacinacao")
    ui.tabela(prontuario.vacinas,
              colunas=["vacina", "fabricante", "dose", "data_aplicacao", "lote"],
              titulos=["VACINA", "FABRICANTE", "DOSE", "APLICACAO", "LOTE"],
              vazio="Nenhuma dose registrada.")
    ui.secao("Metricas de saude")
    ui.tabela(prontuario.metricas,
              colunas=["tipo", "valor", "unidade", "data_hora", "variacao"],
              titulos=["TIPO", "VALOR", "UNIDADE", "DATA/HORA", "VARIACAO"],
              vazio="Nenhuma metrica registrada.")


def usuarios_linha_do_tempo():
    ui.secao("Linha do tempo de saude")
    usuario_id = escolher_usuario()
    if usuario_id is None:
        return
    ui.tabela(SERVICO.linha_do_tempo(usuario_id),
              colunas=["data", "evento", "descricao"],
              titulos=["DATA", "EVENTO", "DESCRICAO"],
              vazio="Nenhum evento registrado.")


@ui.submenu
def menu_usuarios():
    ui.executar_menu(CABECALHO, [
        ("Listar usuarios", usuarios_listar),
        ("Buscar por nome/CPF", usuarios_buscar),
        ("Cadastrar usuario", usuarios_cadastrar),
        ("Atualizar contato e cidade", usuarios_atualizar),
        ("Registrar tipagem sanguinea", usuarios_tipagem),
        ("Prontuario completo", usuarios_ficha),
        ("Linha do tempo", usuarios_linha_do_tempo),
    ], subtitulo="1. Usuarios")


# ---------------------------------------------------------------------------
# 2. ALERGIAS
# ---------------------------------------------------------------------------
def alergias_listar():
    ui.secao("Alergias de um usuario")
    usuario_id = escolher_usuario()
    if usuario_id is None:
        return
    ui.tabela(SERVICO.listar_alergias(usuario_id),
              colunas=["id", "substancia", "gravidade", "observacao"],
              titulos=["ID", "SUBSTANCIA", "GRAVIDADE", "OBSERVACAO"],
              vazio="Nenhuma alergia registrada.")


def alergias_registrar():
    ui.secao("Registrar alergia (INSERT)")
    usuario_id = escolher_usuario()
    if usuario_id is None:
        return
    substancia = ui.ler_texto("Substancia")
    gravidade = ui.ler_opcao("Gravidade", ENUM["gravidade_alergia"])
    observacao = ui.ler_texto("Observacao", obrigatorio=False)
    nova = SERVICO.adicionar_alergia(usuario_id, substancia, gravidade, observacao)
    ui.sucesso("Alergia registrada com o ID {0}.".format(nova.id))


def alergias_atualizar_gravidade():
    ui.secao("Atualizar gravidade da alergia (UPDATE)")
    usuario_id = escolher_usuario()
    if usuario_id is None:
        return
    alergia_id = escolher(SERVICO.listar_alergias(usuario_id), "id", "ID da alergia",
                          colunas=["id", "substancia", "gravidade", "observacao"],
                          titulos=["ID", "SUBSTANCIA", "GRAVIDADE", "OBSERVACAO"])
    if alergia_id is None:
        return
    gravidade = ui.ler_opcao("Nova gravidade", ENUM["gravidade_alergia"])
    SERVICO.atualizar_gravidade_alergia(alergia_id, gravidade)
    ui.sucesso("Gravidade atualizada para {0}.".format(gravidade))


def alergias_remover():
    ui.secao("Remover alergia (DELETE)")
    usuario_id = escolher_usuario()
    if usuario_id is None:
        return
    alergia_id = escolher(SERVICO.listar_alergias(usuario_id), "id", "ID da alergia",
                          colunas=["id", "substancia", "gravidade", "observacao"],
                          titulos=["ID", "SUBSTANCIA", "GRAVIDADE", "OBSERVACAO"])
    if alergia_id is None:
        return
    if ui.confirmar("Confirmar remocao"):
        SERVICO.remover_alergia(alergia_id)
        ui.sucesso("Alergia removida.")


@ui.submenu
def menu_alergias():
    ui.executar_menu(CABECALHO, [
        ("Alergias de um usuario", alergias_listar),
        ("Registrar alergia", alergias_registrar),
        ("Atualizar gravidade", alergias_atualizar_gravidade),
        ("Remover alergia", alergias_remover),
    ], subtitulo="2. Alergias")


# ---------------------------------------------------------------------------
# 3. DOENCAS
# ---------------------------------------------------------------------------
def doencas_catalogo():
    ui.secao("Catalogo de doencas")
    ui.tabela(SERVICO.listar_catalogo_doencas(),
              colunas=["id", "nome", "cid", "impede_doacao"],
              titulos=["ID", "DOENCA", "CID", "IMPEDE DOACAO"])


def doencas_cadastrar():
    ui.secao("Cadastrar doenca no catalogo (INSERT)")
    nome = ui.ler_texto("Nome da doenca")
    cid = ui.ler_texto("CID", obrigatorio=False)
    impede = ui.confirmar("Impede a doacao de orgaos?")
    nova = SERVICO.cadastrar_doenca(nome, cid, impede)
    ui.sucesso("Doenca cadastrada com o ID {0}.".format(nova.id))


def doencas_do_usuario():
    ui.secao("Diagnosticos de um usuario")
    usuario_id = escolher_usuario()
    if usuario_id is None:
        return
    ui.tabela(SERVICO.listar_diagnosticos(usuario_id),
              colunas=["id", "doenca", "cid", "data_diagnostico", "status", "impede_doacao"],
              titulos=["ID", "DOENCA", "CID", "DIAGNOSTICO", "STATUS", "IMPEDE DOACAO"],
              vazio="Nenhum diagnostico registrado.")


def doencas_registrar():
    ui.secao("Registrar diagnostico (INSERT)")
    usuario_id = escolher_usuario()
    if usuario_id is None:
        return
    print()
    doenca_id = escolher(SERVICO.listar_catalogo_doencas(), "id", "ID da doenca",
                         colunas=["id", "nome", "cid", "impede_doacao"],
                         titulos=["ID", "DOENCA", "CID", "IMPEDE DOACAO"])
    if doenca_id is None:
        return
    data = ui.ler_data("Data do diagnostico", padrao=hoje())
    status = ui.ler_opcao("Status", ENUM["status_doenca"], padrao="ativa")
    novo = SERVICO.registrar_diagnostico(usuario_id, doenca_id, data, status)
    ui.sucesso("Diagnostico registrado com o ID {0}.".format(novo.id))


def doencas_atualizar_status():
    ui.secao("Atualizar status do diagnostico (UPDATE)")
    usuario_id = escolher_usuario()
    if usuario_id is None:
        return
    diagnostico_id = escolher(SERVICO.listar_diagnosticos(usuario_id), "id",
                              "ID do diagnostico",
                              colunas=["id", "doenca", "data_diagnostico", "status"],
                              titulos=["ID", "DOENCA", "DIAGNOSTICO", "STATUS"])
    if diagnostico_id is None:
        return
    status = ui.ler_opcao("Novo status", ENUM["status_doenca"])
    SERVICO.atualizar_status_doenca(diagnostico_id, status)
    ui.sucesso("Status atualizado para {0}.".format(status))


@ui.submenu
def menu_doencas():
    ui.executar_menu(CABECALHO, [
        ("Catalogo de doencas", doencas_catalogo),
        ("Cadastrar doenca no catalogo", doencas_cadastrar),
        ("Diagnosticos de um usuario", doencas_do_usuario),
        ("Registrar diagnostico", doencas_registrar),
        ("Atualizar status do diagnostico", doencas_atualizar_status),
    ], subtitulo="3. Doencas")


# ---------------------------------------------------------------------------
# 4. CONSULTAS E EXAMES
# ---------------------------------------------------------------------------
def consultas_listar():
    ui.secao("Consultas de um usuario")
    usuario_id = escolher_usuario()
    if usuario_id is None:
        return
    ui.tabela(SERVICO.listar_consultas(usuario_id),
              colunas=["id", "data_hora", "especialidade", "profissional", "local",
                       "observacoes"],
              titulos=["ID", "DATA/HORA", "ESPECIALIDADE", "PROFISSIONAL", "LOCAL",
                       "OBSERVACOES"],
              vazio="Nenhuma consulta registrada.")


def consultas_registrar():
    ui.secao("Registrar consulta (INSERT)")
    usuario_id = escolher_usuario()
    if usuario_id is None:
        return
    data_hora = ui.ler_data_hora("Data e hora", )
    especialidade = ui.ler_texto("Especialidade")
    profissional = ui.ler_texto("Profissional", obrigatorio=False)
    local = ui.ler_texto("Local", obrigatorio=False)
    observacoes = ui.ler_texto("Observacoes", obrigatorio=False)
    nova = SERVICO.registrar_consulta(usuario_id, data_hora, especialidade,
                                      profissional, local, observacoes)
    ui.sucesso("Consulta registrada com o ID {0}.".format(nova.id))


def consultas_atualizar():
    ui.secao("Atualizar observacoes da consulta (UPDATE)")
    usuario_id = escolher_usuario()
    if usuario_id is None:
        return
    consulta_id = escolher(SERVICO.listar_consultas(usuario_id), "id",
                           "ID da consulta",
                           colunas=["id", "data_hora", "especialidade", "observacoes"],
                           titulos=["ID", "DATA/HORA", "ESPECIALIDADE", "OBSERVACOES"])
    if consulta_id is None:
        return
    observacoes = ui.ler_texto("Observacoes", obrigatorio=False)
    SERVICO.atualizar_consulta(consulta_id, observacoes)
    ui.sucesso("Consulta atualizada.")


def exames_listar():
    ui.secao("Exames de um usuario")
    usuario_id = escolher_usuario()
    if usuario_id is None:
        return
    ui.tabela(SERVICO.listar_exames(usuario_id),
              colunas=["id", "tipo", "data", "resultado", "consulta_id"],
              titulos=["ID", "TIPO", "DATA", "RESULTADO", "CONSULTA"],
              vazio="Nenhum exame registrado.")


def exames_registrar():
    ui.secao("Registrar exame (INSERT)")
    usuario_id = escolher_usuario()
    if usuario_id is None:
        return
    consulta_id = None
    consultas = SERVICO.listar_consultas(usuario_id)
    if consultas and ui.confirmar("Vincular a uma consulta?"):
        print()
        consulta_id = escolher(consultas, "id", "ID da consulta",
                               colunas=["id", "data_hora", "especialidade"],
                               titulos=["ID", "DATA/HORA", "ESPECIALIDADE"])
    tipo = ui.ler_texto("Tipo de exame")
    data = ui.ler_data("Data de realizacao", padrao=hoje())
    resultado = ui.ler_texto("Resultado", obrigatorio=False)
    novo = SERVICO.registrar_exame(usuario_id, tipo, data, resultado, consulta_id)
    ui.sucesso("Exame registrado com o ID {0}.".format(novo.id))


@ui.submenu
def menu_consultas():
    ui.executar_menu(CABECALHO, [
        ("Consultas de um usuario", consultas_listar),
        ("Registrar consulta", consultas_registrar),
        ("Atualizar observacoes da consulta", consultas_atualizar),
        ("Exames de um usuario", exames_listar),
        ("Registrar exame", exames_registrar),
    ], subtitulo="4. Consultas e exames")


# ---------------------------------------------------------------------------
# 5. VACINAS
# ---------------------------------------------------------------------------
def vacinas_catalogo():
    ui.secao("Catalogo de vacinas")
    ui.tabela(SERVICO.listar_catalogo_vacinas(),
              colunas=["id", "nome", "fabricante"],
              titulos=["ID", "VACINA", "FABRICANTE"])


def vacinas_cadastrar():
    ui.secao("Cadastrar vacina no catalogo (INSERT)")
    nome = ui.ler_texto("Nome da vacina")
    fabricante = ui.ler_texto("Fabricante", obrigatorio=False)
    nova = SERVICO.cadastrar_vacina(nome, fabricante)
    ui.sucesso("Vacina cadastrada com o ID {0}.".format(nova.id))


def vacinas_cartao():
    ui.secao("Cartao de vacinacao")
    usuario_id = escolher_usuario()
    if usuario_id is None:
        return
    ui.tabela(SERVICO.cartao_vacinacao(usuario_id),
              colunas=["id", "vacina", "fabricante", "dose", "data_aplicacao", "lote"],
              titulos=["ID", "VACINA", "FABRICANTE", "DOSE", "APLICACAO", "LOTE"],
              vazio="Nenhuma dose registrada.")


def vacinas_registrar():
    ui.secao("Registrar aplicacao de vacina (INSERT)")
    usuario_id = escolher_usuario()
    if usuario_id is None:
        return
    print()
    vacina_id = escolher(SERVICO.listar_catalogo_vacinas(), "id", "ID da vacina",
                         colunas=["id", "nome", "fabricante"],
                         titulos=["ID", "VACINA", "FABRICANTE"])
    if vacina_id is None:
        return
    data = ui.ler_data("Data de aplicacao", padrao=hoje())
    dose = ui.ler_texto("Dose (1a dose, reforco, anual...)")
    lote = ui.ler_texto("Lote", obrigatorio=False)
    nova = SERVICO.registrar_vacina(usuario_id, vacina_id, data, dose, lote)
    ui.sucesso("Dose registrada com o ID {0}.".format(nova.id))


@ui.submenu
def menu_vacinas():
    ui.executar_menu(CABECALHO, [
        ("Catalogo de vacinas", vacinas_catalogo),
        ("Cadastrar vacina no catalogo", vacinas_cadastrar),
        ("Cartao de vacinacao", vacinas_cartao),
        ("Registrar aplicacao", vacinas_registrar),
    ], subtitulo="5. Vacinas")


# ---------------------------------------------------------------------------
# 6. METRICAS
# ---------------------------------------------------------------------------
def metricas_listar():
    ui.secao("Metricas de um usuario")
    usuario_id = escolher_usuario()
    if usuario_id is None:
        return
    por_tipo = SERVICO.metricas_por_tipo(usuario_id)
    if not por_tipo:
        ui.aviso("Nenhuma metrica registrada.")
        return
    for tipo, medicoes in sorted(por_tipo.items()):
        ui.secao(tipo)
        ui.tabela(medicoes, colunas=["data_hora", "valor", "unidade", "variacao"],
                  titulos=["DATA/HORA", "VALOR", "UNIDADE", "VARIACAO"])


def metricas_registrar():
    ui.secao("Registrar metrica (INSERT)")
    usuario_id = escolher_usuario()
    if usuario_id is None:
        return
    tipo = ui.ler_texto("Tipo (Peso, Glicemia, Pressao sistolica...)")
    bruto = ui.ler_texto("Valor")
    try:
        valor = float(bruto.replace(",", "."))
    except ValueError:
        ui.aviso("Valor numerico invalido.")
        return
    unidade = ui.ler_texto("Unidade (kg, mg/dL, mmHg)")
    data_hora = ui.ler_data_hora("Data e hora")
    nova = SERVICO.registrar_metrica(usuario_id, tipo, valor, unidade, data_hora)
    ui.sucesso("Metrica registrada com o ID {0}.".format(nova.id))


def metricas_historico():
    ui.secao("Historico de uma metrica")
    usuario_id = escolher_usuario()
    if usuario_id is None:
        return
    por_tipo = SERVICO.metricas_por_tipo(usuario_id)
    if not por_tipo:
        ui.aviso("Nenhuma metrica registrada.")
        return
    tipo = ui.ler_opcao("Tipo", sorted(por_tipo))
    escolhido = [t for t in por_tipo if t.upper() == tipo][0]
    ui.tabela(SERVICO.historico_metrica(usuario_id, escolhido),
              colunas=["data_hora", "valor", "unidade", "variacao"],
              titulos=["DATA/HORA", "VALOR", "UNIDADE", "VARIACAO"])


@ui.submenu
def menu_metricas():
    ui.executar_menu(CABECALHO, [
        ("Metricas de um usuario", metricas_listar),
        ("Registrar metrica", metricas_registrar),
        ("Historico de uma metrica", metricas_historico),
    ], subtitulo="6. Metricas de saude")


# ---------------------------------------------------------------------------
# MENU PRINCIPAL
# ---------------------------------------------------------------------------
def principal(servico=None):
    global SERVICO, ENUM
    proprio = servico is None
    SERVICO = servico or DiarioService()
    ENUM = enums_do_banco(SERVICO.conexao)
    try:
        ui.executar_menu(CABECALHO, [
            ("Usuarios", menu_usuarios),
            ("Alergias", menu_alergias),
            ("Doencas", menu_doencas),
            ("Consultas e exames", menu_consultas),
            ("Vacinas", menu_vacinas),
            ("Metricas de saude", menu_metricas),
        ], subtitulo="Sistema 1 - PostgreSQL", rotulo_saida="Sair")
    finally:
        if proprio:
            SERVICO.fechar()


if __name__ == "__main__":
    try:
        principal()
    except ErroDeNegocio as erro:
        ui.aviso(str(erro))
