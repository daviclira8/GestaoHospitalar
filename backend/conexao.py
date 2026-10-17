import os
from pathlib import Path

import psycopg2
import psycopg2.extras

from backend.erros import ErroDeConexao

RAIZ_PROJETO = Path(__file__).resolve().parent.parent


def _carregar_arquivo_env() -> None:
    arquivo = RAIZ_PROJETO / ".env"
    if not arquivo.exists():
        return
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        os.environ.setdefault(chave.strip(), valor.strip())


_carregar_arquivo_env()

BANCO_DIARIO = os.getenv("DIARIO_DB", "diario_saude")
BANCO_CENTRAL = os.getenv("CENTRAL_DB", "central_transplantes")


def conectar(nome_banco: str, somente_leitura: bool = False):
    return _conectar(nome_banco, somente_leitura)


def _conectar(nome_banco: str, somente_leitura: bool = False,
              prefixo: str | None = None):
    def configuracao(chave: str, padrao: str) -> str:
        if prefixo:
            valor = os.getenv(f"{prefixo}_{chave}")
            if valor:
                return valor
        return os.getenv(chave, padrao)

    try:
        conexao = psycopg2.connect(
            dbname=nome_banco,
            host=configuracao("PGHOST", "127.0.0.1"),
            port=configuracao("PGPORT", "5432"),
            user=configuracao("PGUSER", "postgres"),
            password=configuracao("PGPASSWORD", ""),
            sslmode=configuracao("PGSSLMODE", "prefer"),
            client_encoding="UTF8",
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
    except (psycopg2.OperationalError, UnicodeDecodeError) as erro:
        raise ErroDeConexao(
            f"Não foi possível conectar ao banco '{nome_banco}'. Verifique se o "
            "PostgreSQL está rodando e se usuário/senha do arquivo .env estão "
            f"corretos. Detalhe: {erro!s}"[:400]
        ) from None
    if somente_leitura:
        conexao.set_session(readonly=True)
    return conexao


def conectar_diario(somente_leitura: bool = False):
    return _conectar(BANCO_DIARIO, somente_leitura, "DIARIO")


def conectar_central():
    return _conectar(BANCO_CENTRAL, prefixo="CENTRAL")
