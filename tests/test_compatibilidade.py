import pytest

from backend.central import compatibilidade as c


@pytest.mark.parametrize("doador, receptor, esperado", [
    ("O", "O", True), ("O", "A", True), ("O", "B", True), ("O", "AB", True),
    ("A", "A", True), ("A", "AB", True), ("A", "O", False), ("A", "B", False),
    ("B", "B", True), ("B", "AB", True), ("B", "A", False), ("B", "O", False),
    ("AB", "AB", True), ("AB", "A", False), ("AB", "B", False), ("AB", "O", False),
])
def test_matriz_abo_completa(doador, receptor, esperado):
    assert c.abo_compativel(doador, receptor) is esperado


def test_rh_importa_so_no_sangue():
    assert c.abo_compativel("A", "A")
    assert not c.sangue_compativel("A", "positivo", "A", "negativo")
    assert c.sangue_compativel("A", "negativo", "A", "positivo")
    assert c.sangue_compativel("O", "negativo", "AB", "positivo")
    assert not c.sangue_compativel("AB", "positivo", "O", "positivo")


def test_distancia_fortaleza_recife():
    assert c.distancia_km(-3.7319, -38.5267, -8.0476, -34.877) == 627.0


def test_modal_e_tempo():
    assert c.modal_transporte(0) == "mesmo hospital"
    assert c.modal_transporte(150) == "terrestre"
    assert c.modal_transporte(151) == "aéreo"
    assert c.tempo_transporte_h(0) == 1.0
    assert c.tempo_transporte_h(120) == 3.0
    assert c.tempo_transporte_h(400) == 2.0


def oferta(sangue="A", horas=3.0):
    return c.OfertaOrgao(orgao_id=1, tipo_orgao="Coração", doador_usuario_id=99,
                         doador_nome="Doador", doador_sangue=sangue, hospital="H1",
                         latitude=-3.7319, longitude=-38.5267, horas_restantes=horas)


def pedido(fila_id, tipo="A", urgencia=3, dias=100, lat=-3.7319, lon=-38.5267):
    return c.PedidoFila(fila_id=fila_id, receptor_id=fila_id, usuario_id=fila_id,
                        nome=f"R{fila_id}", tipo_sanguineo=tipo,
                        fator_rh="positivo" if tipo else None, hospital="H",
                        latitude=lat, longitude=lon, urgencia=urgencia, dias_espera=dias)


def test_motivos_de_exclusao():
    assert c.avaliar(oferta(), pedido(1, tipo=None)).motivo_exclusao == "Sem tipagem sanguínea no Diário"
    assert c.avaliar(oferta(), pedido(2, tipo="B")).motivo_exclusao == "Incompatível ABO (A → B)"
    longe = c.avaliar(oferta(horas=3), pedido(3, lat=-30.03, lon=-51.21))
    assert not longe.elegivel and longe.motivo_exclusao.startswith("Inviável")
    assert c.avaliar(oferta(), pedido(4, tipo="AB")).elegivel


def test_ordem_de_prioridade():
    fila = [
        pedido(1, tipo="AB", urgencia=3, dias=900),
        pedido(2, tipo="A",  urgencia=3, dias=100),
        pedido(3, tipo="AB", urgencia=5, dias=10),
        pedido(4, tipo="O",  urgencia=5, dias=999),
        pedido(5, tipo="AB", urgencia=3, dias=900, lat=-3.69, lon=-40.35),
    ]
    resultado = c.ranquear(oferta(horas=30), fila)
    assert [r.pedido.fila_id for r in resultado] == [3, 2, 1, 5, 4]
    assert [r.posicao for r in resultado] == [1, 2, 3, 4, None]


def test_triagem_sangue():
    assert c.motivos_inaptidao_sangue(30, "feminino", 60, None, []) == []
    assert c.motivos_inaptidao_sangue(30, "feminino", 60, 89, [])
    assert c.motivos_inaptidao_sangue(30, "masculino", 60, 60, []) == []
    assert c.motivos_inaptidao_sangue(15, "masculino", 60, None, [])
    assert c.motivos_inaptidao_sangue(30, "masculino", 48, None, [])
    assert c.motivos_inaptidao_sangue(30, "masculino", None, None, ["Hepatite C"])
