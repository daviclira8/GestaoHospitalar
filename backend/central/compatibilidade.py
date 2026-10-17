from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from typing import Optional

REGRAS_ABO = frozenset({
    ("O", "O"), ("O", "A"), ("O", "B"), ("O", "AB"),
    ("A", "A"), ("A", "AB"),
    ("B", "B"), ("B", "AB"),
    ("AB", "AB"),
})

RAIO_TERRA_KM = 6371
LIMITE_TERRESTRE_KM = 150
VELOCIDADE_TERRESTRE_KMH = 60
VELOCIDADE_AEREA_KMH = 400
TEMPO_PREPARO_H = 1

IDADE_MINIMA_SANGUE = 16
IDADE_MAXIMA_SANGUE = 69
PESO_MINIMO_SANGUE_KG = 50
INTERVALO_MINIMO_DIAS = {"masculino": 60, "feminino": 90, "outro": 90}


def abo_compativel(tipo_doador: str, tipo_receptor: str, regras=REGRAS_ABO) -> bool:
    return (tipo_doador, tipo_receptor) in regras


def sangue_compativel(tipo_doador: str, rh_doador: str, tipo_receptor: str,
                      rh_receptor: str, regras=REGRAS_ABO) -> bool:
    rh_ok = rh_receptor == "positivo" or rh_doador == "negativo"
    return abo_compativel(tipo_doador, tipo_receptor, regras) and rh_ok


def distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return round(2 * RAIO_TERRA_KM * asin(sqrt(a)), 1)


def modal_transporte(distancia: float) -> str:
    if distancia == 0:
        return "mesmo hospital"
    return "terrestre" if distancia <= LIMITE_TERRESTRE_KM else "aéreo"


def tempo_transporte_h(distancia: float) -> float:
    velocidade = (VELOCIDADE_TERRESTRE_KMH if distancia <= LIMITE_TERRESTRE_KM
                  else VELOCIDADE_AEREA_KMH)
    return round(TEMPO_PREPARO_H + distancia / velocidade, 2)


@dataclass
class OfertaOrgao:
    orgao_id: int
    tipo_orgao: str
    doador_usuario_id: int
    doador_nome: str
    doador_sangue: str
    hospital: str
    latitude: float
    longitude: float
    horas_restantes: float


@dataclass
class PedidoFila:
    fila_id: int
    receptor_id: int
    usuario_id: int
    nome: str
    tipo_sanguineo: Optional[str]
    fator_rh: Optional[str]
    hospital: str
    latitude: float
    longitude: float
    urgencia: int
    dias_espera: int


@dataclass
class Candidato:
    pedido: PedidoFila
    distancia_km: float
    modal: str
    tempo_transporte_h: float
    abo_ok: bool
    isogrupo: bool
    logistica_ok: bool
    motivo_exclusao: Optional[str] = None
    posicao: Optional[int] = None

    @property
    def elegivel(self) -> bool:
        return self.motivo_exclusao is None

    @property
    def sangue(self) -> str:
        p = self.pedido
        if not p.tipo_sanguineo:
            return "não informado"
        return p.tipo_sanguineo + ("+" if p.fator_rh == "positivo" else "-")


def avaliar(oferta: OfertaOrgao, pedido: PedidoFila, regras=REGRAS_ABO) -> Candidato:
    dist = distancia_km(oferta.latitude, oferta.longitude, pedido.latitude, pedido.longitude)
    tempo = tempo_transporte_h(dist)
    tem_tipagem = pedido.tipo_sanguineo is not None
    abo_ok = tem_tipagem and abo_compativel(oferta.doador_sangue, pedido.tipo_sanguineo, regras)
    logistica_ok = tempo <= oferta.horas_restantes

    motivo = None
    if not tem_tipagem:
        motivo = "Sem tipagem sanguínea no Diário"
    elif not abo_ok:
        motivo = f"Incompatível ABO ({oferta.doador_sangue} → {pedido.tipo_sanguineo})"
    elif not logistica_ok:
        motivo = (f"Inviável: transporte de {tempo:.1f} h > "
                  f"{oferta.horas_restantes:.1f} h restantes")

    return Candidato(
        pedido=pedido, distancia_km=dist, modal=modal_transporte(dist),
        tempo_transporte_h=tempo, abo_ok=abo_ok,
        isogrupo=tem_tipagem and pedido.tipo_sanguineo == oferta.doador_sangue,
        logistica_ok=logistica_ok, motivo_exclusao=motivo)


def chave_prioridade(c: Candidato) -> tuple:
    return (-c.pedido.urgencia,
            not c.isogrupo,
            -c.pedido.dias_espera,
            c.distancia_km)


def ranquear(oferta: OfertaOrgao, fila: list[PedidoFila], regras=REGRAS_ABO) -> list[Candidato]:
    avaliados = [avaliar(oferta, pedido, regras) for pedido in fila]
    elegiveis = sorted((c for c in avaliados if c.elegivel), key=chave_prioridade)
    excluidos = sorted((c for c in avaliados if not c.elegivel), key=chave_prioridade)
    for posicao, candidato in enumerate(elegiveis, start=1):
        candidato.posicao = posicao
    return elegiveis + excluidos


def motivos_inaptidao_sangue(idade: int, sexo: str, peso_kg: Optional[float],
                             dias_desde_ultima: Optional[int],
                             restricoes_clinicas: list[str]) -> list[str]:
    motivos = []
    if not IDADE_MINIMA_SANGUE <= idade <= IDADE_MAXIMA_SANGUE:
        motivos.append(f"idade {idade} fora da faixa {IDADE_MINIMA_SANGUE}–{IDADE_MAXIMA_SANGUE} anos")
    if peso_kg is not None and peso_kg < PESO_MINIMO_SANGUE_KG:
        motivos.append(f"peso {peso_kg:.1f} kg abaixo de {PESO_MINIMO_SANGUE_KG} kg")
    intervalo = INTERVALO_MINIMO_DIAS.get(sexo, 90)
    if dias_desde_ultima is not None and dias_desde_ultima < intervalo:
        motivos.append(f"última doação há {dias_desde_ultima} dias (mínimo {intervalo})")
    for doenca in restricoes_clinicas:
        motivos.append(f"doença que impede doação: {doenca}")
    return motivos
