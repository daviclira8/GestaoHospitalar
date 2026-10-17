from dataclasses import fields
from decimal import Decimal


class Registro:
    @classmethod
    def de_linha(cls, linha: dict):
        dados = {}
        for campo in fields(cls):
            if campo.name in linha:
                valor = linha[campo.name]
                dados[campo.name] = float(valor) if isinstance(valor, Decimal) else valor
        return cls(**dados)
