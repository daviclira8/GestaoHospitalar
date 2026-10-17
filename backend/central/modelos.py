from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from backend.base import Registro
from backend.central.compatibilidade import Candidato, OfertaOrgao

TIPOS_DOADOR = ("vivo", "falecido")


@dataclass
class Hospital(Registro):
    id: int
    nome: str
    cidade: str
    uf: str
    latitude: float
    longitude: float


@dataclass
class TipoOrgao(Registro):
    id: int
    nome: str
    tempo_max_isquemia_horas: int
    permite_doador_vivo: bool


@dataclass
class Doador(Registro):
    id: int
    usuario_id: int
    tipo: str
    hospital_id: int
    data_cadastro: date
    status: str
    nome: Optional[str] = None
    motivo_inaptidao: Optional[str] = None


@dataclass
class Receptor(Registro):
    id: int
    usuario_id: int
    hospital_id: int
    data_cadastro: date
    nome: Optional[str] = None


@dataclass
class EntradaFila(Registro):
    id: int
    receptor_id: int
    tipo_orgao_id: int
    data_entrada: datetime
    urgencia: int
    status: str


@dataclass
class PosicaoFila(Registro):
    orgao: str
    posicao: int
    fila_id: int
    receptor_usuario_id: int
    hospital: str
    uf: str
    urgencia: int
    entrada: date
    dias_espera: int
    nome: Optional[str] = None
    sangue: Optional[str] = None


@dataclass
class Orgao(Registro):
    id: int
    doador_id: int
    tipo_orgao_id: int
    hospital_id: int
    data_hora_captacao: datetime
    status: str


@dataclass
class OrgaoDisponivel(Registro):
    orgao_id: int
    orgao: str
    doador_usuario_id: int
    tipo_doador: str
    hospital_origem: str
    data_hora_captacao: datetime
    prazo_limite: datetime
    horas_restantes: float
    doador_nome: Optional[str] = None
    doador_sangue: Optional[str] = None


@dataclass
class Alocacao(Registro):
    id: int
    orgao_id: int
    fila_id: int
    data_hora: datetime
    status_logistica: str


@dataclass
class Processo(Registro):
    alocacao_id: int
    orgao: str
    doador_usuario_id: int
    receptor_usuario_id: int
    hospital_origem: str
    hospital_destino: str
    distancia_km: float
    alocado_em: datetime
    status_logistica: str
    status_fila: str
    doador_nome: Optional[str] = None
    receptor_nome: Optional[str] = None


@dataclass
class Bolsa(Registro):
    id: int
    usuario_id: int
    hospital_id: int
    data_coleta: date
    data_validade: date
    volume_ml: int
    status: str
    hospital: Optional[str] = None
    sangue: Optional[str] = None

    @property
    def dias_ate_vencer(self) -> int:
        return (self.data_validade - date.today()).days


@dataclass
class ResultadoSelecao:
    oferta: OfertaOrgao
    candidatos: list[Candidato] = field(default_factory=list)

    @property
    def elegiveis(self) -> list[Candidato]:
        return [c for c in self.candidatos if c.elegivel]

    @property
    def excluidos(self) -> list[Candidato]:
        return [c for c in self.candidatos if not c.elegivel]

    @property
    def indicado(self) -> Optional[Candidato]:
        return self.elegiveis[0] if self.elegiveis else None
