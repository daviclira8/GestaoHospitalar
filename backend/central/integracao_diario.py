from dataclasses import dataclass
from typing import Optional

from backend.base import Registro
from backend.conexao import conectar_diario
from backend.erros import NaoEncontrado, transacao


@dataclass
class PessoaDiario(Registro):
    id: int
    nome: str
    idade: int
    sexo: str
    tipo_sanguineo: Optional[str]
    fator_rh: Optional[str]
    sangue: Optional[str]
    cidade: Optional[str]
    uf: Optional[str]
    restricao_doacao: bool

    @property
    def tem_tipagem(self) -> bool:
        return self.tipo_sanguineo is not None and self.fator_rh is not None


_COLUNAS = """id, nome, idade, sexo, tipo_sanguineo, fator_rh, sangue,
              cidade, uf, restricao_doacao"""


class DiarioGateway:
    def __init__(self, conexao=None):
        self.conexao = conexao or conectar_diario(somente_leitura=True)

    def fechar(self):
        self.conexao.close()

    def pessoa(self, usuario_id: int) -> PessoaDiario:
        with transacao(self.conexao) as cur:
            cur.execute(f"SELECT {_COLUNAS} FROM vw_ficha_usuario WHERE id = %s", (usuario_id,))
            linha = cur.fetchone()
        if linha is None:
            raise NaoEncontrado(f"Usuário {usuario_id} não existe no Diário de Saúde.")
        return PessoaDiario.de_linha(linha)

    def pessoas(self, ids) -> dict[int, PessoaDiario]:
        ids = list(set(ids))
        if not ids:
            return {}
        with transacao(self.conexao) as cur:
            cur.execute(f"SELECT {_COLUNAS} FROM vw_ficha_usuario WHERE id = ANY(%s)", (ids,))
            return {l["id"]: PessoaDiario.de_linha(l) for l in cur.fetchall()}

    def restricoes_doacao(self, usuario_id: int) -> list[str]:
        with transacao(self.conexao) as cur:
            cur.execute("""SELECT d.nome || ' (' || ud.status || ')' AS descricao
                             FROM usuario_doenca ud JOIN doenca d ON d.id = ud.doenca_id
                            WHERE ud.usuario_id = %s AND d.impede_doacao
                              AND ud.status <> 'curada'""", (usuario_id,))
            return [l["descricao"] for l in cur.fetchall()]

    def ultimo_peso(self, usuario_id: int) -> Optional[float]:
        with transacao(self.conexao) as cur:
            cur.execute("""SELECT valor FROM metrica_saude
                            WHERE usuario_id = %s AND tipo = 'peso'
                            ORDER BY data_hora DESC LIMIT 1""", (usuario_id,))
            linha = cur.fetchone()
        return float(linha["valor"]) if linha else None

    def ids_existentes(self, ids) -> set[int]:
        ids = list(set(ids))
        if not ids:
            return set()
        with transacao(self.conexao) as cur:
            cur.execute("SELECT id FROM usuario WHERE id = ANY(%s)", (ids,))
            return {l["id"] for l in cur.fetchall()}
