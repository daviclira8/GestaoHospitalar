import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

from psycopg2 import sql

from backend.conexao import BANCO_CENTRAL, BANCO_DIARIO, RAIZ_PROJETO, conectar
from backend.erros import ErroDeNegocio, transacao

SCRIPTS_DIARIO = ["sql/diario/01_criacao.sql", "sql/diario/02_povoamento.sql"]
SCRIPTS_CENTRAL = ["sql/central/01_criacao.sql", "sql/central/02_povoamento.sql"]


def recriar_banco(nome: str) -> None:
    conexao = conectar("postgres")
    conexao.autocommit = True
    try:
        with conexao.cursor() as cursor:
            cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)")
                           .format(sql.Identifier(nome)))
            cursor.execute(sql.SQL("CREATE DATABASE {} ENCODING 'UTF8' TEMPLATE template0")
                           .format(sql.Identifier(nome)))
    finally:
        conexao.close()


def executar_scripts(nome_banco: str, scripts: list[str]) -> None:
    conexao = conectar(nome_banco)
    try:
        for caminho in scripts:
            texto = (RAIZ_PROJETO / caminho).read_text(encoding="utf-8")
            with transacao(conexao) as cursor:
                cursor.execute(texto)
            print(f"   ✔ {caminho}")
    finally:
        conexao.close()


def criar_bancos(banco_diario: str = BANCO_DIARIO, banco_central: str = BANCO_CENTRAL) -> None:
    print(f">> Diário de Saúde ({banco_diario})")
    recriar_banco(banco_diario)
    executar_scripts(banco_diario, SCRIPTS_DIARIO)
    print(f">> Central de Transplantes ({banco_central})")
    recriar_banco(banco_central)
    executar_scripts(banco_central, SCRIPTS_CENTRAL)
    print(">> Bancos criados e povoados com sucesso.")


if __name__ == "__main__":
    if "--sim" not in sys.argv:
        resposta = input(f"Isto APAGA e recria '{BANCO_DIARIO}' e '{BANCO_CENTRAL}'. "
                         "Continuar? [s/N] ")
        if resposta.strip().lower() not in ("s", "sim"):
            sys.exit("Cancelado.")
    try:
        criar_bancos()
    except ErroDeNegocio as erro:
        sys.exit(f"ERRO: {erro}")
