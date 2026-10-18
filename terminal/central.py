# -*- coding: utf-8 -*-
"""CENTRAL HOSPITALAR DE TRANSPLANTES - menus interativos de terminal.

Toda regra fica no backend (CentralService). Doadores e receptores sao
sempre pessoas ja cadastradas no Diario de Saude: a Central le esses dados
pelo DiarioGateway e nao duplica nome, CPF nem tipagem sanguinea.
"""

from backend.central.integracao_diario import DiarioGateway
from backend.central.servico import CentralService
from backend.erros import ErroDeNegocio
from terminal import ui
from terminal.ui import agora, hoje, valor_do_campo
from terminal.enums import enums_do_banco

CABECALHO = "CENTRAL HOSPITALAR DE TRANSPLANTES"

SERVICO = None
DIARIO = None
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


def escolher_hospital():
    return escolher(SERVICO.listar_hospitais(), "id", "ID do hospital",
                    colunas=["id", "nome", "cidade", "uf"],
                    titulos=["ID", "HOSPITAL", "CIDADE", "UF"])


def escolher_tipo_orgao(apenas_doador_vivo=False):
    tipos = SERVICO.listar_tipos_orgao()
    if apenas_doador_vivo:
        tipos = [t for t in tipos if t.permite_doador_vivo]
    return escolher(tipos, "id", "ID do tipo de orgao",
                    colunas=["id", "nome", "tempo_max_isquemia_horas",
                             "permite_doador_vivo"],
                    titulos=["ID", "ORGAO", "ISQUEMIA (H)", "ACEITA DOADOR VIVO"])


def escolher_usuario_diario(rotulo="ID do usuario no Diario de Saude"):
    """Lista os usuarios do Diario de Saude (fonte de doadores e receptores)."""
    from backend.diario.servico import DiarioService
    with DiarioService() as diario:
        usuarios = [diario.ficha(u.id) for u in diario.listar_usuarios()]
    return escolher(usuarios, "id", rotulo,
                    colunas=["id", "nome", "idade", "sangue", "cidade", "uf",
                             "restricao_doacao"],
                    titulos=["ID", "NOME", "IDADE", "SANGUE", "CIDADE", "UF",
                             "RESTRICAO DOACAO"],
                    vazio="Nenhum usuario no Diario de Saude.")


# ---------------------------------------------------------------------------
# 1. DOADORES
# ---------------------------------------------------------------------------
def doadores_listar():
    ui.secao("Doadores cadastrados")
    ui.tabela(SERVICO.listar_doadores(),
              colunas=["id", "usuario_id", "nome", "tipo", "status",
                       "hospital_id", "data_cadastro", "motivo_inaptidao"],
              titulos=["ID", "USUARIO", "NOME", "TIPO", "STATUS", "HOSPITAL",
                       "CADASTRO", "MOTIVO DE INAPTIDAO"])


def doadores_cadastrar():
    ui.secao("Cadastrar doador (a partir de um usuario do Diario)")
    usuario_id = escolher_usuario_diario()
    if usuario_id is None:
        return
    tipo = ui.ler_opcao("Tipo de doador", ENUM["tipo_doador"])
    print()
    hospital_id = escolher_hospital()
    if hospital_id is None:
        return
    novo = SERVICO.cadastrar_doador(usuario_id, tipo, hospital_id)
    ui.sucesso("Doador {0} cadastrado ({1}).".format(novo.id, novo.status))
    if novo.motivo_inaptidao:
        ui.aviso("Motivo da inaptidao: {0}".format(novo.motivo_inaptidao))


def doadores_reavaliar():
    ui.secao("Reavaliar doadores com base no Diario de Saude")
    print("  Reconsulta restricoes clinicas e atualiza o status de cada doador.")
    mudancas = SERVICO.reavaliar_doadores()
    if not mudancas:
        ui.sucesso("Nenhuma mudanca: todos os status continuam corretos.")
        return
    linhas = [{"doador": d.nome or d.usuario_id, "de": antes, "para": depois}
              for d, antes, depois in mudancas]
    ui.tabela(linhas, colunas=["doador", "de", "para"],
              titulos=["DOADOR", "STATUS ANTERIOR", "NOVO STATUS"])


@ui.submenu
def menu_doadores():
    ui.executar_menu(CABECALHO, [
        ("Listar doadores", doadores_listar),
        ("Cadastrar doador", doadores_cadastrar),
        ("Reavaliar aptidao (consulta o Diario)", doadores_reavaliar),
    ], subtitulo="1. Doadores")


# ---------------------------------------------------------------------------
# 2. RECEPTORES E FILA
# ---------------------------------------------------------------------------
COLUNAS_FILA = ["orgao", "posicao", "fila_id", "nome", "sangue", "urgencia",
                "dias_espera", "hospital", "uf"]
TITULOS_FILA = ["ORGAO", "POS", "FILA", "RECEPTOR", "SANGUE", "URGENCIA",
                "DIAS", "HOSPITAL", "UF"]


def receptores_cadastrar():
    ui.secao("Cadastrar receptor (a partir de um usuario do Diario)")
    usuario_id = escolher_usuario_diario()
    if usuario_id is None:
        return
    print()
    hospital_id = escolher_hospital()
    if hospital_id is None:
        return
    novo = SERVICO.cadastrar_receptor(usuario_id, hospital_id)
    ui.sucesso("Receptor cadastrado com o ID {0}.".format(novo.id))
    if ui.confirmar("Incluir na fila de espera agora?"):
        fila_incluir(receptor_id=novo.id)


def receptores_listar():
    ui.secao("Receptores cadastrados")
    ui.tabela(SERVICO.listar_receptores(),
              colunas=["id", "usuario_id", "nome", "hospital_id", "data_cadastro"],
              titulos=["ID", "USUARIO", "NOME", "HOSPITAL", "CADASTRO"],
              vazio="Nenhum receptor cadastrado.")


def fila_listar():
    ui.secao("Fila de espera ativa (ordenada pelo backend)")
    ui.tabela(SERVICO.fila_ativa(), colunas=COLUNAS_FILA, titulos=TITULOS_FILA,
              vazio="Fila vazia.")


def fila_por_orgao():
    ui.secao("Fila de um tipo de orgao")
    tipo_orgao_id = escolher_tipo_orgao()
    if tipo_orgao_id is None:
        return
    ui.tabela(SERVICO.fila_ativa(tipo_orgao_id), colunas=COLUNAS_FILA,
              titulos=TITULOS_FILA, vazio="Ninguem aguardando este orgao.")


def fila_incluir(receptor_id=None):
    ui.secao("Incluir receptor na fila (INSERT)")
    if receptor_id is None:
        usuario_id = escolher_usuario_diario("ID do usuario (receptor) no Diario")
        if usuario_id is None:
            return
        receptor = SERVICO.buscar_receptor_por_usuario(usuario_id)
        if receptor is None:
            ui.aviso("Este usuario ainda nao e receptor. Cadastre-o primeiro.")
            return
        receptor_id = receptor.id
    print()
    tipo_orgao_id = escolher_tipo_orgao()
    if tipo_orgao_id is None:
        return
    urgencia = ui.ler_inteiro("Urgencia (1 = menor, 5 = maior)", minimo=1, maximo=5)
    nova = SERVICO.incluir_na_fila(receptor_id, tipo_orgao_id, urgencia)
    ui.sucesso("Receptor incluido na fila (ID {0}).".format(nova.id))


def fila_urgencia():
    ui.secao("Alterar urgencia na fila (UPDATE)")
    fila_id = escolher(SERVICO.fila_ativa(), "fila_id", "ID da fila",
                       colunas=COLUNAS_FILA, titulos=TITULOS_FILA)
    if fila_id is None:
        return
    urgencia = ui.ler_inteiro("Nova urgencia (1 a 5)", minimo=1, maximo=5)
    SERVICO.atualizar_urgencia(fila_id, urgencia)
    ui.sucesso("Urgencia atualizada para {0}.".format(urgencia))


def fila_remover():
    ui.secao("Remover da fila (UPDATE de status)")
    fila_id = escolher(SERVICO.fila_ativa(), "fila_id", "ID da fila",
                       colunas=COLUNAS_FILA, titulos=TITULOS_FILA)
    if fila_id is None:
        return
    if ui.confirmar("Confirmar remocao da fila"):
        SERVICO.remover_da_fila(fila_id)
        ui.sucesso("Registro removido da fila.")


@ui.submenu
def menu_fila():
    ui.executar_menu(CABECALHO, [
        ("Listar receptores", receptores_listar),
        ("Fila de espera ativa", fila_listar),
        ("Fila de um tipo de orgao", fila_por_orgao),
        ("Cadastrar receptor", receptores_cadastrar),
        ("Incluir receptor na fila", fila_incluir),
        ("Alterar urgencia", fila_urgencia),
        ("Remover da fila", fila_remover),
    ], subtitulo="2. Receptores e fila de espera")


# ---------------------------------------------------------------------------
# 3. ORGAOS
# ---------------------------------------------------------------------------
COLUNAS_ORGAO = ["orgao_id", "orgao", "doador_nome", "doador_sangue",
                 "tipo_doador", "hospital_origem", "data_hora_captacao",
                 "prazo_limite", "horas_restantes"]
TITULOS_ORGAO = ["ID", "ORGAO", "DOADOR", "SANGUE", "DOACAO", "HOSPITAL",
                 "CAPTACAO", "PRAZO", "HORAS RESTANTES"]


def orgaos_disponiveis():
    ui.secao("Orgaos disponiveis (com tempo de isquemia restante)")
    ui.tabela(SERVICO.orgaos_disponiveis(), colunas=COLUNAS_ORGAO,
              titulos=TITULOS_ORGAO, vazio="Nenhum orgao disponivel.")


def orgaos_todos():
    ui.secao("Todos os orgaos captados")
    status = ui.ler_opcao("Filtrar por status",
                          ["todos"] + list(ENUM["status_orgao"]), padrao="todos")
    linhas = SERVICO.listar_orgaos(None if status == "TODOS" else status.lower())
    ui.tabela(linhas, vazio="Nenhum orgao encontrado.")


def orgaos_registrar():
    ui.secao("Registrar orgao captado (INSERT)")
    doador_id = escolher(SERVICO.listar_doadores(), "id", "ID do doador",
                         colunas=["id", "nome", "tipo", "status", "hospital_id"],
                         titulos=["ID", "DOADOR", "TIPO", "STATUS", "HOSPITAL"])
    if doador_id is None:
        return
    print()
    tipo_orgao_id = escolher_tipo_orgao()
    if tipo_orgao_id is None:
        return
    hospital_id = None
    if ui.confirmar("O orgao esta em outro hospital?"):
        print()
        hospital_id = escolher_hospital()
    novo = SERVICO.registrar_orgao(doador_id, tipo_orgao_id, hospital_id)
    ui.sucesso("Orgao registrado com o ID {0} (status {1}).".format(
        novo.id, novo.status))


@ui.submenu
def menu_orgaos():
    ui.executar_menu(CABECALHO, [
        ("Orgaos disponiveis", orgaos_disponiveis),
        ("Todos os orgaos (por status)", orgaos_todos),
        ("Registrar orgao captado", orgaos_registrar),
        ("Tipos de orgao", lambda: ui.tabela(
            SERVICO.listar_tipos_orgao(),
            colunas=["id", "nome", "tempo_max_isquemia_horas", "permite_doador_vivo"],
            titulos=["ID", "ORGAO", "ISQUEMIA (H)", "ACEITA DOADOR VIVO"])),
    ], subtitulo="3. Orgaos")


# ---------------------------------------------------------------------------
# 4. COMPATIBILIDADE E ALOCACAO
# ---------------------------------------------------------------------------
def _mostrar_selecao(resultado):
    oferta = resultado.oferta
    ui.secao("Oferta: {0} de {1} ({2}) - {3}".format(
        oferta.tipo_orgao, oferta.doador_nome, oferta.doador_sangue, oferta.hospital))
    print("  Horas restantes de isquemia: {0}".format(oferta.horas_restantes))

    elegiveis = [c for c in resultado.candidatos if c.elegivel]
    excluidos = [c for c in resultado.candidatos if not c.elegivel]

    linhas = [{
        "posicao": c.posicao,
        "fila_id": c.pedido.fila_id,
        "receptor": c.pedido.nome,
        "sangue": c.sangue,
        "urgencia": c.pedido.urgencia,
        "dias": c.pedido.dias_espera,
        "hospital": c.pedido.hospital,
        "distancia_km": c.distancia_km,
        "modal": c.modal,
        "horas": c.tempo_transporte_h,
        "isogrupo": "sim" if c.isogrupo else "nao",
    } for c in elegiveis]
    ui.secao("Candidatos elegiveis (ordem de alocacao)")
    ui.tabela(linhas,
              colunas=["posicao", "fila_id", "receptor", "sangue", "urgencia",
                       "dias", "hospital", "distancia_km", "modal", "horas",
                       "isogrupo"],
              titulos=["POS", "FILA", "RECEPTOR", "SANGUE", "URG", "DIAS",
                       "HOSPITAL", "DIST (KM)", "MODAL", "TEMPO (H)", "ISOGRUPO"],
              vazio="Nenhum candidato elegivel para este orgao.")

    if excluidos:
        ui.secao("Descartados e o motivo")
        ui.tabela([{"receptor": c.pedido.nome, "sangue": c.sangue,
                    "urgencia": c.pedido.urgencia,
                    "motivo": c.motivo_exclusao} for c in excluidos],
                  colunas=["receptor", "sangue", "urgencia", "motivo"],
                  titulos=["RECEPTOR", "SANGUE", "URGENCIA", "MOTIVO DA EXCLUSAO"])
    return elegiveis


def compat_selecionar():
    ui.secao("Selecionar receptores compativeis com um orgao")
    print("  Criterios do backend: compatibilidade_abo + fator RH + tempo de")
    print("  isquemia restante x tempo de transporte ate o hospital do receptor.")
    orgao_id = escolher(SERVICO.orgaos_disponiveis(), "orgao_id", "ID do orgao",
                        colunas=COLUNAS_ORGAO, titulos=TITULOS_ORGAO,
                        vazio="Nenhum orgao disponivel.")
    if orgao_id is None:
        return
    resultado = SERVICO.selecionar_receptores(orgao_id)
    elegiveis = _mostrar_selecao(resultado)
    if not elegiveis:
        return
    if not ui.confirmar("\n  Alocar o orgao agora"):
        return
    fila_id = ui.ler_inteiro("  ID da fila do receptor escolhido (0 cancela)",
                             minimo=0)
    if fila_id == 0:
        return
    alocacao = SERVICO.alocar_orgao(orgao_id, fila_id)
    ui.sucesso("Alocacao {0} criada (status {1}).".format(
        alocacao.id, alocacao.status_logistica))


def compat_alocar_melhor():
    ui.secao("Alocar automaticamente para o primeiro da lista")
    orgao_id = escolher(SERVICO.orgaos_disponiveis(), "orgao_id", "ID do orgao",
                        colunas=COLUNAS_ORGAO, titulos=TITULOS_ORGAO,
                        vazio="Nenhum orgao disponivel.")
    if orgao_id is None:
        return
    resultado = SERVICO.selecionar_receptores(orgao_id)
    elegiveis = _mostrar_selecao(resultado)
    if not elegiveis:
        return
    primeiro = elegiveis[0]
    if not ui.confirmar("\n  Confirmar alocacao para {0}".format(primeiro.pedido.nome)):
        return
    alocacao = SERVICO.alocar_melhor_receptor(orgao_id)
    ui.sucesso("Alocacao {0} criada.".format(alocacao.id if alocacao else "-"))


def compat_regras():
    ui.secao("Tabela compatibilidade_abo (doador -> receptor)")
    with SERVICO.conexao.cursor() as cursor:
        cursor.execute("""
            SELECT tipo_doador::TEXT AS doador,
                   STRING_AGG(tipo_receptor::TEXT, ', ' ORDER BY tipo_receptor) AS receptores
              FROM compatibilidade_abo GROUP BY tipo_doador ORDER BY tipo_doador
        """)
        linhas = cursor.fetchall()
    ui.tabela(linhas, colunas=["doador", "receptores"],
              titulos=["DOADOR (ABO)", "PODE DOAR PARA"])
    print("\n  Fator RH: doador negativo atende ambos; positivo so atende positivo.")
    print("  Isogrupo (mesmo ABO) e preferido no desempate da fila.")


@ui.submenu
def menu_compatibilidade():
    ui.executar_menu(CABECALHO, [
        ("Selecionar receptores para um orgao", compat_selecionar),
        ("Alocar para o primeiro da lista", compat_alocar_melhor),
        ("Regras de compatibilidade (compatibilidade_abo)", compat_regras),
    ], subtitulo="4. Compatibilidade e alocacao")


# ---------------------------------------------------------------------------
# 5. PROCESSOS (LOGISTICA)
# ---------------------------------------------------------------------------
COLUNAS_PROCESSO = ["alocacao_id", "orgao", "doador_nome", "receptor_nome",
                    "hospital_origem", "hospital_destino", "distancia_km",
                    "alocado_em", "status_logistica", "status_fila"]
TITULOS_PROCESSO = ["ID", "ORGAO", "DOADOR", "RECEPTOR", "ORIGEM", "DESTINO",
                    "DIST (KM)", "ALOCADO EM", "LOGISTICA", "FILA"]


def processos_listar():
    ui.secao("Processos de transplante")
    ui.tabela(SERVICO.processos(), colunas=COLUNAS_PROCESSO,
              titulos=TITULOS_PROCESSO, vazio="Nenhum processo registrado.")


def _escolher_processo(status_esperado=None):
    processos = SERVICO.processos()
    if status_esperado:
        processos = [p for p in processos if p.status_logistica == status_esperado]
    return escolher(processos, "alocacao_id", "ID da alocacao",
                    colunas=COLUNAS_PROCESSO, titulos=TITULOS_PROCESSO,
                    vazio="Nenhum processo neste estagio.")


def processos_entregar():
    ui.secao("Registrar entrega do orgao (em_transporte -> entregue)")
    alocacao_id = _escolher_processo("em_transporte")
    if alocacao_id is None:
        return
    alocacao = SERVICO.registrar_entrega(alocacao_id)
    ui.sucesso("Entrega registrada (status {0}).".format(alocacao.status_logistica))


def processos_concluir():
    ui.secao("Concluir transplante (entregue -> realizado)")
    alocacao_id = _escolher_processo("entregue")
    if alocacao_id is None:
        return
    alocacao = SERVICO.concluir_transplante(alocacao_id)
    ui.sucesso("Transplante concluido (status {0}).".format(alocacao.status_logistica))


def processos_cancelar():
    ui.secao("Cancelar alocacao")
    alocacao_id = _escolher_processo()
    if alocacao_id is None:
        return
    if not ui.confirmar("Confirmar cancelamento"):
        return
    alocacao = SERVICO.cancelar_alocacao(alocacao_id)
    ui.sucesso("Alocacao cancelada (status {0}).".format(alocacao.status_logistica))


@ui.submenu
def menu_processos():
    ui.executar_menu(CABECALHO, [
        ("Processos em andamento", processos_listar),
        ("Registrar entrega", processos_entregar),
        ("Concluir transplante", processos_concluir),
        ("Cancelar alocacao", processos_cancelar),
    ], subtitulo="5. Processos e logistica")


# ---------------------------------------------------------------------------
# 6. BANCO DE SANGUE
# ---------------------------------------------------------------------------
def sangue_estoque():
    ui.secao("Estoque de bolsas por tipo sanguineo")
    estoque = SERVICO.estoque_sangue()
    if not estoque:
        ui.aviso("Estoque vazio.")
        return
    linhas = []
    for tipo, dados in sorted(estoque.items()):
        linha = {"sangue": tipo}
        linha.update(dados if isinstance(dados, dict) else {"bolsas": dados})
        linhas.append(linha)
    ui.tabela(linhas)


def sangue_doar():
    ui.secao("Registrar doacao de sangue (INSERT)")
    usuario_id = escolher_usuario_diario("ID do doador no Diario")
    if usuario_id is None:
        return
    print()
    hospital_id = escolher_hospital()
    if hospital_id is None:
        return
    volume = ui.ler_inteiro("Volume (mL, entre 200 e 600)", minimo=200,
                            maximo=600, padrao=450)
    bolsa = SERVICO.registrar_doacao_sangue(usuario_id, hospital_id, volume)
    ui.sucesso("Bolsa {0} registrada ({1}, valida ate {2}).".format(
        bolsa.id, bolsa.sangue, bolsa.data_validade))


def sangue_compativeis():
    ui.secao("Bolsas compativeis com um receptor")
    usuario_id = escolher_usuario_diario("ID do receptor no Diario")
    if usuario_id is None:
        return
    bolsas = SERVICO.bolsas_compativeis(usuario_id)
    ui.tabela(bolsas,
              colunas=["id", "sangue", "hospital", "volume_ml", "data_coleta",
                       "data_validade", "status"],
              titulos=["ID", "SANGUE", "HOSPITAL", "VOLUME", "COLETA",
                       "VALIDADE", "STATUS"],
              vazio="Nenhuma bolsa compativel disponivel.")
    if not bolsas:
        return
    if not ui.confirmar("Utilizar uma bolsa agora"):
        return
    bolsa_id = ui.ler_inteiro("ID da bolsa (0 cancela)", minimo=0)
    if bolsa_id == 0:
        return
    bolsa = SERVICO.utilizar_bolsa(bolsa_id, usuario_id)
    ui.sucesso("Bolsa {0} marcada como {1}.".format(bolsa.id, bolsa.status))


@ui.submenu
def menu_sangue():
    ui.executar_menu(CABECALHO, [
        ("Estoque por tipo sanguineo", sangue_estoque),
        ("Registrar doacao", sangue_doar),
        ("Bolsas compativeis com um receptor", sangue_compativeis),
    ], subtitulo="6. Banco de sangue")


# ---------------------------------------------------------------------------
# 7. MANUTENCAO
# ---------------------------------------------------------------------------
def manutencao_rotina():
    ui.secao("Rotina de manutencao")
    print("  Vence bolsas fora da validade e descarta orgaos sem prazo de isquemia.")
    resultado = SERVICO.executar_manutencao()
    ui.tabela([{"item": chave, "registros": valor}
               for chave, valor in sorted(resultado.items())],
              titulos=["ITEM", "REGISTROS AFETADOS"])


def manutencao_integridade():
    ui.secao("Verificacao de integridade")
    problemas = SERVICO.verificar_integridade()
    if not problemas:
        ui.sucesso("Nenhuma inconsistencia encontrada.")
        return
    ui.tabela([{"verificacao": nome, "ocorrencias": total}
               for nome, total in problemas],
              titulos=["VERIFICACAO", "OCORRENCIAS"])


@ui.submenu
def menu_manutencao():
    ui.executar_menu(CABECALHO, [
        ("Executar rotina de manutencao", manutencao_rotina),
        ("Verificar integridade", manutencao_integridade),
        ("Hospitais", lambda: ui.tabela(
            SERVICO.listar_hospitais(),
            colunas=["id", "nome", "cidade", "uf", "latitude", "longitude"],
            titulos=["ID", "HOSPITAL", "CIDADE", "UF", "LAT", "LON"])),
    ], subtitulo="7. Manutencao")


# ---------------------------------------------------------------------------
# MENU PRINCIPAL
# ---------------------------------------------------------------------------
def principal(servico=None):
    global SERVICO, DIARIO, ENUM
    proprio = servico is None
    SERVICO = servico or CentralService()
    ENUM = enums_do_banco(SERVICO.conexao)
    try:
        ui.executar_menu(CABECALHO, [
            ("Doadores", menu_doadores),
            ("Receptores e fila de espera", menu_fila),
            ("Orgaos", menu_orgaos),
            ("Compatibilidade e alocacao", menu_compatibilidade),
            ("Processos e logistica", menu_processos),
            ("Banco de sangue", menu_sangue),
            ("Manutencao", menu_manutencao),
        ], subtitulo="Sistema 2 - PostgreSQL", rotulo_saida="Sair")
    finally:
        if proprio:
            SERVICO.fechar()


if __name__ == "__main__":
    try:
        principal()
    except ErroDeNegocio as erro:
        ui.aviso(str(erro))
