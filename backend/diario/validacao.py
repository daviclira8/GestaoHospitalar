import re
from datetime import date, datetime

from backend.diario.modelos import (FATORES_RH, GRAVIDADES_ALERGIA, SEXOS,
                                    STATUS_DOENCA, TIPOS_SANGUINEOS)
from backend.erros import DadosInvalidos


def normalizar_cpf(cpf: str) -> str:
    digitos = re.sub(r"\D", "", cpf or "")
    if len(digitos) != 11:
        raise DadosInvalidos("CPF inválido: informe 11 dígitos.")
    return digitos


def para_data(valor, campo: str) -> date:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(valor).strip(), formato).date()
        except ValueError:
            pass
    raise DadosInvalidos(f"{campo}: data inválida '{valor}' (use DD/MM/AAAA).")


def para_data_hora(valor, campo: str) -> datetime:
    if isinstance(valor, datetime):
        return valor
    for formato in ("%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(valor).strip(), formato)
        except ValueError:
            pass
    raise DadosInvalidos(f"{campo}: data/hora inválida '{valor}' (use DD/MM/AAAA HH:MM).")


def nao_futura(data: date, campo: str) -> date:
    if data > date.today():
        raise DadosInvalidos(f"{campo} não pode estar no futuro.")
    return data


def obrigatorio(valor, campo: str) -> str:
    if valor is None or not str(valor).strip():
        raise DadosInvalidos(f"{campo} é obrigatório.")
    return str(valor).strip()


def opcional(valor):
    if valor is None:
        return None
    valor = str(valor).strip()
    return valor or None


def escolha(valor, opcoes: tuple, campo: str):
    if valor not in opcoes:
        raise DadosInvalidos(f"{campo} deve ser um de: {', '.join(opcoes)}.")
    return valor


def validar_tipagem(tipo, fator) -> tuple:
    tipo = opcional(tipo)
    fator = opcional(fator)
    if (tipo is None) != (fator is None):
        raise DadosInvalidos("Informe tipo sanguíneo e fator RH juntos.")
    if tipo is not None:
        tipo = escolha(tipo.upper(), TIPOS_SANGUINEOS, "Tipo sanguíneo")
        fator = escolha(fator.lower(), FATORES_RH, "Fator RH")
    return tipo, fator


def validar_dados_usuario(dados: dict) -> dict:
    limpo = {}
    if "nome" in dados:
        limpo["nome"] = obrigatorio(dados["nome"], "Nome")
    if "cpf" in dados:
        limpo["cpf"] = normalizar_cpf(dados["cpf"])
    if "data_nascimento" in dados:
        limpo["data_nascimento"] = nao_futura(
            para_data(dados["data_nascimento"], "Data de nascimento"), "Data de nascimento")
    if "sexo" in dados:
        limpo["sexo"] = escolha(str(dados["sexo"]).lower(), SEXOS, "Sexo")
    if "tipo_sanguineo" in dados or "fator_rh" in dados:
        limpo["tipo_sanguineo"], limpo["fator_rh"] = validar_tipagem(
            dados.get("tipo_sanguineo"), dados.get("fator_rh"))
    if "cidade" in dados:
        limpo["cidade"] = opcional(dados["cidade"])
    if "uf" in dados:
        uf = opcional(dados["uf"])
        if uf is not None and not re.fullmatch(r"[A-Za-z]{2}", uf):
            raise DadosInvalidos("UF inválida: use a sigla com 2 letras (ex.: CE).")
        limpo["uf"] = uf.upper() if uf else None
    if "email" in dados:
        email = opcional(dados["email"])
        if email is not None and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise DadosInvalidos("E-mail inválido.")
        limpo["email"] = email.lower() if email else None
    if "telefone" in dados:
        limpo["telefone"] = opcional(dados["telefone"])
    return limpo


def validar_gravidade(gravidade) -> str:
    return escolha(str(gravidade).lower(), GRAVIDADES_ALERGIA, "Gravidade")


def validar_status_doenca(status) -> str:
    return escolha(str(status).lower(), STATUS_DOENCA, "Status")


def validar_valor_metrica(valor) -> float:
    try:
        numero = float(str(valor).replace(",", "."))
    except ValueError:
        raise DadosInvalidos(f"Valor da métrica inválido: '{valor}'.") from None
    if numero < 0:
        raise DadosInvalidos("O valor da métrica não pode ser negativo.")
    return numero
