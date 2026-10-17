from contextlib import contextmanager

import psycopg2
from psycopg2 import errors as pg


class ErroDeNegocio(Exception):
    pass


class NaoEncontrado(ErroDeNegocio):
    pass


class DadosInvalidos(ErroDeNegocio):
    pass


class ErroDeConexao(ErroDeNegocio):
    pass


MENSAGENS_RESTRICOES = {
    "usuario_cpf_key": "Já existe um usuário com este CPF.",
    "usuario_email_key": "Já existe um usuário com este e-mail.",
    "usuario_cpf_check": "CPF inválido: informe 11 dígitos.",
    "usuario_email_check": "E-mail inválido.",
    "usuario_uf_check": "UF inválida: use a sigla com 2 letras (ex.: CE).",
    "ck_sangue_completo": "Informe tipo sanguíneo e fator RH juntos.",
    "uq_alergia": "Esta alergia já está registrada para o usuário.",
    "uq_usuario_doenca": "Este diagnóstico já está registrado nesta data.",
    "uq_aplicacao": "Esta dose desta vacina já foi registrada.",
    "doador_usuario_id_key": "Este usuário já está cadastrado como doador.",
    "receptor_usuario_id_key": "Este usuário já está cadastrado como receptor.",
    "uq_fila_ativa": "O receptor já está aguardando este tipo de órgão.",
    "uq_alocacao_orgao": "Este órgão já possui uma alocação ativa.",
    "uq_alocacao_fila": "Este receptor já possui um órgão alocado.",
    "fila_espera_urgencia_check": "A urgência deve estar entre 1 e 5.",
    "bolsa_sangue_volume_ml_check": "O volume da bolsa deve estar entre 200 e 600 mL.",
}


@contextmanager
def traduzir_erros_do_banco():
    try:
        yield
    except pg.RaiseException as erro:
        raise ErroDeNegocio(erro.diag.message_primary) from None
    except (pg.UniqueViolation, pg.CheckViolation) as erro:
        restricao = erro.diag.constraint_name
        raise DadosInvalidos(
            MENSAGENS_RESTRICOES.get(restricao, f"Dados inválidos ({restricao}).")
        ) from None
    except pg.ForeignKeyViolation:
        raise DadosInvalidos("Referência inválida: o registro relacionado não existe.") from None
    except pg.NotNullViolation as erro:
        raise DadosInvalidos(f"Campo obrigatório não informado: {erro.diag.column_name}.") from None
    except pg.InvalidTextRepresentation as erro:
        raise DadosInvalidos(f"Valor inválido: {erro.diag.message_primary}") from None
    except pg.ReadOnlySqlTransaction:
        raise ErroDeNegocio("Operação de escrita em uma conexão somente leitura.") from None
    except psycopg2.Error as erro:
        raise ErroDeNegocio(f"Erro no banco de dados: {erro.diag.message_primary or erro}") from None


@contextmanager
def transacao(conexao):
    with traduzir_erros_do_banco():
        with conexao:
            with conexao.cursor() as cursor:
                yield cursor
