# -*- coding: utf-8 -*-
"""CENTRAL HOSPITALAR DE TRANSPLANTES - menus interativos de terminal.

Execucao:
    python3 CentralHospitalar/CentralHospitalar.py
"""

import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import db, ui
from CentralHospitalar import repositorio as repo

CABECALHO = "CENTRAL HOSPITALAR DE TRANSPLANTES"
STATUS_ORGAO = ("DISPONIVEL", "RESERVADO", "TRANSPLANTADO", "DESCARTADO")
PRIORIDADES = ("EMERGENCIA", "ALTA", "NORMAL")

CONEXAO = None


def hoje():
    return datetime.date.today().isoformat()


# ---------------------------------------------------------------------------
# Selecao de registros
# ---------------------------------------------------------------------------
def escolher(linhas, coluna_id, rotulo, colunas=None, titulos=None,
             vazio="Nenhum registro encontrado."):
    ui.tabela(linhas, colunas=colunas, titulos=titulos, vazio=vazio)
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


def escolher_hospital():
    return escolher(repo.listar_hospitais(CONEXAO), "id_hospital",
                    "ID do hospital", titulos=["ID", "HOSPITAL", "CIDADE", "UF", "CNES"])


def escolher_tipo_orgao():
    return escolher(repo.listar_tipos_orgao(CONEXAO), "id_tipo_orgao",
                    "ID do tipo de orgao",
                    colunas=["id_tipo_orgao", "nome", "tempo_isquemia_horas",
                             "disponiveis", "na_fila"],
                    titulos=["ID", "ORGAO", "ISQUEMIA (H)", "DISPONIVEIS", "NA FILA"])


# ---------------------------------------------------------------------------
# 1. DOADORES
# ---------------------------------------------------------------------------
def doadores_listar():
    ui.secao("Doadores cadastrados")
    ui.tabela(repo.listar_doadores(CONEXAO),
              titulos=["ID", "NOME", "SANGUE", "TIPO", "HOSPITAL", "REGISTRO", "ORGAOS"])


def doadores_cadastrar():
    ui.secao("Cadastro de doador (INSERT)")
    nome = ui.ler_texto("Nome completo")
    cpf = ui.ler_texto("CPF")
    nascimento = ui.ler_data("Data de nascimento")
    tipo_sanguineo = ui.ler_opcao("Tipo sanguineo", ui.TIPOS_SANGUINEOS)
    fator_rh = ui.ler_opcao("Fator RH", ui.FATORES_RH)
    tipo_doador = ui.ler_opcao("Tipo de doador", ("VIVO", "FALECIDO"))
    print()
    id_hospital = escolher_hospital()
    if id_hospital is None:
        return
    novo = repo.inserir_doador(CONEXAO, {
        "nome": nome, "cpf": cpf, "data_nascimento": nascimento,
        "tipo_sanguineo": tipo_sanguineo, "fator_rh": fator_rh,
        "tipo_doador": tipo_doador, "id_hospital": id_hospital,
        "data_registro": hoje(),
    })
    ui.sucesso("Doador cadastrado com o ID {0}.".format(novo))


@ui.submenu
def menu_doadores():
    ui.executar_menu(CABECALHO, [
        ("Listar doadores", doadores_listar),
        ("Cadastrar doador", doadores_cadastrar),
    ], subtitulo="1. Doadores")


# ---------------------------------------------------------------------------
# 2. RECEPTORES
# ---------------------------------------------------------------------------
def receptores_listar():
    ui.secao("Receptores cadastrados")
    ui.tabela(repo.listar_receptores(CONEXAO),
              titulos=["ID", "NOME", "SANGUE", "HOSPITAL", "CONTATO", "FILAS ATIVAS"])


def receptores_cadastrar():
    ui.secao("Cadastro de receptor (INSERT)")
    nome = ui.ler_texto("Nome completo")
    cpf = ui.ler_texto("CPF")
    nascimento = ui.ler_data("Data de nascimento")
    tipo_sanguineo = ui.ler_opcao("Tipo sanguineo", ui.TIPOS_SANGUINEOS)
    fator_rh = ui.ler_opcao("Fator RH", ui.FATORES_RH)
    contato = ui.ler_texto("Contato", obrigatorio=False)
    print()
    id_hospital = escolher_hospital()
    if id_hospital is None:
        return
    novo = repo.inserir_receptor(CONEXAO, {
        "nome": nome, "cpf": cpf, "data_nascimento": nascimento,
        "tipo_sanguineo": tipo_sanguineo, "fator_rh": fator_rh,
        "id_hospital": id_hospital, "contato": contato,
    })
    ui.sucesso("Receptor cadastrado com o ID {0}.".format(novo))
    if ui.confirmar("Inserir o receptor em uma fila de espera agora?"):
        fila_inserir(id_receptor=novo)


def receptores_atualizar_contato():
    ui.secao("Atualizar contato do receptor (UPDATE)")
    id_receptor = escolher(repo.listar_receptores(CONEXAO), "id_receptor",
                           "ID do receptor",
                           colunas=["id_receptor", "nome", "sangue", "contato"],
                           titulos=["ID", "NOME", "SANGUE", "CONTATO"])
    if id_receptor is None:
        return
    contato = ui.ler_texto("Novo contato")
    repo.atualizar_contato_receptor(CONEXAO, id_receptor, contato)
    ui.sucesso("Contato atualizado.")


@ui.submenu
def menu_receptores():
    ui.executar_menu(CABECALHO, [
        ("Listar receptores", receptores_listar),
        ("Cadastrar receptor", receptores_cadastrar),
        ("Atualizar contato", receptores_atualizar_contato),
    ], subtitulo="2. Receptores")


# ---------------------------------------------------------------------------
# 3. ORGAOS
# ---------------------------------------------------------------------------
COLUNAS_ORGAO = ["id_orgao", "orgao", "doador", "sangue", "status",
                 "data_captacao", "horas_desde_captacao", "isquemia_h", "hospital"]
TITULOS_ORGAO = ["ID", "ORGAO", "DOADOR", "SANGUE", "STATUS", "CAPTACAO",
                 "H. DECORRIDAS", "ISQUEMIA", "HOSPITAL"]


def orgaos_disponiveis():
    ui.secao("Orgaos disponiveis")
    ui.tabela(repo.listar_orgaos(CONEXAO, status="DISPONIVEL"),
              colunas=COLUNAS_ORGAO, titulos=TITULOS_ORGAO,
              vazio="Nenhum orgao disponivel.")


def orgaos_todos():
    ui.secao("Todos os orgaos captados")
    ui.tabela(repo.listar_orgaos(CONEXAO),
              colunas=COLUNAS_ORGAO, titulos=TITULOS_ORGAO)


def orgaos_registrar():
    ui.secao("Registrar orgao captado (INSERT)")
    id_doador = escolher(repo.listar_doadores(CONEXAO), "id_doador", "ID do doador",
                         colunas=["id_doador", "nome", "sangue", "tipo_doador", "hospital"],
                         titulos=["ID", "DOADOR", "SANGUE", "TIPO", "HOSPITAL"])
    if id_doador is None:
        return
    print()
    id_tipo_orgao = escolher_tipo_orgao()
    if id_tipo_orgao is None:
        return
    print()
    id_hospital = escolher_hospital()
    if id_hospital is None:
        return
    novo = repo.inserir_orgao(CONEXAO, {
        "id_doador": id_doador,
        "id_tipo_orgao": id_tipo_orgao,
        "id_hospital": id_hospital,
        "data_captacao": ui.ler_data_hora("Data/hora da captacao"),
        "status": ui.ler_opcao("Status", STATUS_ORGAO, padrao="DISPONIVEL"),
        "observacao": ui.ler_texto("Observacao", obrigatorio=False),
    })
    ui.sucesso("Orgao registrado com o ID {0}.".format(novo))


def orgaos_atualizar_status():
    ui.secao("Atualizar status de um orgao (UPDATE)")
    id_orgao = escolher(repo.listar_orgaos(CONEXAO), "id_orgao", "ID do orgao",
                        colunas=["id_orgao", "orgao", "doador", "sangue", "status"],
                        titulos=["ID", "ORGAO", "DOADOR", "SANGUE", "STATUS"])
    if id_orgao is None:
        return
    status = ui.ler_opcao("Novo status", STATUS_ORGAO)
    repo.atualizar_status_orgao(CONEXAO, id_orgao, status)
    ui.sucesso("Status alterado para {0}.".format(status))


def orgaos_tipos():
    ui.secao("Tipos de orgao - disponibilidade x demanda")
    ui.tabela(repo.listar_tipos_orgao(CONEXAO),
              titulos=["ID", "ORGAO", "ISQUEMIA (H)", "DISPONIVEIS", "NA FILA"])


@ui.submenu
def menu_orgaos():
    ui.executar_menu(CABECALHO, [
        ("Orgaos disponiveis", orgaos_disponiveis),
        ("Todos os orgaos captados", orgaos_todos),
        ("Registrar orgao captado", orgaos_registrar),
        ("Atualizar status do orgao", orgaos_atualizar_status),
        ("Tipos de orgao (oferta x demanda)", orgaos_tipos),
    ], subtitulo="3. Orgaos")


# ---------------------------------------------------------------------------
# 4. FILA DE ESPERA
# ---------------------------------------------------------------------------
TITULOS_FILA = ["ID", "RECEPTOR", "SANGUE", "ORGAO", "PRIORIDADE",
                "ENTRADA", "DIAS", "STATUS", "HOSPITAL"]


def fila_listar():
    ui.secao("Fila de espera - aguardando (ordem de prioridade)")
    ui.tabela(repo.listar_fila(CONEXAO, status="AGUARDANDO"),
              titulos=TITULOS_FILA, vazio="Fila vazia.")


def fila_listar_tudo():
    ui.secao("Fila de espera - historico completo")
    ui.tabela(repo.listar_fila(CONEXAO, status=None), titulos=TITULOS_FILA)


def fila_por_orgao():
    ui.secao("Fila de um tipo de orgao")
    id_tipo_orgao = escolher_tipo_orgao()
    if id_tipo_orgao is None:
        return
    ui.tabela(repo.listar_fila(CONEXAO, status="AGUARDANDO",
                               id_tipo_orgao=id_tipo_orgao),
              titulos=TITULOS_FILA, vazio="Nenhum receptor aguardando este orgao.")


def fila_inserir(id_receptor=None):
    ui.secao("Inserir receptor na fila de espera (INSERT)")
    if id_receptor is None:
        id_receptor = escolher(repo.listar_receptores(CONEXAO), "id_receptor",
                               "ID do receptor",
                               colunas=["id_receptor", "nome", "sangue", "hospital",
                                        "filas_ativas"],
                               titulos=["ID", "NOME", "SANGUE", "HOSPITAL", "FILAS"])
        if id_receptor is None:
            return
    print()
    id_tipo_orgao = escolher_tipo_orgao()
    if id_tipo_orgao is None:
        return
    novo = repo.inserir_na_fila(CONEXAO, {
        "id_receptor": id_receptor,
        "id_tipo_orgao": id_tipo_orgao,
        "prioridade": ui.ler_opcao("Prioridade", PRIORIDADES, padrao="NORMAL"),
        "data_entrada": ui.ler_data("Data de entrada", padrao=hoje()),
    })
    ui.sucesso("Receptor inserido na fila (ID {0}).".format(novo))


def fila_atualizar_prioridade():
    ui.secao("Alterar prioridade na fila (UPDATE)")
    id_fila = escolher(repo.listar_fila(CONEXAO, status="AGUARDANDO"), "id_fila",
                       "ID da fila",
                       colunas=["id_fila", "receptor", "orgao", "prioridade", "dias_na_fila"],
                       titulos=["ID", "RECEPTOR", "ORGAO", "PRIORIDADE", "DIAS"])
    if id_fila is None:
        return
    prioridade = ui.ler_opcao("Nova prioridade", PRIORIDADES)
    repo.atualizar_prioridade(CONEXAO, id_fila, prioridade)
    ui.sucesso("Prioridade alterada para {0}.".format(prioridade))


def fila_atualizar_status():
    ui.secao("Alterar situacao na fila (UPDATE)")
    id_fila = escolher(repo.listar_fila(CONEXAO, status=None), "id_fila", "ID da fila",
                       colunas=["id_fila", "receptor", "orgao", "prioridade", "status"],
                       titulos=["ID", "RECEPTOR", "ORGAO", "PRIORIDADE", "STATUS"])
    if id_fila is None:
        return
    status = ui.ler_opcao("Nova situacao",
                          ("AGUARDANDO", "TRANSPLANTADO", "SUSPENSO", "OBITO"))
    repo.atualizar_status_fila(CONEXAO, id_fila, status)
    ui.sucesso("Situacao alterada para {0}.".format(status))


@ui.submenu
def menu_fila():
    ui.executar_menu(CABECALHO, [
        ("Fila aguardando (por prioridade)", fila_listar),
        ("Fila de um tipo de orgao", fila_por_orgao),
        ("Historico completo da fila", fila_listar_tudo),
        ("Inserir receptor na fila", fila_inserir),
        ("Alterar prioridade", fila_atualizar_prioridade),
        ("Alterar situacao", fila_atualizar_status),
    ], subtitulo="4. Fila de espera")


# ---------------------------------------------------------------------------
# 5. COMPATIBILIDADE
# ---------------------------------------------------------------------------
def compat_todas():
    ui.secao("Cruzamentos compativeis (orgao disponivel x fila)")
    print("  Criterio: mesmo tipo de orgao + ABO compativel + RH compativel")
    ui.tabela(repo.compatibilidade_geral(CONEXAO),
              colunas=["id_orgao", "orgao", "sangue_doador", "receptor",
                       "sangue_receptor", "prioridade", "dias_na_fila",
                       "hospital_receptor"],
              titulos=["ORGAO ID", "ORGAO", "SANGUE DOADOR", "RECEPTOR",
                       "SANGUE RECEPTOR", "PRIORIDADE", "DIAS", "HOSPITAL"],
              vazio="Nenhum cruzamento compativel no momento.")


def compat_por_orgao():
    ui.secao("Buscar receptores compativeis com um orgao")
    id_orgao = escolher(repo.listar_orgaos(CONEXAO, status="DISPONIVEL"),
                        "id_orgao", "ID do orgao",
                        colunas=["id_orgao", "orgao", "doador", "sangue", "hospital"],
                        titulos=["ID", "ORGAO", "DOADOR", "SANGUE", "HOSPITAL"],
                        vazio="Nenhum orgao disponivel.")
    if id_orgao is None:
        return
    orgao = repo.buscar_orgao(CONEXAO, id_orgao)
    ui.secao("Candidatos para {0} do doador {1} ({2})".format(
        orgao["orgao"], orgao["doador"], orgao["sangue"]))
    candidatos = repo.compativeis_para_orgao(CONEXAO, id_orgao)
    ui.tabela(candidatos,
              colunas=["id_fila", "receptor", "sangue_receptor", "prioridade",
                       "data_entrada", "dias_na_fila", "hospital_receptor"],
              titulos=["FILA", "RECEPTOR", "SANGUE", "PRIORIDADE", "ENTRADA",
                       "DIAS", "HOSPITAL"],
              vazio="Nenhum receptor compativel aguardando este orgao.")
    if candidatos:
        primeiro = candidatos[0]
        print("\n  >> Proximo da lista: {0} ({1}, {2}, {3} dias de espera)".format(
            primeiro["receptor"], primeiro["sangue_receptor"],
            primeiro["prioridade"], primeiro["dias_na_fila"]))


def compat_resumo():
    ui.secao("Candidatos compativeis por orgao disponivel")
    ui.tabela(repo.candidatos_por_orgao(CONEXAO),
              titulos=["ID", "ORGAO", "SANGUE DOADOR", "CAPTACAO", "HOSPITAL", "CANDIDATOS"],
              vazio="Nenhum orgao disponivel.")


def compat_sem_doador():
    ui.secao("Receptores sem orgao compativel disponivel hoje")
    ui.tabela(repo.sem_compatibilidade(CONEXAO),
              titulos=["RECEPTOR", "SANGUE", "ORGAO", "PRIORIDADE", "DIAS", "HOSPITAL"],
              vazio="Todos os receptores da fila possuem alguma opcao compativel.")


def compat_regras():
    ui.secao("Tabela de compatibilidade sanguinea (doador -> receptor)")
    regras = repo.regras_compatibilidade(CONEXAO)
    por_doador = {}
    for regra in regras:
        por_doador.setdefault(regra["doador"], []).append(regra["receptor"])
    print()
    for doador in sorted(por_doador):
        print("   Doador {0:>3}  ->  pode doar para: {1}".format(
            doador, ", ".join(sorted(por_doador[doador]))))
    print("\n  Regra ABO: O doa para todos | A -> A/AB | B -> B/AB | AB -> AB")
    print("  Regra RH : negativo doa para ambos | positivo somente para positivo")


@ui.submenu
def menu_compatibilidade():
    ui.executar_menu(CABECALHO, [
        ("Buscar receptores compativeis com um orgao", compat_por_orgao),
        ("Todos os cruzamentos compativeis", compat_todas),
        ("Resumo de candidatos por orgao", compat_resumo),
        ("Receptores sem opcao compativel", compat_sem_doador),
        ("Tabela de regras de compatibilidade", compat_regras),
    ], subtitulo="5. Compatibilidade")


# ---------------------------------------------------------------------------
# 6. TRANSPLANTES
# ---------------------------------------------------------------------------
def transplantes_listar():
    ui.secao("Transplantes realizados")
    ui.tabela(repo.listar_transplantes(CONEXAO),
              titulos=["ID", "ORGAO", "DOADOR", "RECEPTOR", "CIRURGIA",
                       "CIRURGIAO", "RESULTADO", "HOSPITAL"],
              vazio="Nenhum transplante registrado.")


def transplantes_efetivar():
    ui.secao("Efetivar transplante (INSERT + 2 UPDATEs em transacao)")
    id_orgao = escolher(repo.listar_orgaos(CONEXAO, status="DISPONIVEL"),
                        "id_orgao", "ID do orgao",
                        colunas=["id_orgao", "orgao", "doador", "sangue", "hospital"],
                        titulos=["ID", "ORGAO", "DOADOR", "SANGUE", "HOSPITAL"],
                        vazio="Nenhum orgao disponivel.")
    if id_orgao is None:
        return
    candidatos = repo.compativeis_para_orgao(CONEXAO, id_orgao)
    ui.secao("Receptores compativeis (em ordem de alocacao)")
    id_fila = escolher(candidatos, "id_fila", "ID da fila do receptor escolhido",
                       colunas=["id_fila", "receptor", "sangue_receptor",
                                "prioridade", "dias_na_fila", "hospital_receptor"],
                       titulos=["FILA", "RECEPTOR", "SANGUE", "PRIORIDADE",
                                "DIAS", "HOSPITAL"],
                       vazio="Nenhum receptor compativel para este orgao.")
    if id_fila is None:
        return
    item = repo.buscar_item_fila(CONEXAO, id_fila)
    print()
    id_hospital = escolher_hospital()
    if id_hospital is None:
        return
    dados = {
        "id_orgao": id_orgao,
        "id_receptor": item["id_receptor"],
        "id_hospital": id_hospital,
        "data_cirurgia": ui.ler_data_hora("Data/hora da cirurgia"),
        "cirurgiao": ui.ler_texto("Cirurgiao responsavel", obrigatorio=False),
    }
    if not ui.confirmar("Confirmar o transplante para {0}".format(item["receptor"])):
        ui.aviso("Operacao cancelada.")
        return
    novo = repo.registrar_transplante(CONEXAO, id_orgao, id_fila, dados)
    ui.sucesso("Transplante {0} registrado. Orgao e fila atualizados.".format(novo))


def transplantes_atualizar_resultado():
    ui.secao("Atualizar desfecho do transplante (UPDATE)")
    id_transplante = escolher(repo.listar_transplantes(CONEXAO), "id_transplante",
                              "ID do transplante",
                              colunas=["id_transplante", "orgao", "receptor",
                                       "data_cirurgia", "resultado"],
                              titulos=["ID", "ORGAO", "RECEPTOR", "CIRURGIA", "RESULTADO"])
    if id_transplante is None:
        return
    resultado = ui.ler_opcao("Novo resultado",
                             ("SUCESSO", "REJEICAO", "OBITO", "EM_ACOMPANHAMENTO"))
    repo.atualizar_resultado_transplante(CONEXAO, id_transplante, resultado)
    ui.sucesso("Resultado atualizado para {0}.".format(resultado))


@ui.submenu
def menu_transplantes():
    ui.executar_menu(CABECALHO, [
        ("Transplantes realizados", transplantes_listar),
        ("Efetivar transplante", transplantes_efetivar),
        ("Atualizar desfecho", transplantes_atualizar_resultado),
    ], subtitulo="6. Transplantes")


# ---------------------------------------------------------------------------
# 7. PAINEL E RELATORIOS
# ---------------------------------------------------------------------------
def painel_indicadores():
    ui.secao("Painel da central")
    dados = repo.painel(CONEXAO)
    print("\n  Doadores cadastrados........: {0}".format(dados["doadores"]))
    print("  Receptores cadastrados......: {0}".format(dados["receptores"]))
    print("  Orgaos disponiveis..........: {0}".format(dados["orgaos_disponiveis"]))
    print("  Orgaos reservados...........: {0}".format(dados["orgaos_reservados"]))
    print("  Receptores aguardando.......: {0} (emergencias: {1})".format(
        dados["na_fila"], dados["emergencias"]))
    print("  Transplantes realizados.....: {0}".format(dados["transplantes"]))
    print("  Cruzamentos compativeis.....: {0}".format(dados["cruzamentos_compativeis"]))


def relatorio_fila_por_orgao():
    ui.secao("Demanda da fila por tipo de orgao")
    ui.tabela(repo.fila_por_orgao(CONEXAO),
              titulos=["ORGAO", "AGUARDANDO", "EMERGENCIAS", "MEDIA DE DIAS", "DISPONIVEIS"])


def relatorio_hospitais():
    ui.secao("Transplantes por hospital")
    ui.tabela(repo.transplantes_por_hospital(CONEXAO),
              titulos=["HOSPITAL", "TRANSPLANTES", "SUCESSOS"])


@ui.submenu
def menu_relatorios():
    ui.executar_menu(CABECALHO, [
        ("Painel de indicadores", painel_indicadores),
        ("Demanda por tipo de orgao", relatorio_fila_por_orgao),
        ("Transplantes por hospital", relatorio_hospitais),
        ("Candidatos compativeis por orgao", compat_resumo),
        ("Receptores sem opcao compativel", compat_sem_doador),
    ], subtitulo="7. Relatorios")


# ---------------------------------------------------------------------------
# 8. MANUTENCAO
# ---------------------------------------------------------------------------
def banco_informacoes():
    ui.secao("Informacoes do banco")
    print("\n  SGBD...........: SQLite 3")
    print("  Arquivo........: {0}".format(db.caminho_banco(repo.NOME_BANCO)))
    print("  Script DDL/DML.: {0}".format(db.caminho_script(repo.NOME_BANCO)))
    ui.secao("Tabelas e views")
    ui.tabela(db.consultar(CONEXAO, """
        SELECT name AS objeto, type AS tipo
          FROM sqlite_master
         WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%'
         ORDER BY type, name
    """), titulos=["OBJETO", "TIPO"])


def banco_recriar():
    global CONEXAO
    ui.secao("Recriar banco de dados")
    print("\n  Esta operacao apaga {0}".format(db.caminho_banco(repo.NOME_BANCO)))
    print("  e executa novamente o script bdCentralHospitalar.sql.")
    if not ui.confirmar("\n  Confirmar"):
        ui.aviso("Operacao cancelada.")
        return
    CONEXAO.close()
    CONEXAO = db.recriar(repo.NOME_BANCO)
    ui.sucesso("Banco recriado com os dados ficticios originais.")


@ui.submenu
def menu_manutencao():
    ui.executar_menu(CABECALHO, [
        ("Informacoes do banco", banco_informacoes),
        ("Recriar banco (volta aos dados originais)", banco_recriar),
    ], subtitulo="8. Manutencao")


# ---------------------------------------------------------------------------
# MENU PRINCIPAL
# ---------------------------------------------------------------------------
def principal():
    global CONEXAO
    CONEXAO = repo.conectar()
    try:
        ui.executar_menu(CABECALHO, [
            ("Doadores", menu_doadores),
            ("Receptores", menu_receptores),
            ("Orgaos", menu_orgaos),
            ("Fila de espera", menu_fila),
            ("Compatibilidade doador x receptor", menu_compatibilidade),
            ("Transplantes", menu_transplantes),
            ("Painel e relatorios", menu_relatorios),
            ("Manutencao do banco", menu_manutencao),
        ], subtitulo="Sistema 2 - SQLite", rotulo_saida="Sair")
    finally:
        if CONEXAO is not None:
            CONEXAO.close()
    print("\n  Encerrado.\n")


if __name__ == "__main__":
    principal()
