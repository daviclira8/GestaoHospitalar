import psycopg2
import pytest

from backend.erros import DadosInvalidos, ErroDeNegocio, NaoEncontrado


def test_crud_usuario(bancos):
    diario, _ = bancos
    u = diario.cadastrar_usuario(nome=" Ana Teste ", cpf="123.456.789-09",
                                 data_nascimento="01/02/2000", sexo="Feminino", uf="ce")
    assert (u.nome, u.cpf, u.uf, u.sangue) == ("Ana Teste", "12345678909", "CE", "não informado")
    assert diario.buscar_por_cpf("12345678909").id == u.id
    assert diario.atualizar_usuario(u.id, cidade="Sobral").cidade == "Sobral"
    u = diario.registrar_tipagem(u.id, "ab", "negativo")
    assert u.sangue == "AB-"
    assert any(e.tipo.startswith("Tipagem") for e in diario.listar_exames(u.id))
    diario.adicionar_alergia(u.id, "Látex", "leve")
    diario.excluir_usuario(u.id)
    with pytest.raises(NaoEncontrado):
        diario.buscar_usuario(u.id)


@pytest.mark.parametrize("campos, mensagem", [
    (dict(cpf="10000000001"), "CPF"),
    (dict(cpf="123"), "11 dígitos"),
    (dict(data_nascimento="01/01/2999"), "futuro"),
    (dict(sexo="x"), "Sexo"),
    (dict(tipo_sanguineo="A"), "juntos"),
    (dict(tipo_sanguineo="C", fator_rh="positivo"), "Tipo sanguíneo"),
])
def test_validacoes_usuario(bancos, campos, mensagem):
    diario, _ = bancos
    dados = dict(nome="X", cpf="99999999999", data_nascimento="2000-01-01", sexo="outro")
    dados.update(campos)
    with pytest.raises(DadosInvalidos, match=mensagem):
        diario.cadastrar_usuario(**dados)


def test_exame_nao_pode_usar_consulta_de_outro_usuario(bancos):
    diario, _ = bancos
    with pytest.raises(DadosInvalidos, match="outro usuário"):
        diario.registrar_exame(2, "Hemograma", "2026-01-01", consulta_id=1)


def test_metricas_ao_longo_do_tempo(bancos):
    diario, _ = bancos
    serie = diario.historico_metrica(2, "glicemia_jejum")
    assert [m.variacao for m in serie] == [None, -17.0, -13.0, -9.0]
    assert diario.prontuario(10).metricas.keys() == {"peso", "pressao_sistolica"}


def test_selecao_do_coracao(bancos):
    _, central = bancos
    r = central.selecionar_receptores(6)
    assert r.indicado.pedido.nome == "Lucas Ferreira Dantas"
    motivos = {c.pedido.nome: c.motivo_exclusao for c in r.excluidos}
    assert motivos["Igor Sampaio Teixeira"] == "Incompatível ABO (A → B)"
    assert motivos["Sérgio Lemos Vieira"].startswith("Inviável")


def test_python_e_sql_concordam_na_logistica(bancos):
    _, central = bancos
    for orgao_id in (3, 5, 6):
        python = {c.pedido.fila_id: c for c in central.selecionar_receptores(orgao_id).candidatos}
        with central.conexao.cursor() as cur:
            cur.execute("SELECT * FROM fn_candidatos_orgao(%s)", (orgao_id,))
            sql = cur.fetchall()
        central.conexao.rollback()
        assert {l["fila_id"] for l in sql} == set(python)
        for l in sql:
            assert float(l["distancia_km"]) == python[l["fila_id"]].distancia_km
            assert l["logisticamente_viavel"] == python[l["fila_id"]].logistica_ok


def test_alocacao_e_fluxo_logistico(bancos):
    _, central = bancos
    with pytest.raises(ErroDeNegocio, match="Incompatível ABO"):
        central.alocar_orgao(6, 9)
    aloc, escolhido = central.alocar_melhor_receptor(6)
    assert escolhido.pedido.fila_id == 12 and aloc.status_logistica == "em_transporte"
    with pytest.raises(ErroDeNegocio, match="não está disponível"):
        central.alocar_orgao(6, 10)
    assert central.registrar_entrega(aloc.id).status_logistica == "entregue"
    assert central.concluir_transplante(aloc.id).status_logistica == "realizado"
    assert all(p.fila_id != 12 for p in central.fila_ativa())


def test_cancelamento_devolve_o_orgao(bancos):
    _, central = bancos
    aloc, _ = central.alocar_melhor_receptor(3)
    assert central.cancelar_alocacao(aloc.id).status_logistica == "cancelado"
    assert 3 in {o.orgao_id for o in central.orgaos_disponiveis()}
    central.alocar_orgao(3, 3)


def test_receptor_com_orgao_a_caminho_sai_da_selecao(bancos):
    _, central = bancos
    central.alocar_orgao(3, 4)
    assert 4 not in {c.pedido.fila_id for c in central.selecionar_receptores(4).candidatos}


def test_receptor_precisa_de_tipagem_no_diario(bancos):
    diario, central = bancos
    with pytest.raises(ErroDeNegocio, match="tipagem"):
        central.cadastrar_receptor(16, 1)
    diario.registrar_tipagem(16, "B", "negativo")
    receptor = central.cadastrar_receptor(16, 1)
    assert receptor.nome == "Vanessa Pires Cunha"
    with pytest.raises(NaoEncontrado):
        central.cadastrar_receptor(999, 1)


def test_diagnostico_no_diario_torna_doador_inapto(bancos):
    diario, central = bancos
    doador = central.cadastrar_doador(19, "vivo", 1)
    assert doador.status == "apto"
    diario.registrar_diagnostico(19, doenca_id=5, data_diagnostico="2026-10-01")
    mudancas = central.reavaliar_doadores()
    assert [(d.usuario_id, novo) for d, _, novo in mudancas] == [(13, "inapto"), (19, "inapto")]
    with pytest.raises(ErroDeNegocio, match="INAPTO"):
        central.registrar_orgao(doador.id, tipo_orgao_id=1)


def test_central_nao_consegue_escrever_no_diario(bancos):
    _, central = bancos
    with pytest.raises(psycopg2.errors.ReadOnlySqlTransaction):
        with central.diario.conexao.cursor() as cur:
            cur.execute("DELETE FROM usuario")
    central.diario.conexao.rollback()


def test_integridade_detecta_usuario_apagado_no_diario(bancos):
    diario, central = bancos
    assert central.verificar_integridade() == []
    diario.excluir_usuario(10)
    assert central.verificar_integridade() == [("receptor", 10)]


def test_sangue(bancos):
    diario, central = bancos
    assert {b.sangue for b in central.bolsas_compativeis(10)} == {"O-"}
    with pytest.raises(ErroDeNegocio, match="última doação"):
        central.registrar_doacao_sangue(19, 1)
    diario.registrar_metrica(2, "peso", 48, "kg")
    with pytest.raises(ErroDeNegocio, match="peso"):
        central.registrar_doacao_sangue(2, 1)
    bolsa = central.registrar_doacao_sangue(12, 1)
    assert bolsa.sangue == "A+" and (bolsa.data_validade - bolsa.data_coleta).days == 42
    assert central.estoque_sangue()["A+"]["bolsas"] == 2
    assert central.utilizar_bolsa(bolsa.id, 2).status == "utilizada"
    with pytest.raises(ErroDeNegocio):
        central.utilizar_bolsa(bolsa.id, 2)
