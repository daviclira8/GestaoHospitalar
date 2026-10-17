from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from backend.base import Registro

SEXOS = ("masculino", "feminino", "outro")
TIPOS_SANGUINEOS = ("A", "B", "AB", "O")
FATORES_RH = ("positivo", "negativo")
GRAVIDADES_ALERGIA = ("leve", "moderada", "grave")
STATUS_DOENCA = ("ativa", "controlada", "curada")


def formatar_sangue(tipo: Optional[str], fator: Optional[str]) -> str:
    if not tipo or not fator:
        return "não informado"
    return tipo + ("+" if fator == "positivo" else "-")


def calcular_idade(nascimento: date, hoje: Optional[date] = None) -> int:
    hoje = hoje or date.today()
    fez_aniversario = (hoje.month, hoje.day) >= (nascimento.month, nascimento.day)
    return hoje.year - nascimento.year - (0 if fez_aniversario else 1)


@dataclass
class Usuario(Registro):
    id: int
    nome: str
    cpf: str
    data_nascimento: date
    sexo: str
    tipo_sanguineo: Optional[str]
    fator_rh: Optional[str]
    cidade: Optional[str]
    uf: Optional[str]
    email: Optional[str]
    telefone: Optional[str]
    criado_em: datetime

    @property
    def idade(self) -> int:
        return calcular_idade(self.data_nascimento)

    @property
    def sangue(self) -> str:
        return formatar_sangue(self.tipo_sanguineo, self.fator_rh)

    @property
    def tem_tipagem(self) -> bool:
        return self.tipo_sanguineo is not None and self.fator_rh is not None


@dataclass
class Alergia(Registro):
    id: int
    usuario_id: int
    substancia: str
    gravidade: str
    observacao: Optional[str]


@dataclass
class Doenca(Registro):
    id: int
    nome: str
    cid: Optional[str]
    impede_doacao: bool


@dataclass
class Diagnostico(Registro):
    id: int
    usuario_id: int
    doenca_id: int
    doenca: str
    cid: Optional[str]
    impede_doacao: bool
    data_diagnostico: date
    status: str


@dataclass
class Vacina(Registro):
    id: int
    nome: str
    fabricante: Optional[str]


@dataclass
class AplicacaoVacina(Registro):
    id: int
    usuario_id: int
    vacina_id: int
    vacina: str
    fabricante: Optional[str]
    data_aplicacao: date
    dose: str
    lote: Optional[str]


@dataclass
class Consulta(Registro):
    id: int
    usuario_id: int
    data_hora: datetime
    especialidade: str
    profissional: Optional[str]
    local: Optional[str]
    observacoes: Optional[str]


@dataclass
class Exame(Registro):
    id: int
    usuario_id: int
    consulta_id: Optional[int]
    tipo: str
    data: date
    resultado: Optional[str]


@dataclass
class Metrica(Registro):
    id: int
    usuario_id: int
    tipo: str
    valor: float
    unidade: str
    data_hora: datetime
    variacao: Optional[float] = None


@dataclass
class Evento(Registro):
    data: date
    evento: str
    descricao: str


@dataclass
class FichaUsuario(Registro):
    id: int
    nome: str
    cpf: str
    data_nascimento: date
    idade: int
    sexo: str
    tipo_sanguineo: Optional[str]
    fator_rh: Optional[str]
    sangue: Optional[str]
    cidade: Optional[str]
    uf: Optional[str]
    restricao_doacao: bool
    alergias: Optional[str]


@dataclass
class Prontuario:
    usuario: Usuario
    alergias: list
    diagnosticos: list
    vacinas: list
    consultas: list
    exames: list
    metricas: dict
    linha_do_tempo: list
