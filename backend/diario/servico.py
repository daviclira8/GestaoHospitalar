from datetime import date, datetime
from typing import Optional

from psycopg2 import sql

from backend.conexao import conectar_diario
from backend.diario import validacao as v
from backend.diario.modelos import (Alergia, AplicacaoVacina, Consulta,
                                    Diagnostico, Doenca, Evento, Exame,
                                    FichaUsuario, Metrica, Prontuario, Usuario,
                                    Vacina)
from backend.erros import DadosInvalidos, NaoEncontrado, transacao

CAMPOS_EDITAVEIS = ("nome", "data_nascimento", "sexo", "tipo_sanguineo",
                    "fator_rh", "cidade", "uf", "email", "telefone")

EXAME_TIPAGEM = "Tipagem sanguínea ABO/Rh"


class DiarioService:
    def __init__(self, conexao=None):
        self.conexao = conexao or conectar_diario()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.fechar()

    def fechar(self):
        self.conexao.close()

    def cadastrar_usuario(self, nome, cpf, data_nascimento, sexo,
                          tipo_sanguineo=None, fator_rh=None, cidade=None,
                          uf=None, email=None, telefone=None) -> Usuario:
        dados = v.validar_dados_usuario(dict(
            nome=nome, cpf=cpf, data_nascimento=data_nascimento, sexo=sexo,
            tipo_sanguineo=tipo_sanguineo, fator_rh=fator_rh, cidade=cidade,
            uf=uf, email=email, telefone=telefone))
        with transacao(self.conexao) as cur:
            cur.execute("""
                INSERT INTO usuario (nome, cpf, data_nascimento, sexo, tipo_sanguineo,
                                     fator_rh, cidade, uf, email, telefone)
                VALUES (%(nome)s, %(cpf)s, %(data_nascimento)s, %(sexo)s, %(tipo_sanguineo)s,
                        %(fator_rh)s, %(cidade)s, %(uf)s, %(email)s, %(telefone)s)
                RETURNING *""", dados)
            return Usuario.de_linha(cur.fetchone())

    def buscar_usuario(self, usuario_id: int) -> Usuario:
        with transacao(self.conexao) as cur:
            cur.execute("SELECT * FROM usuario WHERE id = %s", (usuario_id,))
            linha = cur.fetchone()
        if linha is None:
            raise NaoEncontrado(f"Usuário {usuario_id} não encontrado no Diário.")
        return Usuario.de_linha(linha)

    def buscar_por_cpf(self, cpf: str) -> Optional[Usuario]:
        with transacao(self.conexao) as cur:
            cur.execute("SELECT * FROM usuario WHERE cpf = %s", (v.normalizar_cpf(cpf),))
            linha = cur.fetchone()
        return Usuario.de_linha(linha) if linha else None

    def listar_usuarios(self, busca: Optional[str] = None) -> list[Usuario]:
        with transacao(self.conexao) as cur:
            if busca:
                cur.execute("""SELECT * FROM usuario
                                WHERE nome ILIKE %(t)s OR cpf LIKE %(t)s
                                ORDER BY nome""", {"t": f"%{busca.strip()}%"})
            else:
                cur.execute("SELECT * FROM usuario ORDER BY id")
            return [Usuario.de_linha(l) for l in cur.fetchall()]

    def atualizar_usuario(self, usuario_id: int, **campos) -> Usuario:
        invalidos = set(campos) - set(CAMPOS_EDITAVEIS)
        if invalidos:
            raise DadosInvalidos(f"Campo(s) não editável(is): {', '.join(sorted(invalidos))}.")
        if not campos:
            raise DadosInvalidos("Nenhum campo informado para atualizar.")

        if ("tipo_sanguineo" in campos) != ("fator_rh" in campos):
            atual = self.buscar_usuario(usuario_id)
            campos.setdefault("tipo_sanguineo", atual.tipo_sanguineo)
            campos.setdefault("fator_rh", atual.fator_rh)
        dados = v.validar_dados_usuario(campos)

        atribuicoes = sql.SQL(", ").join(
            sql.SQL("{} = {}").format(sql.Identifier(c), sql.Placeholder(c)) for c in dados)
        comando = sql.SQL("UPDATE usuario SET {} WHERE id = %(id)s RETURNING *").format(atribuicoes)
        with transacao(self.conexao) as cur:
            cur.execute(comando, {**dados, "id": usuario_id})
            linha = cur.fetchone()
        if linha is None:
            raise NaoEncontrado(f"Usuário {usuario_id} não encontrado no Diário.")
        return Usuario.de_linha(linha)

    def registrar_tipagem(self, usuario_id: int, tipo: str, fator: str,
                          data=None) -> Usuario:
        tipo, fator = v.validar_tipagem(tipo, fator)
        if tipo is None:
            raise DadosInvalidos("Informe tipo sanguíneo e fator RH.")
        data = v.nao_futura(v.para_data(data or date.today(), "Data do exame"), "Data do exame")
        resultado = f"{tipo} {fator}"
        with transacao(self.conexao) as cur:
            cur.execute("""UPDATE usuario SET tipo_sanguineo = %s, fator_rh = %s
                            WHERE id = %s RETURNING *""", (tipo, fator, usuario_id))
            linha = cur.fetchone()
            if linha is None:
                raise NaoEncontrado(f"Usuário {usuario_id} não encontrado no Diário.")
            cur.execute("""INSERT INTO exame (usuario_id, tipo, data, resultado)
                           VALUES (%s, %s, %s, %s)""", (usuario_id, EXAME_TIPAGEM, data, resultado))
        return Usuario.de_linha(linha)

    def excluir_usuario(self, usuario_id: int) -> None:
        with transacao(self.conexao) as cur:
            cur.execute("DELETE FROM usuario WHERE id = %s", (usuario_id,))
            if cur.rowcount == 0:
                raise NaoEncontrado(f"Usuário {usuario_id} não encontrado no Diário.")

    def adicionar_alergia(self, usuario_id: int, substancia: str, gravidade: str,
                          observacao: Optional[str] = None) -> Alergia:
        substancia = v.obrigatorio(substancia, "Substância")
        gravidade = v.validar_gravidade(gravidade)
        with transacao(self.conexao) as cur:
            cur.execute("""INSERT INTO alergia (usuario_id, substancia, gravidade, observacao)
                           VALUES (%s, %s, %s, %s) RETURNING *""",
                        (usuario_id, substancia, gravidade, v.opcional(observacao)))
            return Alergia.de_linha(cur.fetchone())

    def listar_alergias(self, usuario_id: int) -> list[Alergia]:
        with transacao(self.conexao) as cur:
            cur.execute("""SELECT * FROM alergia WHERE usuario_id = %s
                            ORDER BY gravidade DESC, substancia""", (usuario_id,))
            return [Alergia.de_linha(l) for l in cur.fetchall()]

    def remover_alergia(self, alergia_id: int) -> None:
        with transacao(self.conexao) as cur:
            cur.execute("DELETE FROM alergia WHERE id = %s", (alergia_id,))
            if cur.rowcount == 0:
                raise NaoEncontrado(f"Alergia {alergia_id} não encontrada.")

    _SELECT_DIAGNOSTICO = """
        SELECT ud.id, ud.usuario_id, ud.doenca_id, d.nome AS doenca, d.cid,
               d.impede_doacao, ud.data_diagnostico, ud.status
          FROM usuario_doenca ud JOIN doenca d ON d.id = ud.doenca_id"""

    def listar_catalogo_doencas(self) -> list[Doenca]:
        with transacao(self.conexao) as cur:
            cur.execute("SELECT * FROM doenca ORDER BY nome")
            return [Doenca.de_linha(l) for l in cur.fetchall()]

    def cadastrar_doenca(self, nome: str, cid: Optional[str] = None,
                         impede_doacao: bool = False) -> Doenca:
        nome = v.obrigatorio(nome, "Nome da doença")
        with transacao(self.conexao) as cur:
            cur.execute("""INSERT INTO doenca (nome, cid, impede_doacao)
                           VALUES (%s, %s, %s) RETURNING *""",
                        (nome, v.opcional(cid), bool(impede_doacao)))
            return Doenca.de_linha(cur.fetchone())

    def registrar_diagnostico(self, usuario_id: int, doenca_id: int,
                              data_diagnostico, status: str = "ativa") -> Diagnostico:
        data = v.nao_futura(v.para_data(data_diagnostico, "Data do diagnóstico"),
                            "Data do diagnóstico")
        status = v.validar_status_doenca(status)
        with transacao(self.conexao) as cur:
            cur.execute("""INSERT INTO usuario_doenca (usuario_id, doenca_id, data_diagnostico, status)
                           VALUES (%s, %s, %s, %s) RETURNING id""",
                        (usuario_id, doenca_id, data, status))
            novo_id = cur.fetchone()["id"]
            cur.execute(self._SELECT_DIAGNOSTICO + " WHERE ud.id = %s", (novo_id,))
            return Diagnostico.de_linha(cur.fetchone())

    def atualizar_status_doenca(self, diagnostico_id: int, status: str) -> Diagnostico:
        status = v.validar_status_doenca(status)
        with transacao(self.conexao) as cur:
            cur.execute("UPDATE usuario_doenca SET status = %s WHERE id = %s",
                        (status, diagnostico_id))
            if cur.rowcount == 0:
                raise NaoEncontrado(f"Diagnóstico {diagnostico_id} não encontrado.")
            cur.execute(self._SELECT_DIAGNOSTICO + " WHERE ud.id = %s", (diagnostico_id,))
            return Diagnostico.de_linha(cur.fetchone())

    def atualizar_gravidade_alergia(self, alergia_id: int, gravidade: str) -> Alergia:
        gravidade = v.validar_gravidade(gravidade)
        with transacao(self.conexao) as cur:
            cur.execute("""UPDATE alergia SET gravidade = %s WHERE id = %s
                           RETURNING *""", (gravidade, alergia_id))
            linha = cur.fetchone()
        if linha is None:
            raise NaoEncontrado(f"Alergia {alergia_id} não encontrada.")
        return Alergia.de_linha(linha)

    def listar_diagnosticos(self, usuario_id: int) -> list[Diagnostico]:
        with transacao(self.conexao) as cur:
            cur.execute(self._SELECT_DIAGNOSTICO +
                        " WHERE ud.usuario_id = %s ORDER BY ud.data_diagnostico", (usuario_id,))
            return [Diagnostico.de_linha(l) for l in cur.fetchall()]

    _SELECT_APLICACAO = """
        SELECT av.id, av.usuario_id, av.vacina_id, va.nome AS vacina, va.fabricante,
               av.data_aplicacao, av.dose, av.lote
          FROM aplicacao_vacina av JOIN vacina va ON va.id = av.vacina_id"""

    def listar_catalogo_vacinas(self) -> list[Vacina]:
        with transacao(self.conexao) as cur:
            cur.execute("SELECT * FROM vacina ORDER BY nome")
            return [Vacina.de_linha(l) for l in cur.fetchall()]

    def cadastrar_vacina(self, nome: str, fabricante: Optional[str] = None) -> Vacina:
        nome = v.obrigatorio(nome, "Nome da vacina")
        with transacao(self.conexao) as cur:
            cur.execute("""INSERT INTO vacina (nome, fabricante)
                           VALUES (%s, %s) RETURNING *""",
                        (nome, v.opcional(fabricante)))
            return Vacina.de_linha(cur.fetchone())

    def registrar_vacina(self, usuario_id: int, vacina_id: int, data_aplicacao,
                         dose: str, lote: Optional[str] = None) -> AplicacaoVacina:
        data = v.nao_futura(v.para_data(data_aplicacao, "Data da aplicação"), "Data da aplicação")
        dose = v.obrigatorio(dose, "Dose")
        with transacao(self.conexao) as cur:
            cur.execute("""INSERT INTO aplicacao_vacina (usuario_id, vacina_id, data_aplicacao, dose, lote)
                           VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                        (usuario_id, vacina_id, data, dose, v.opcional(lote)))
            novo_id = cur.fetchone()["id"]
            cur.execute(self._SELECT_APLICACAO + " WHERE av.id = %s", (novo_id,))
            return AplicacaoVacina.de_linha(cur.fetchone())

    def cartao_vacinacao(self, usuario_id: int) -> list[AplicacaoVacina]:
        with transacao(self.conexao) as cur:
            cur.execute(self._SELECT_APLICACAO +
                        " WHERE av.usuario_id = %s ORDER BY av.data_aplicacao", (usuario_id,))
            return [AplicacaoVacina.de_linha(l) for l in cur.fetchall()]

    def registrar_consulta(self, usuario_id: int, data_hora, especialidade: str,
                           profissional=None, local=None, observacoes=None) -> Consulta:
        quando = v.para_data_hora(data_hora, "Data/hora da consulta")
        with transacao(self.conexao) as cur:
            cur.execute("""INSERT INTO consulta (usuario_id, data_hora, especialidade,
                                                 profissional, local, observacoes)
                           VALUES (%s, %s, %s, %s, %s, %s) RETURNING *""",
                        (usuario_id, quando, v.obrigatorio(especialidade, "Especialidade"),
                         v.opcional(profissional), v.opcional(local), v.opcional(observacoes)))
            return Consulta.de_linha(cur.fetchone())

    def listar_consultas(self, usuario_id: int) -> list[Consulta]:
        with transacao(self.conexao) as cur:
            cur.execute("SELECT * FROM consulta WHERE usuario_id = %s ORDER BY data_hora",
                        (usuario_id,))
            return [Consulta.de_linha(l) for l in cur.fetchall()]

    def atualizar_consulta(self, consulta_id: int, observacoes: Optional[str]) -> Consulta:
        with transacao(self.conexao) as cur:
            cur.execute("""UPDATE consulta SET observacoes = %s WHERE id = %s
                           RETURNING *""", (v.opcional(observacoes), consulta_id))
            linha = cur.fetchone()
        if linha is None:
            raise NaoEncontrado(f"Consulta {consulta_id} não encontrada.")
        return Consulta.de_linha(linha)

    def registrar_exame(self, usuario_id: int, tipo: str, data, resultado=None,
                        consulta_id: Optional[int] = None) -> Exame:
        data = v.nao_futura(v.para_data(data, "Data do exame"), "Data do exame")
        with transacao(self.conexao) as cur:
            if consulta_id is not None:
                cur.execute("SELECT usuario_id FROM consulta WHERE id = %s", (consulta_id,))
                dono = cur.fetchone()
                if dono is None:
                    raise NaoEncontrado(f"Consulta {consulta_id} não encontrada.")
                if dono["usuario_id"] != usuario_id:
                    raise DadosInvalidos("A consulta informada pertence a outro usuário.")
            cur.execute("""INSERT INTO exame (usuario_id, consulta_id, tipo, data, resultado)
                           VALUES (%s, %s, %s, %s, %s) RETURNING *""",
                        (usuario_id, consulta_id, v.obrigatorio(tipo, "Tipo do exame"),
                         data, v.opcional(resultado)))
            return Exame.de_linha(cur.fetchone())

    def listar_exames(self, usuario_id: int) -> list[Exame]:
        with transacao(self.conexao) as cur:
            cur.execute("SELECT * FROM exame WHERE usuario_id = %s ORDER BY data", (usuario_id,))
            return [Exame.de_linha(l) for l in cur.fetchall()]

    def atualizar_resultado_exame(self, exame_id: int, resultado: str) -> Exame:
        resultado = v.obrigatorio(resultado, "Resultado")
        with transacao(self.conexao) as cur:
            cur.execute("""UPDATE exame SET resultado = %s WHERE id = %s
                           RETURNING *""", (resultado, exame_id))
            linha = cur.fetchone()
        if linha is None:
            raise NaoEncontrado(f"Exame {exame_id} não encontrado.")
        return Exame.de_linha(linha)

    def registrar_metrica(self, usuario_id: int, tipo: str, valor, unidade: str,
                          data_hora=None) -> Metrica:
        quando = v.para_data_hora(data_hora, "Data/hora") if data_hora else datetime.now()
        if quando > datetime.now():
            raise DadosInvalidos("A medição não pode estar no futuro.")
        with transacao(self.conexao) as cur:
            cur.execute("""INSERT INTO metrica_saude (usuario_id, tipo, valor, unidade, data_hora)
                           VALUES (%s, %s, %s, %s, %s) RETURNING *""",
                        (usuario_id, v.obrigatorio(tipo, "Tipo").lower(),
                         v.validar_valor_metrica(valor), v.obrigatorio(unidade, "Unidade"), quando))
            return Metrica.de_linha(cur.fetchone())

    def historico_metrica(self, usuario_id: int, tipo: str) -> list[Metrica]:
        with transacao(self.conexao) as cur:
            cur.execute("""SELECT * FROM metrica_saude WHERE usuario_id = %s AND tipo = %s
                            ORDER BY data_hora""", (usuario_id, tipo.lower()))
            serie = [Metrica.de_linha(l) for l in cur.fetchall()]
        for anterior, atual in zip(serie, serie[1:]):
            atual.variacao = round(atual.valor - anterior.valor, 2)
        return serie

    def metricas_por_tipo(self, usuario_id: int) -> dict[str, list[Metrica]]:
        with transacao(self.conexao) as cur:
            cur.execute("SELECT DISTINCT tipo FROM metrica_saude WHERE usuario_id = %s ORDER BY tipo",
                        (usuario_id,))
            tipos = [l["tipo"] for l in cur.fetchall()]
        return {tipo: self.historico_metrica(usuario_id, tipo) for tipo in tipos}

    def ultima_metrica(self, usuario_id: int, tipo: str) -> Optional[Metrica]:
        with transacao(self.conexao) as cur:
            cur.execute("""SELECT * FROM metrica_saude WHERE usuario_id = %s AND tipo = %s
                            ORDER BY data_hora DESC LIMIT 1""", (usuario_id, tipo.lower()))
            linha = cur.fetchone()
        return Metrica.de_linha(linha) if linha else None

    def ficha(self, usuario_id: int) -> FichaUsuario:
        with transacao(self.conexao) as cur:
            cur.execute("SELECT * FROM vw_ficha_usuario WHERE id = %s", (usuario_id,))
            linha = cur.fetchone()
        if linha is None:
            raise NaoEncontrado(f"Usuário {usuario_id} não encontrado no Diário.")
        return FichaUsuario.de_linha(linha)

    def linha_do_tempo(self, usuario_id: int) -> list[Evento]:
        with transacao(self.conexao) as cur:
            cur.execute("""SELECT data, evento, descricao FROM vw_linha_do_tempo
                            WHERE usuario_id = %s ORDER BY data, evento""", (usuario_id,))
            return [Evento.de_linha(l) for l in cur.fetchall()]

    def prontuario(self, usuario_id: int) -> Prontuario:
        return Prontuario(
            usuario=self.buscar_usuario(usuario_id),
            alergias=self.listar_alergias(usuario_id),
            diagnosticos=self.listar_diagnosticos(usuario_id),
            vacinas=self.cartao_vacinacao(usuario_id),
            consultas=self.listar_consultas(usuario_id),
            exames=self.listar_exames(usuario_id),
            metricas=self.metricas_por_tipo(usuario_id),
            linha_do_tempo=self.linha_do_tempo(usuario_id),
        )
