import os
import sys
from pathlib import Path

import pytest

os.environ["DIARIO_DB"] = "diario_saude_teste"
os.environ["CENTRAL_DB"] = "central_transplantes_teste"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import conexao as _conexao

for _prefixo in ("DIARIO", "CENTRAL"):
    for _chave in ("PGHOST", "PGPORT", "PGUSER", "PGPASSWORD", "PGSSLMODE"):
        _valor = os.getenv(_chave)
        if _valor:
            os.environ[f"{_prefixo}_{_chave}"] = _valor
        else:
            os.environ.pop(f"{_prefixo}_{_chave}", None)

from backend.erros import ErroDeConexao


@pytest.fixture
def bancos():
    from backend.central.servico import CentralService
    from backend.diario.servico import DiarioService
    from criar_bancos import criar_bancos
    try:
        criar_bancos("diario_saude_teste", "central_transplantes_teste")
    except ErroDeConexao as erro:
        pytest.skip(f"PostgreSQL indisponível: {erro}")
    diario, central = DiarioService(), CentralService()
    yield diario, central
    diario.fechar()
    central.fechar()
