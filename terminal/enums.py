"""Leitura dos ENUMs do PostgreSQL.

O backend define os dominios como tipos nativos (CREATE TYPE ... AS ENUM).
As telas montam suas listas de opcoes a partir daqui, entao um valor novo no
banco aparece sozinho nos menus, na interface grafica e no front web.
"""

CONSULTA = """
    SELECT t.typname AS tipo, e.enumlabel AS valor
      FROM pg_type t
      JOIN pg_enum e ON e.enumtypid = t.oid
      JOIN pg_namespace n ON n.oid = t.typnamespace
     WHERE n.nspname = 'public'
     ORDER BY t.typname, e.enumsortorder
"""


def enums_do_banco(conexao):
    """Devolve {nome_do_enum: [valores...]} do banco conectado."""
    with conexao.cursor() as cursor:
        cursor.execute(CONSULTA)
        linhas = cursor.fetchall()
    agrupado = {}
    for linha in linhas:
        tipo = linha["tipo"] if isinstance(linha, dict) else linha[0]
        valor = linha["valor"] if isinstance(linha, dict) else linha[1]
        agrupado.setdefault(tipo, []).append(valor)
    return agrupado


def sinal_rh(fator_rh):
    """'positivo' -> '+'  |  'negativo' -> '-'"""
    return {"positivo": "+", "negativo": "-"}.get(fator_rh, "")


def sangue(tipo_sanguineo, fator_rh):
    if not tipo_sanguineo or not fator_rh:
        return "nao informado"
    return "{0}{1}".format(tipo_sanguineo, sinal_rh(fator_rh))
