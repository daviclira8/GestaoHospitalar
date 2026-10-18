# -*- coding: utf-8 -*-
"""Utilitarios dos menus de terminal: tabelas, leitura validada e menus.

As tabelas aceitam dicionarios e tambem as dataclasses devolvidas pelo
backend (backend.base.Registro), convertendo date, datetime e Decimal para
texto legivel.
"""

import dataclasses
import datetime
import os
import re
import sys
from decimal import Decimal

LARGURA = 78


# ---------------------------------------------------------------------------
# Leitura de registros do backend
# ---------------------------------------------------------------------------
def valor_do_campo(registro, campo, padrao=""):
    """Le um campo de uma dataclass, dicionario ou objeto qualquer."""
    if registro is None:
        return padrao
    if isinstance(registro, dict):
        valor = registro.get(campo, padrao)
    else:
        valor = getattr(registro, campo, padrao)
    return padrao if valor is None else valor


def como_dicionario(registro):
    """Converte um registro do backend em dicionario JSON-friendly."""
    if registro is None:
        return None
    if isinstance(registro, dict):
        bruto = dict(registro)
    elif dataclasses.is_dataclass(registro) and not isinstance(registro, type):
        bruto = dataclasses.asdict(registro)
    else:
        bruto = {c: getattr(registro, c) for c in dir(registro)
                 if not c.startswith("_") and not callable(getattr(registro, c))}
    return {chave: simplificar(valor) for chave, valor in bruto.items()}


def simplificar(valor):
    """Normaliza tipos do psycopg2 (date, datetime, Decimal) para texto/numero."""
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, datetime.datetime):
        return valor.strftime("%Y-%m-%d %H:%M")
    if isinstance(valor, datetime.date):
        return valor.isoformat()
    if isinstance(valor, (list, tuple)):
        return [simplificar(item) for item in valor]
    if isinstance(valor, dict):
        return {chave: simplificar(item) for chave, item in valor.items()}
    if dataclasses.is_dataclass(valor) and not isinstance(valor, type):
        return como_dicionario(valor)
    return valor


def texto(valor):
    """Representacao curta de um valor para exibir em tabelas."""
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "sim" if valor else "nao"
    if isinstance(valor, Decimal):
        valor = float(valor)
    if isinstance(valor, float):
        return "{0:g}".format(valor)
    if isinstance(valor, datetime.datetime):
        return valor.strftime("%Y-%m-%d %H:%M")
    if isinstance(valor, datetime.date):
        return valor.isoformat()
    return str(valor)


def hoje():
    return datetime.date.today().isoformat()


def agora():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


# ---------------------------------------------------------------------------
# Saida formatada
# ---------------------------------------------------------------------------
def limpar():
    if os.name == "nt":
        os.system("cls")
    elif sys.stdout.isatty():
        sys.stdout.write("\033[H\033[J")   # move o cursor e limpa a tela
        sys.stdout.flush()


def titulo(texto, subtitulo=None):
    print("=" * LARGURA)
    print(texto.center(LARGURA))
    if subtitulo:
        print(subtitulo.center(LARGURA))
    print("=" * LARGURA)


def secao(texto):
    print()
    print("-" * LARGURA)
    print(" " + texto)
    print("-" * LARGURA)


def aviso(texto):
    print("\n  [!] " + texto)


def sucesso(texto):
    print("\n  [OK] " + texto)


def pausar():
    try:
        input("\n  Pressione ENTER para continuar... ")
    except EOFError:
        sys.exit(0)


def tabela(linhas, colunas=None, titulos=None, vazio="Nenhum registro encontrado."):
    """Imprime uma lista de sqlite3.Row (ou dicts) como tabela alinhada.

    colunas: nomes das colunas a exibir (padrao: todas, na ordem do SELECT)
    titulos: rotulos do cabecalho (padrao: nome da coluna em maiusculas)
    """
    if not linhas:
        aviso(vazio)
        return

    if colunas is None:
        primeira = linhas[0]
        colunas = (list(primeira.keys()) if isinstance(primeira, dict)
                   else [c.name for c in __import__("dataclasses").fields(primeira)])
    if titulos is None:
        titulos = [c.replace("_", " ").upper() for c in colunas]

    dados = []
    for linha in linhas:
        dados.append([texto(valor_do_campo(linha, c, None)) for c in colunas])

    larguras = []
    for i, cab in enumerate(titulos):
        maior = max([len(cab)] + [len(d[i]) for d in dados])
        larguras.append(min(maior, 34))

    def formatar(valores):
        partes = []
        for i, valor in enumerate(valores):
            if len(valor) > larguras[i]:
                valor = valor[: larguras[i] - 3] + "..."
            partes.append(valor.ljust(larguras[i]))
        return " | ".join(partes)

    print()
    print("  " + formatar(titulos))
    print("  " + "-+-".join("-" * l for l in larguras))
    for d in dados:
        print("  " + formatar(d))
    print("\n  {0} registro(s).".format(len(dados)))


# ---------------------------------------------------------------------------
# Entrada de dados validada
# ---------------------------------------------------------------------------
def _ler(mensagem):
    try:
        return input(mensagem).strip()
    except EOFError:
        print()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n  Operacao cancelada.")
        raise


def ler_texto(rotulo, obrigatorio=True, padrao=None):
    while True:
        extra = " [{0}]".format(padrao) if padrao else ""
        valor = _ler("  {0}{1}: ".format(rotulo, extra))
        if not valor and padrao is not None:
            return padrao
        if valor or not obrigatorio:
            return valor or None
        aviso("Campo obrigatorio.")


def ler_inteiro(rotulo, minimo=None, maximo=None, padrao=None, obrigatorio=True):
    while True:
        extra = " [{0}]".format(padrao) if padrao is not None else ""
        valor = _ler("  {0}{1}: ".format(rotulo, extra))
        if not valor:
            if padrao is not None:
                return padrao
            if not obrigatorio:
                return None
            aviso("Campo obrigatorio.")
            continue
        try:
            numero = int(valor)
        except ValueError:
            aviso("Digite um numero inteiro.")
            continue
        if minimo is not None and numero < minimo:
            aviso("Valor minimo: {0}.".format(minimo))
            continue
        if maximo is not None and numero > maximo:
            aviso("Valor maximo: {0}.".format(maximo))
            continue
        return numero


def ler_opcao(rotulo, opcoes, padrao=None, obrigatorio=True):
    """Le um valor que precisa pertencer a uma lista de opcoes."""
    lista = "/".join(opcoes)
    while True:
        extra = " [{0}]".format(padrao) if padrao else ""
        valor = _ler("  {0} ({1}){2}: ".format(rotulo, lista, extra)).upper()
        if not valor:
            if padrao:
                return padrao
            if not obrigatorio:
                return None
        if valor in [o.upper() for o in opcoes]:
            return valor
        aviso("Opcao invalida. Use: " + lista)


def ler_data(rotulo, obrigatorio=True, padrao=None):
    """Le uma data no formato YYYY-MM-DD."""
    padrao_regex = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    while True:
        valor = ler_texto(rotulo + " (YYYY-MM-DD)", obrigatorio, padrao)
        if valor is None:
            return None
        if padrao_regex.match(valor):
            return valor
        aviso("Formato invalido. Exemplo: 2025-10-13")


def ler_data_hora(rotulo, obrigatorio=True):
    """Le uma data/hora no formato YYYY-MM-DD HH:MM."""
    padrao_regex = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")
    while True:
        valor = ler_texto(rotulo + " (YYYY-MM-DD HH:MM)", obrigatorio)
        if valor is None:
            return None
        if padrao_regex.match(valor):
            return valor
        aviso("Formato invalido. Exemplo: 2025-10-13 14:30")


def confirmar(mensagem):
    return ler_opcao(mensagem, ("S", "N"), padrao="N") == "S"


# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------
def menu(cabecalho, itens, subtitulo=None, rotulo_saida="Voltar"):
    """Desenha um menu numerado e devolve a acao escolhida.

    itens: lista de tuplas (descricao, funcao). A opcao 0 encerra o menu.
    Retorna None quando o usuario escolhe 0.
    """
    limpar()
    titulo(cabecalho, subtitulo)
    print()
    for indice, (descricao, _) in enumerate(itens, start=1):
        print("   {0:>2}. {1}".format(indice, descricao))
    print("    0. {0}".format(rotulo_saida))
    print()
    escolha = ler_inteiro("Opcao", minimo=0, maximo=len(itens))
    if escolha == 0:
        return None
    return itens[escolha - 1][1]


def submenu(funcao):
    """Marca a funcao como submenu: ao retornar nao exibe a pausa de leitura."""
    funcao._submenu = True
    return funcao


def executar_menu(cabecalho, itens, subtitulo=None, rotulo_saida="Voltar"):
    """Laco principal de um menu: desenha, executa a acao e repete."""
    while True:
        try:
            acao = menu(cabecalho, itens, subtitulo, rotulo_saida)
        except KeyboardInterrupt:
            return
        if acao is None:
            return
        if getattr(acao, "_submenu", False):   # abre outro menu: sem pausa
            acao()
            continue
        limpar()
        titulo(cabecalho, subtitulo)
        try:
            acao()
        except KeyboardInterrupt:
            aviso("Operacao cancelada pelo usuario.")
        except Exception as erro:                      # erros de SQL, etc.
            aviso("Erro: {0}".format(erro))
        pausar()
