# -*- coding: utf-8 -*-
"""DIARIO DE SAUDE PESSOAL - menus interativos de terminal.

Execucao:
    python3 DiarioPessoal/DiarioPessoal.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import db, ui
from DiarioPessoal import repositorio as repo

CABECALHO = "DIARIO DE SAUDE PESSOAL"

# Conexao unica usada por todos os menus
CONEXAO = None


# ---------------------------------------------------------------------------
# Selecao de registros (apoio aos formularios)
# ---------------------------------------------------------------------------
def escolher_usuario(rotulo="Informe o ID do usuario"):
    usuarios = repo.listar_usuarios(CONEXAO)
    ui.tabela(usuarios,
              colunas=["id_usuario", "nome", "sangue", "idade", "telefone"],
              titulos=["ID", "NOME", "SANGUE", "IDADE", "TELEFONE"])
    if not usuarios:
        return None
    validos = [u["id_usuario"] for u in usuarios]
    while True:
        escolha = ui.ler_inteiro("\n  " + rotulo, minimo=0)
        if escolha == 0:
            return None
        if escolha in validos:
            return escolha
        ui.aviso("ID inexistente. Digite 0 para cancelar.")


def escolher_de_tabela(linhas, coluna_id, rotulo, colunas=None, titulos=None):
    ui.tabela(linhas, colunas=colunas, titulos=titulos)
    if not linhas:
        return None
    validos = [l[coluna_id] for l in linhas]
    while True:
        escolha = ui.ler_inteiro("\n  " + rotulo + " (0 cancela)", minimo=0)
        if escolha == 0:
            return None
        if escolha in validos:
            return escolha
        ui.aviso("ID inexistente.")


# ---------------------------------------------------------------------------
# 1. USUARIOS
# ---------------------------------------------------------------------------
def usuarios_listar():
    ui.secao("Usuarios cadastrados")
    ui.tabela(repo.listar_usuarios(CONEXAO),
              colunas=["id_usuario", "nome", "cpf", "sangue", "data_nascimento",
                       "idade", "telefone"],
              titulos=["ID", "NOME", "CPF", "SANGUE", "NASCIMENTO", "IDADE", "TELEFONE"])


def usuarios_cadastrar():
    ui.secao("Cadastro de usuario (INSERT)")
    dados = {
        "nome": ui.ler_texto("Nome completo"),
        "cpf": ui.ler_texto("CPF"),
        "data_nascimento": ui.ler_data("Data de nascimento"),
        "sexo": ui.ler_opcao("Sexo", ("M", "F", "O")),
        "tipo_sanguineo": ui.ler_opcao("Tipo sanguineo", ui.TIPOS_SANGUINEOS),
        "fator_rh": ui.ler_opcao("Fator RH", ui.FATORES_RH),
        "telefone": ui.ler_texto("Telefone", obrigatorio=False),
        "email": ui.ler_texto("E-mail", obrigatorio=False),
    }
    novo = repo.inserir_usuario(CONEXAO, dados)
    ui.sucesso("Usuario cadastrado com o ID {0}.".format(novo))


def usuarios_buscar():
    ui.secao("Busca por nome ou CPF")
    termo = ui.ler_texto("Termo de busca")
    ui.tabela(repo.buscar_usuarios_por_nome(CONEXAO, termo),
              colunas=["id_usuario", "nome", "cpf", "sangue", "idade", "telefone"],
              titulos=["ID", "NOME", "CPF", "SANGUE", "IDADE", "TELEFONE"])


def usuarios_atualizar_contato():
    ui.secao("Atualizacao de contato (UPDATE)")
    id_usuario = escolher_usuario()
    if id_usuario is None:
        return
    atual = repo.buscar_usuario(CONEXAO, id_usuario)
    print("\n  Telefone atual: {0}\n  E-mail atual:   {1}".format(
        atual["telefone"], atual["email"]))
    telefone = ui.ler_texto("Novo telefone", padrao=atual["telefone"])
    email = ui.ler_texto("Novo e-mail", padrao=atual["email"])
    repo.atualizar_contato(CONEXAO, id_usuario, telefone, email)
    ui.sucesso("Contato atualizado.")


def usuarios_atualizar_sangue():
    ui.secao("Correcao de tipo sanguineo / fator RH (UPDATE)")
    id_usuario = escolher_usuario()
    if id_usuario is None:
        return
    atual = repo.buscar_usuario(CONEXAO, id_usuario)
    print("\n  Registro atual: {0}".format(atual["sangue"]))
    tipo = ui.ler_opcao("Tipo sanguineo", ui.TIPOS_SANGUINEOS, padrao=atual["tipo_sanguineo"])
    rh = ui.ler_opcao("Fator RH", ui.FATORES_RH, padrao=atual["fator_rh"])
    repo.atualizar_tipo_sanguineo(CONEXAO, id_usuario, tipo, rh)
    ui.sucesso("Tipo sanguineo atualizado para {0}{1}.".format(tipo, rh))


def usuarios_ficha_completa():
    ui.secao("Ficha de saude completa")
    id_usuario = escolher_usuario()
    if id_usuario is None:
        return
    usuario = repo.buscar_usuario(CONEXAO, id_usuario)
    ui.limpar()
    ui.titulo("FICHA DE SAUDE", usuario["nome"])
    print("\n  CPF............: {0}".format(usuario["cpf"]))
    print("  Nascimento.....: {0}".format(usuario["data_nascimento"]))
    print("  Tipo sanguineo.: {0}".format(usuario["sangue"]))
    print("  Telefone.......: {0}".format(usuario["telefone"] or "-"))
    print("  E-mail.........: {0}".format(usuario["email"] or "-"))

    ui.secao("Alergias")
    ui.tabela(repo.listar_alergias_usuario(CONEXAO, id_usuario),
              vazio="Nenhuma alergia registrada.")
    ui.secao("Consultas")
    ui.tabela(repo.listar_consultas_usuario(CONEXAO, id_usuario),
              colunas=["data_hora", "profissional", "especialidade", "motivo", "diagnostico"],
              titulos=["DATA/HORA", "PROFISSIONAL", "ESPECIALIDADE", "MOTIVO", "DIAGNOSTICO"],
              vazio="Nenhuma consulta registrada.")
    ui.secao("Exames")
    ui.tabela(repo.listar_exames_usuario(CONEXAO, id_usuario),
              colunas=["tipo", "data_realizacao", "laboratorio", "status", "resultado"],
              titulos=["TIPO", "DATA", "LABORATORIO", "STATUS", "RESULTADO"],
              vazio="Nenhum exame registrado.")
    ui.secao("Carteira de vacinacao")
    ui.tabela(repo.carteira_vacinacao(CONEXAO, id_usuario),
              vazio="Nenhuma dose registrada.")


@ui.submenu
def menu_usuarios():
    ui.executar_menu(CABECALHO, [
        ("Listar usuarios", usuarios_listar),
        ("Cadastrar usuario", usuarios_cadastrar),
        ("Buscar por nome/CPF", usuarios_buscar),
        ("Atualizar contato", usuarios_atualizar_contato),
        ("Corrigir tipo sanguineo / RH", usuarios_atualizar_sangue),
        ("Ficha de saude completa", usuarios_ficha_completa),
    ], subtitulo="1. Usuarios")


# ---------------------------------------------------------------------------
# 2. ALERGIAS
# ---------------------------------------------------------------------------
def alergias_catalogo():
    ui.secao("Catalogo de alergias")
    ui.tabela(repo.listar_catalogo_alergias(CONEXAO),
              titulos=["ID", "ALERGIA", "CATEGORIA", "USUARIOS"])


def alergias_cadastrar_catalogo():
    ui.secao("Nova alergia no catalogo (INSERT)")
    nome = ui.ler_texto("Nome da alergia")
    categoria = ui.ler_opcao("Categoria",
                             ("MEDICAMENTO", "ALIMENTO", "AMBIENTAL", "OUTRO"))
    novo = repo.inserir_alergia_catalogo(CONEXAO, nome, categoria)
    ui.sucesso("Alergia cadastrada com o ID {0}.".format(novo))


def alergias_do_usuario():
    ui.secao("Alergias de um usuario")
    id_usuario = escolher_usuario()
    if id_usuario is None:
        return
    ui.tabela(repo.listar_alergias_usuario(CONEXAO, id_usuario),
              vazio="Nenhuma alergia registrada para este usuario.")


def alergias_vincular():
    ui.secao("Registrar alergia de um usuario (INSERT na tabela N:N)")
    id_usuario = escolher_usuario()
    if id_usuario is None:
        return
    print()
    id_alergia = escolher_de_tabela(repo.listar_catalogo_alergias(CONEXAO),
                                    "id_alergia", "ID da alergia",
                                    colunas=["id_alergia", "nome", "categoria"],
                                    titulos=["ID", "ALERGIA", "CATEGORIA"])
    if id_alergia is None:
        return
    gravidade = ui.ler_opcao("Gravidade", ("LEVE", "MODERADA", "GRAVE"))
    observacao = ui.ler_texto("Observacao", obrigatorio=False)
    repo.vincular_alergia(CONEXAO, id_usuario, id_alergia, gravidade, observacao)
    ui.sucesso("Alergia vinculada ao usuario.")


def alergias_atualizar_gravidade():
    ui.secao("Atualizar gravidade de uma alergia (UPDATE)")
    id_usuario = escolher_usuario()
    if id_usuario is None:
        return
    atuais = db.consultar(CONEXAO, """
        SELECT a.id_alergia, a.nome, a.categoria, ua.gravidade
          FROM usuario_alergia ua
          JOIN alergia a ON a.id_alergia = ua.id_alergia
         WHERE ua.id_usuario = ?
    """, (id_usuario,))
    print()
    id_alergia = escolher_de_tabela(atuais, "id_alergia", "ID da alergia",
                                    titulos=["ID", "ALERGIA", "CATEGORIA", "GRAVIDADE"])
    if id_alergia is None:
        return
    gravidade = ui.ler_opcao("Nova gravidade", ("LEVE", "MODERADA", "GRAVE"))
    repo.atualizar_gravidade_alergia(CONEXAO, id_usuario, id_alergia, gravidade)
    ui.sucesso("Gravidade atualizada.")


def alergias_alertas():
    ui.secao("Alertas - alergias graves e moderadas")
    ui.tabela(repo.alergias_graves(CONEXAO),
              titulos=["USUARIO", "SANGUE", "ALERGIA", "CATEGORIA", "GRAVIDADE", "OBSERVACAO"])


@ui.submenu
def menu_alergias():
    ui.executar_menu(CABECALHO, [
        ("Catalogo de alergias", alergias_catalogo),
        ("Cadastrar alergia no catalogo", alergias_cadastrar_catalogo),
        ("Alergias de um usuario", alergias_do_usuario),
        ("Registrar alergia de um usuario", alergias_vincular),
        ("Atualizar gravidade", alergias_atualizar_gravidade),
        ("Alertas (graves/moderadas)", alergias_alertas),
    ], subtitulo="2. Alergias")


# ---------------------------------------------------------------------------
# 3. CONSULTAS
# ---------------------------------------------------------------------------
def consultas_listar():
    ui.secao("Historico de consultas")
    id_usuario = escolher_usuario()
    if id_usuario is None:
        return
    ui.tabela(repo.listar_consultas_usuario(CONEXAO, id_usuario),
              colunas=["id_consulta", "data_hora", "profissional", "especialidade",
                       "motivo", "diagnostico"],
              titulos=["ID", "DATA/HORA", "PROFISSIONAL", "ESPECIALIDADE",
                       "MOTIVO", "DIAGNOSTICO"],
              vazio="Nenhuma consulta registrada.")


def consultas_registrar():
    ui.secao("Registrar consulta (INSERT)")
    id_usuario = escolher_usuario()
    if id_usuario is None:
        return
    print()
    id_profissional = escolher_de_tabela(repo.listar_profissionais(CONEXAO),
                                         "id_profissional", "ID do profissional",
                                         colunas=["id_profissional", "nome",
                                                  "especialidade", "registro"],
                                         titulos=["ID", "NOME", "ESPECIALIDADE", "REGISTRO"])
    if id_profissional is None:
        return
    dados = {
        "id_usuario": id_usuario,
        "id_profissional": id_profissional,
        "data_hora": ui.ler_data_hora("Data e hora"),
        "motivo": ui.ler_texto("Motivo"),
        "diagnostico": ui.ler_texto("Diagnostico", obrigatorio=False),
        "prescricao": ui.ler_texto("Prescricao", obrigatorio=False),
    }
    novo = repo.inserir_consulta(CONEXAO, dados)
    ui.sucesso("Consulta registrada com o ID {0}.".format(novo))


def consultas_atualizar():
    ui.secao("Atualizar diagnostico/prescricao (UPDATE)")
    id_usuario = escolher_usuario()
    if id_usuario is None:
        return
    consultas = repo.listar_consultas_usuario(CONEXAO, id_usuario)
    print()
    id_consulta = escolher_de_tabela(consultas, "id_consulta", "ID da consulta",
                                     colunas=["id_consulta", "data_hora", "motivo",
                                              "diagnostico"],
                                     titulos=["ID", "DATA/HORA", "MOTIVO", "DIAGNOSTICO"])
    if id_consulta is None:
        return
    diagnostico = ui.ler_texto("Diagnostico")
    prescricao = ui.ler_texto("Prescricao", obrigatorio=False)
    repo.atualizar_consulta(CONEXAO, id_consulta, diagnostico, prescricao)
    ui.sucesso("Consulta atualizada.")


def profissionais_listar():
    ui.secao("Profissionais de saude")
    ui.tabela(repo.listar_profissionais(CONEXAO),
              titulos=["ID", "NOME", "ESPECIALIDADE", "REGISTRO", "CONSULTAS"])


def profissionais_cadastrar():
    ui.secao("Cadastrar profissional (INSERT)")
    nome = ui.ler_texto("Nome")
    especialidade = ui.ler_texto("Especialidade")
    registro = ui.ler_texto("Registro (CRM/COREN)")
    novo = repo.inserir_profissional(CONEXAO, nome, especialidade, registro)
    ui.sucesso("Profissional cadastrado com o ID {0}.".format(novo))


@ui.submenu
def menu_consultas():
    ui.executar_menu(CABECALHO, [
        ("Historico de consultas de um usuario", consultas_listar),
        ("Registrar consulta", consultas_registrar),
        ("Atualizar diagnostico/prescricao", consultas_atualizar),
        ("Listar profissionais", profissionais_listar),
        ("Cadastrar profissional", profissionais_cadastrar),
    ], subtitulo="3. Consultas")


# ---------------------------------------------------------------------------
# 4. EXAMES
# ---------------------------------------------------------------------------
def exames_listar():
    ui.secao("Exames de um usuario")
    id_usuario = escolher_usuario()
    if id_usuario is None:
        return
    ui.tabela(repo.listar_exames_usuario(CONEXAO, id_usuario),
              colunas=["id_exame", "tipo", "data_realizacao", "laboratorio",
                       "status", "resultado"],
              titulos=["ID", "TIPO", "DATA", "LABORATORIO", "STATUS", "RESULTADO"],
              vazio="Nenhum exame registrado.")


def exames_registrar():
    ui.secao("Registrar exame (INSERT)")
    id_usuario = escolher_usuario()
    if id_usuario is None:
        return
    id_consulta = None
    consultas = repo.listar_consultas_usuario(CONEXAO, id_usuario)
    if consultas and ui.confirmar("Vincular a uma consulta?"):
        print()
        id_consulta = escolher_de_tabela(consultas, "id_consulta", "ID da consulta",
                                         colunas=["id_consulta", "data_hora", "motivo"],
                                         titulos=["ID", "DATA/HORA", "MOTIVO"])
    dados = {
        "id_usuario": id_usuario,
        "id_consulta": id_consulta,
        "tipo": ui.ler_texto("Tipo de exame"),
        "data_realizacao": ui.ler_data("Data de realizacao"),
        "laboratorio": ui.ler_texto("Laboratorio", obrigatorio=False),
        "resultado": ui.ler_texto("Resultado", obrigatorio=False),
        "status": ui.ler_opcao("Status", ("PENDENTE", "CONCLUIDO", "CANCELADO"),
                               padrao="PENDENTE"),
    }
    novo = repo.inserir_exame(CONEXAO, dados)
    ui.sucesso("Exame registrado com o ID {0}.".format(novo))


def exames_lancar_resultado():
    ui.secao("Lancar resultado de exame pendente (UPDATE)")
    pendentes = repo.exames_pendentes(CONEXAO)
    id_exame = escolher_de_tabela(pendentes, "id_exame", "ID do exame",
                                  titulos=["ID", "USUARIO", "TIPO", "DATA",
                                           "LABORATORIO", "CONSULTA DE ORIGEM"])
    if id_exame is None:
        return
    resultado = ui.ler_texto("Resultado")
    repo.lancar_resultado_exame(CONEXAO, id_exame, resultado)
    ui.sucesso("Resultado lancado e exame marcado como CONCLUIDO.")


def exames_pendentes_listar():
    ui.secao("Exames pendentes (todos os usuarios)")
    ui.tabela(repo.exames_pendentes(CONEXAO),
              titulos=["ID", "USUARIO", "TIPO", "DATA", "LABORATORIO", "CONSULTA DE ORIGEM"],
              vazio="Nenhum exame pendente.")


@ui.submenu
def menu_exames():
    ui.executar_menu(CABECALHO, [
        ("Exames de um usuario", exames_listar),
        ("Registrar exame", exames_registrar),
        ("Lancar resultado (exame pendente)", exames_lancar_resultado),
        ("Exames pendentes", exames_pendentes_listar),
    ], subtitulo="4. Exames")


# ---------------------------------------------------------------------------
# 5. VACINAS
# ---------------------------------------------------------------------------
def vacinas_catalogo():
    ui.secao("Catalogo de vacinas")
    ui.tabela(repo.listar_catalogo_vacinas(CONEXAO),
              titulos=["ID", "VACINA", "DOSES RECOMENDADAS", "FABRICANTE"])


def vacinas_carteira():
    ui.secao("Carteira de vacinacao")
    id_usuario = escolher_usuario()
    if id_usuario is None:
        return
    ui.tabela(repo.carteira_vacinacao(CONEXAO, id_usuario),
              vazio="Nenhuma dose registrada.")
    ui.secao("Doses em aberto")
    ui.tabela(repo.doses_pendentes(CONEXAO, id_usuario),
              vazio="Nenhuma dose em aberto para as vacinas iniciadas.")


def vacinas_registrar():
    ui.secao("Registrar aplicacao de dose (INSERT)")
    id_usuario = escolher_usuario()
    if id_usuario is None:
        return
    print()
    id_vacina = escolher_de_tabela(repo.listar_catalogo_vacinas(CONEXAO),
                                   "id_vacina", "ID da vacina",
                                   titulos=["ID", "VACINA", "DOSES", "FABRICANTE"])
    if id_vacina is None:
        return
    dados = {
        "id_usuario": id_usuario,
        "id_vacina": id_vacina,
        "dose": ui.ler_inteiro("Numero da dose", minimo=1, padrao=1),
        "data_aplicacao": ui.ler_data("Data de aplicacao"),
        "lote": ui.ler_texto("Lote", obrigatorio=False),
        "local_aplicacao": ui.ler_texto("Local de aplicacao", obrigatorio=False),
    }
    novo = repo.inserir_vacinacao(CONEXAO, dados)
    ui.sucesso("Dose registrada com o ID {0}.".format(novo))


def vacinas_pendentes():
    ui.secao("Esquemas vacinais incompletos (todos os usuarios)")
    ui.tabela(repo.doses_pendentes(CONEXAO),
              titulos=["USUARIO", "VACINA", "APLICADAS", "RECOMENDADAS",
                       "FALTAM", "ULTIMA DOSE"],
              vazio="Nenhum esquema incompleto.")


@ui.submenu
def menu_vacinas():
    ui.executar_menu(CABECALHO, [
        ("Catalogo de vacinas", vacinas_catalogo),
        ("Carteira de vacinacao de um usuario", vacinas_carteira),
        ("Registrar aplicacao de dose", vacinas_registrar),
        ("Esquemas vacinais incompletos", vacinas_pendentes),
    ], subtitulo="5. Vacinas")


# ---------------------------------------------------------------------------
# 6. RELATORIOS
# ---------------------------------------------------------------------------
def relatorio_resumo():
    ui.secao("Resumo geral do banco")
    resumo = repo.resumo_geral(CONEXAO)
    print("\n  Usuarios cadastrados...: {0}".format(resumo["usuarios"]))
    print("  Consultas registradas..: {0}".format(resumo["consultas"]))
    print("  Exames registrados.....: {0} (pendentes: {1})".format(
        resumo["exames"], resumo["exames_pendentes"]))
    print("  Doses de vacina........: {0}".format(resumo["doses_aplicadas"]))
    print("  Alergias registradas...: {0}".format(resumo["alergias_registradas"]))


def relatorio_sangue():
    ui.secao("Distribuicao por tipo sanguineo")
    ui.tabela(repo.distribuicao_sanguinea(CONEXAO), titulos=["SANGUE", "USUARIOS"])


def relatorio_especialidades():
    ui.secao("Consultas por especialidade")
    ui.tabela(repo.consultas_por_especialidade(CONEXAO),
              titulos=["ESPECIALIDADE", "TOTAL", "PRIMEIRA", "ULTIMA"])


def relatorio_linha_do_tempo():
    ui.secao("Linha do tempo de saude (consultas + exames + vacinas)")
    id_usuario = escolher_usuario()
    if id_usuario is None:
        return
    ui.tabela(repo.linha_do_tempo(CONEXAO, id_usuario),
              titulos=["DATA", "EVENTO", "DESCRICAO", "DETALHE"],
              vazio="Nenhum evento registrado.")


@ui.submenu
def menu_relatorios():
    ui.executar_menu(CABECALHO, [
        ("Resumo geral", relatorio_resumo),
        ("Distribuicao por tipo sanguineo", relatorio_sangue),
        ("Consultas por especialidade", relatorio_especialidades),
        ("Linha do tempo de um usuario", relatorio_linha_do_tempo),
        ("Alergias graves/moderadas", alergias_alertas),
        ("Exames pendentes", exames_pendentes_listar),
        ("Esquemas vacinais incompletos", vacinas_pendentes),
    ], subtitulo="6. Relatorios e consultas")


# ---------------------------------------------------------------------------
# 7. MANUTENCAO
# ---------------------------------------------------------------------------
def banco_recriar():
    global CONEXAO
    ui.secao("Recriar banco de dados")
    print("\n  Esta operacao apaga {0}".format(db.caminho_banco(repo.NOME_BANCO)))
    print("  e executa novamente o script bdDiarioPessoal.sql.")
    if not ui.confirmar("\n  Confirmar"):
        ui.aviso("Operacao cancelada.")
        return
    CONEXAO.close()
    CONEXAO = db.recriar(repo.NOME_BANCO)
    ui.sucesso("Banco recriado com os dados ficticios originais.")


def banco_informacoes():
    ui.secao("Informacoes do banco")
    print("\n  SGBD...........: SQLite 3")
    print("  Arquivo........: {0}".format(db.caminho_banco(repo.NOME_BANCO)))
    print("  Script DDL/DML.: {0}".format(db.caminho_script(repo.NOME_BANCO)))
    ui.secao("Tabelas")
    ui.tabela(db.consultar(CONEXAO, """
        SELECT name AS tabela,
               (SELECT COUNT(*) FROM pragma_table_info(name)) AS colunas
          FROM sqlite_master
         WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
         ORDER BY name
    """), titulos=["TABELA", "COLUNAS"])


@ui.submenu
def menu_manutencao():
    ui.executar_menu(CABECALHO, [
        ("Informacoes do banco", banco_informacoes),
        ("Recriar banco (volta aos dados originais)", banco_recriar),
    ], subtitulo="7. Manutencao")


# ---------------------------------------------------------------------------
# MENU PRINCIPAL
# ---------------------------------------------------------------------------
def principal():
    global CONEXAO
    CONEXAO = repo.conectar()
    try:
        ui.executar_menu(CABECALHO, [
            ("Usuarios", menu_usuarios),
            ("Alergias", menu_alergias),
            ("Consultas", menu_consultas),
            ("Exames", menu_exames),
            ("Vacinas", menu_vacinas),
            ("Relatorios e consultas", menu_relatorios),
            ("Manutencao do banco", menu_manutencao),
        ], subtitulo="Sistema 1 - SQLite", rotulo_saida="Sair")
    finally:
        if CONEXAO is not None:
            CONEXAO.close()
    print("\n  Encerrado.\n")


if __name__ == "__main__":
    principal()
