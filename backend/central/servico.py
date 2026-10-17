from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Optional

from backend.central import compatibilidade as compat
from backend.central.integracao_diario import DiarioGateway
from backend.central.modelos import (TIPOS_DOADOR, Alocacao, Bolsa, Doador,
                                     EntradaFila, Hospital, Orgao,
                                     OrgaoDisponivel, PosicaoFila, Processo,
                                     Receptor, ResultadoSelecao, TipoOrgao)
from backend.conexao import conectar_central
from backend.erros import DadosInvalidos, ErroDeNegocio, NaoEncontrado, transacao

VALIDADE_BOLSA_DIAS = 42


class CentralService:
    def __init__(self, conexao=None, diario: Optional[DiarioGateway] = None):
        self.conexao = conexao or conectar_central()
        self.diario = diario or DiarioGateway()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.fechar()

    def fechar(self):
        self.conexao.close()
        self.diario.fechar()

    def listar_hospitais(self) -> list[Hospital]:
        with transacao(self.conexao) as cur:
            cur.execute("SELECT * FROM hospital ORDER BY id")
            return [Hospital.de_linha(l) for l in cur.fetchall()]

    def listar_tipos_orgao(self) -> list[TipoOrgao]:
        with transacao(self.conexao) as cur:
            cur.execute("SELECT * FROM tipo_orgao ORDER BY id")
            return [TipoOrgao.de_linha(l) for l in cur.fetchall()]

    def _regras_abo(self, cur) -> frozenset:
        cur.execute("SELECT tipo_doador, tipo_receptor FROM compatibilidade_abo")
        return frozenset((l["tipo_doador"], l["tipo_receptor"]) for l in cur.fetchall())

    def cadastrar_receptor(self, usuario_id: int, hospital_id: int) -> Receptor:
        pessoa = self.diario.pessoa(usuario_id)
        if not pessoa.tem_tipagem:
            raise ErroDeNegocio(
                f"{pessoa.nome} não tem tipagem sanguínea no Diário. "
                "Registre o exame de tipagem antes de cadastrá-lo(a) como receptor.")
        with transacao(self.conexao) as cur:
            cur.execute("""INSERT INTO receptor (usuario_id, hospital_id)
                           VALUES (%s, %s) RETURNING *""", (usuario_id, hospital_id))
            receptor = Receptor.de_linha(cur.fetchone())
        receptor.nome = pessoa.nome
        return receptor

    def buscar_receptor_por_usuario(self, usuario_id: int) -> Optional[Receptor]:
        with transacao(self.conexao) as cur:
            cur.execute("SELECT * FROM receptor WHERE usuario_id = %s", (usuario_id,))
            linha = cur.fetchone()
        return Receptor.de_linha(linha) if linha else None

    def incluir_na_fila(self, receptor_id: int, tipo_orgao_id: int, urgencia: int) -> EntradaFila:
        urgencia = self._validar_urgencia(urgencia)
        with transacao(self.conexao) as cur:
            cur.execute("""INSERT INTO fila_espera (receptor_id, tipo_orgao_id, urgencia)
                           VALUES (%s, %s, %s) RETURNING *""",
                        (receptor_id, tipo_orgao_id, urgencia))
            return EntradaFila.de_linha(cur.fetchone())

    def atualizar_urgencia(self, fila_id: int, urgencia: int) -> EntradaFila:
        urgencia = self._validar_urgencia(urgencia)
        with transacao(self.conexao) as cur:
            cur.execute("""UPDATE fila_espera SET urgencia = %s
                            WHERE id = %s AND status = 'aguardando' RETURNING *""",
                        (urgencia, fila_id))
            linha = cur.fetchone()
        if linha is None:
            raise NaoEncontrado(f"Não há posição AGUARDANDO com id {fila_id} na fila.")
        return EntradaFila.de_linha(linha)

    def remover_da_fila(self, fila_id: int) -> EntradaFila:
        with transacao(self.conexao) as cur:
            cur.execute("""SELECT 1 FROM alocacao
                            WHERE fila_id = %s AND status_logistica <> 'cancelado'
                              AND status_logistica <> 'realizado'""", (fila_id,))
            if cur.fetchone():
                raise ErroDeNegocio("Há um órgão a caminho deste receptor: cancele a alocação antes.")
            cur.execute("""UPDATE fila_espera SET status = 'removido'
                            WHERE id = %s AND status = 'aguardando' RETURNING *""", (fila_id,))
            linha = cur.fetchone()
        if linha is None:
            raise NaoEncontrado(f"Não há posição AGUARDANDO com id {fila_id} na fila.")
        return EntradaFila.de_linha(linha)

    def fila_ativa(self, tipo_orgao_id: Optional[int] = None) -> list[PosicaoFila]:
        with transacao(self.conexao) as cur:
            if tipo_orgao_id:
                cur.execute("""SELECT v.* FROM vw_fila_ativa v
                                 JOIN fila_espera f ON f.id = v.fila_id
                                WHERE f.tipo_orgao_id = %s ORDER BY v.posicao""", (tipo_orgao_id,))
            else:
                cur.execute("SELECT * FROM vw_fila_ativa ORDER BY orgao, posicao")
            fila = [PosicaoFila.de_linha(l) for l in cur.fetchall()]
        pessoas = self.diario.pessoas(p.receptor_usuario_id for p in fila)
        for p in fila:
            pessoa = pessoas.get(p.receptor_usuario_id)
            p.nome = pessoa.nome if pessoa else "(fora do Diário)"
            p.sangue = pessoa.sangue if pessoa else None
        return fila

    @staticmethod
    def _validar_urgencia(urgencia) -> int:
        try:
            urgencia = int(urgencia)
        except (TypeError, ValueError):
            raise DadosInvalidos("A urgência deve ser um número de 1 a 5.") from None
        if not 1 <= urgencia <= 5:
            raise DadosInvalidos("A urgência deve estar entre 1 e 5.")
        return urgencia

    def cadastrar_doador(self, usuario_id: int, tipo: str, hospital_id: int) -> Doador:
        if tipo not in TIPOS_DOADOR:
            raise DadosInvalidos("Tipo de doador deve ser 'vivo' ou 'falecido'.")
        pessoa = self.diario.pessoa(usuario_id)
        if not pessoa.tem_tipagem:
            raise ErroDeNegocio(f"{pessoa.nome} não tem tipagem sanguínea no Diário.")
        restricoes = self.diario.restricoes_doacao(usuario_id)
        status = "inapto" if restricoes else "apto"
        with transacao(self.conexao) as cur:
            cur.execute("""INSERT INTO doador (usuario_id, tipo, hospital_id, status)
                           VALUES (%s, %s, %s, %s) RETURNING *""",
                        (usuario_id, tipo, hospital_id, status))
            doador = Doador.de_linha(cur.fetchone())
        doador.nome = pessoa.nome
        doador.motivo_inaptidao = "; ".join(restricoes) or None
        return doador

    def listar_doadores(self) -> list[Doador]:
        with transacao(self.conexao) as cur:
            cur.execute("SELECT * FROM doador ORDER BY id")
            doadores = [Doador.de_linha(l) for l in cur.fetchall()]
        pessoas = self.diario.pessoas(d.usuario_id for d in doadores)
        for d in doadores:
            d.nome = pessoas[d.usuario_id].nome if d.usuario_id in pessoas else "(fora do Diário)"
        return doadores

    def reavaliar_doadores(self) -> list[tuple[Doador, str, str]]:
        mudancas = []
        for doador in self.listar_doadores():
            restricoes = self.diario.restricoes_doacao(doador.usuario_id)
            novo = "inapto" if restricoes else "apto"
            if novo != doador.status:
                with transacao(self.conexao) as cur:
                    cur.execute("UPDATE doador SET status = %s WHERE id = %s", (novo, doador.id))
                mudancas.append((doador, doador.status, novo))
                doador.status = novo
                doador.motivo_inaptidao = "; ".join(restricoes) or None
        return mudancas

    def registrar_orgao(self, doador_id: int, tipo_orgao_id: int,
                        hospital_id: Optional[int] = None,
                        data_hora_captacao: Optional[datetime] = None) -> Orgao:
        with transacao(self.conexao) as cur:
            cur.execute("SELECT * FROM doador WHERE id = %s", (doador_id,))
            linha = cur.fetchone()
        if linha is None:
            raise NaoEncontrado(f"Doador {doador_id} não encontrado.")
        doador = Doador.de_linha(linha)

        restricoes = self.diario.restricoes_doacao(doador.usuario_id)
        if restricoes and doador.status == "apto":
            with transacao(self.conexao) as cur:
                cur.execute("UPDATE doador SET status = 'inapto' WHERE id = %s", (doador_id,))
            raise ErroDeNegocio("Doador passou a INAPTO pelo histórico do Diário: "
                                + "; ".join(restricoes))

        with transacao(self.conexao) as cur:
            cur.execute("""INSERT INTO orgao_disponivel
                               (doador_id, tipo_orgao_id, hospital_id, data_hora_captacao)
                           VALUES (%s, %s, %s, COALESCE(%s, NOW())) RETURNING *""",
                        (doador_id, tipo_orgao_id, hospital_id or doador.hospital_id,
                         data_hora_captacao))
            return Orgao.de_linha(cur.fetchone())

    def orgaos_disponiveis(self) -> list[OrgaoDisponivel]:
        with transacao(self.conexao) as cur:
            cur.execute("SELECT * FROM vw_orgaos_disponiveis ORDER BY horas_restantes")
            orgaos = [OrgaoDisponivel.de_linha(l) for l in cur.fetchall()]
        pessoas = self.diario.pessoas(o.doador_usuario_id for o in orgaos)
        for o in orgaos:
            pessoa = pessoas.get(o.doador_usuario_id)
            o.doador_nome = pessoa.nome if pessoa else "(fora do Diário)"
            o.doador_sangue = pessoa.sangue if pessoa else None
        return orgaos

    def selecionar_receptores(self, orgao_id: int) -> ResultadoSelecao:
        with transacao(self.conexao) as cur:
            cur.execute("""
                SELECT od.id, od.status, od.tipo_orgao_id, t.nome AS tipo_orgao,
                       d.usuario_id AS doador_usuario_id, h.nome AS hospital,
                       h.latitude, h.longitude,
                       EXTRACT(EPOCH FROM (od.data_hora_captacao
                             + t.tempo_max_isquemia_horas * INTERVAL '1 hour' - NOW())) / 3600
                           AS horas_restantes
                  FROM orgao_disponivel od
                  JOIN doador d     ON d.id = od.doador_id
                  JOIN tipo_orgao t ON t.id = od.tipo_orgao_id
                  JOIN hospital h   ON h.id = od.hospital_id
                 WHERE od.id = %s""", (orgao_id,))
            orgao = cur.fetchone()
            if orgao is None:
                raise NaoEncontrado(f"Órgão {orgao_id} não encontrado.")
            if orgao["status"] != "disponivel":
                raise ErroDeNegocio(f"Órgão {orgao_id} não está disponível (status: {orgao['status']}).")
            if orgao["horas_restantes"] <= 0:
                raise ErroDeNegocio(f"Órgão {orgao_id} excedeu o tempo máximo de isquemia.")

            cur.execute("""
                SELECT f.id AS fila_id, r.id AS receptor_id, r.usuario_id,
                       h.nome AS hospital, h.latitude, h.longitude, f.urgencia,
                       CURRENT_DATE - f.data_entrada::DATE AS dias_espera
                  FROM fila_espera f
                  JOIN receptor r ON r.id = f.receptor_id
                  JOIN hospital h ON h.id = r.hospital_id
                 WHERE f.tipo_orgao_id = %s
                   AND f.status = 'aguardando'
                   AND r.usuario_id <> %s
                   AND NOT EXISTS (SELECT 1 FROM alocacao a
                                    WHERE a.fila_id = f.id
                                      AND a.status_logistica <> 'cancelado')""",
                        (orgao["tipo_orgao_id"], orgao["doador_usuario_id"]))
            fila = cur.fetchall()
            regras = self._regras_abo(cur)

        pessoas = self.diario.pessoas([orgao["doador_usuario_id"]] + [f["usuario_id"] for f in fila])
        doador = pessoas.get(orgao["doador_usuario_id"])
        if doador is None or not doador.tem_tipagem:
            raise ErroDeNegocio("O doador não tem tipagem sanguínea válida no Diário.")

        oferta = compat.OfertaOrgao(
            orgao_id=orgao["id"], tipo_orgao=orgao["tipo_orgao"],
            doador_usuario_id=doador.id, doador_nome=doador.nome,
            doador_sangue=doador.tipo_sanguineo, hospital=orgao["hospital"],
            latitude=float(orgao["latitude"]), longitude=float(orgao["longitude"]),
            horas_restantes=round(float(orgao["horas_restantes"]), 2))

        pedidos = []
        for f in fila:
            pessoa = pessoas.get(f["usuario_id"])
            pedidos.append(compat.PedidoFila(
                fila_id=f["fila_id"], receptor_id=f["receptor_id"], usuario_id=f["usuario_id"],
                nome=pessoa.nome if pessoa else "(fora do Diário)",
                tipo_sanguineo=pessoa.tipo_sanguineo if pessoa else None,
                fator_rh=pessoa.fator_rh if pessoa else None,
                hospital=f["hospital"], latitude=float(f["latitude"]),
                longitude=float(f["longitude"]), urgencia=f["urgencia"],
                dias_espera=f["dias_espera"]))

        return ResultadoSelecao(oferta=oferta, candidatos=compat.ranquear(oferta, pedidos, regras))

    def alocar_orgao(self, orgao_id: int, fila_id: int) -> Alocacao:
        resultado = self.selecionar_receptores(orgao_id)
        candidato = next((c for c in resultado.candidatos if c.pedido.fila_id == fila_id), None)
        if candidato is None:
            raise ErroDeNegocio(f"A posição {fila_id} da fila não é candidata a este órgão "
                                "(outro tipo de órgão, fora da fila ou já com órgão alocado).")
        if not candidato.elegivel:
            raise ErroDeNegocio(f"Alocação recusada para {candidato.pedido.nome}: "
                                f"{candidato.motivo_exclusao}.")
        with transacao(self.conexao) as cur:
            cur.execute("SELECT fn_alocar_orgao(%s, %s) AS id", (orgao_id, fila_id))
            alocacao_id = cur.fetchone()["id"]
        return self.buscar_alocacao(alocacao_id)

    def alocar_melhor_receptor(self, orgao_id: int):
        resultado = self.selecionar_receptores(orgao_id)
        if resultado.indicado is None:
            raise ErroDeNegocio("Nenhum receptor elegível para este órgão no momento.")
        return self.alocar_orgao(orgao_id, resultado.indicado.pedido.fila_id), resultado.indicado

    def buscar_alocacao(self, alocacao_id: int) -> Alocacao:
        with transacao(self.conexao) as cur:
            cur.execute("SELECT * FROM alocacao WHERE id = %s", (alocacao_id,))
            linha = cur.fetchone()
        if linha is None:
            raise NaoEncontrado(f"Alocação {alocacao_id} não encontrada.")
        return Alocacao.de_linha(linha)

    def _executar_etapa(self, funcao_sql: str, alocacao_id: int) -> Alocacao:
        with transacao(self.conexao) as cur:
            cur.execute(f"SELECT {funcao_sql}(%s)", (alocacao_id,))
        return self.buscar_alocacao(alocacao_id)

    def registrar_entrega(self, alocacao_id: int) -> Alocacao:
        return self._executar_etapa("fn_registrar_entrega", alocacao_id)

    def concluir_transplante(self, alocacao_id: int) -> Alocacao:
        return self._executar_etapa("fn_concluir_transplante", alocacao_id)

    def cancelar_alocacao(self, alocacao_id: int) -> Alocacao:
        return self._executar_etapa("fn_cancelar_alocacao", alocacao_id)

    def processos(self) -> list[Processo]:
        with transacao(self.conexao) as cur:
            cur.execute("SELECT * FROM vw_processos ORDER BY alocacao_id")
            processos = [Processo.de_linha(l) for l in cur.fetchall()]
        pessoas = self.diario.pessoas(
            [p.doador_usuario_id for p in processos] + [p.receptor_usuario_id for p in processos])
        for p in processos:
            p.doador_nome = getattr(pessoas.get(p.doador_usuario_id), "nome", "(fora do Diário)")
            p.receptor_nome = getattr(pessoas.get(p.receptor_usuario_id), "nome", "(fora do Diário)")
        return processos

    def registrar_doacao_sangue(self, usuario_id: int, hospital_id: int,
                                volume_ml: int = 450, data_coleta: Optional[date] = None) -> Bolsa:
        data_coleta = data_coleta or date.today()
        pessoa = self.diario.pessoa(usuario_id)
        if not pessoa.tem_tipagem:
            raise ErroDeNegocio(f"{pessoa.nome} não tem tipagem sanguínea no Diário.")

        with transacao(self.conexao) as cur:
            cur.execute("SELECT MAX(data_coleta) AS ultima FROM bolsa_sangue WHERE usuario_id = %s",
                        (usuario_id,))
            ultima = cur.fetchone()["ultima"]
        motivos = compat.motivos_inaptidao_sangue(
            idade=pessoa.idade, sexo=pessoa.sexo,
            peso_kg=self.diario.ultimo_peso(usuario_id),
            dias_desde_ultima=(data_coleta - ultima).days if ultima else None,
            restricoes_clinicas=self.diario.restricoes_doacao(usuario_id))
        if motivos:
            raise ErroDeNegocio(f"Doação de sangue recusada para {pessoa.nome}: " + "; ".join(motivos) + ".")

        with transacao(self.conexao) as cur:
            cur.execute("""INSERT INTO bolsa_sangue (usuario_id, hospital_id, data_coleta,
                                                     data_validade, volume_ml)
                           VALUES (%s, %s, %s, %s, %s) RETURNING *""",
                        (usuario_id, hospital_id, data_coleta,
                         data_coleta + timedelta(days=VALIDADE_BOLSA_DIAS), volume_ml))
            bolsa = Bolsa.de_linha(cur.fetchone())
        bolsa.sangue = pessoa.sangue
        return bolsa

    def _bolsas_disponiveis(self, hospital_id: Optional[int] = None) -> list[Bolsa]:
        with transacao(self.conexao) as cur:
            cur.execute("""SELECT b.*, h.nome AS hospital
                             FROM bolsa_sangue b JOIN hospital h ON h.id = b.hospital_id
                            WHERE b.status = 'disponivel' AND b.data_validade >= CURRENT_DATE
                              AND (%(h)s::INT IS NULL OR b.hospital_id = %(h)s::INT)
                            ORDER BY b.data_validade""", {"h": hospital_id})
            bolsas = [Bolsa.de_linha(l) for l in cur.fetchall()]
        pessoas = self.diario.pessoas(b.usuario_id for b in bolsas)
        for b in bolsas:
            b.sangue = getattr(pessoas.get(b.usuario_id), "sangue", None)
        return bolsas

    def estoque_sangue(self, hospital_id: Optional[int] = None) -> dict[str, dict]:
        estoque = defaultdict(lambda: {"bolsas": 0, "volume_ml": 0})
        for bolsa in self._bolsas_disponiveis(hospital_id):
            chave = bolsa.sangue or "sem tipagem"
            estoque[chave]["bolsas"] += 1
            estoque[chave]["volume_ml"] += bolsa.volume_ml
        return dict(sorted(estoque.items()))

    def bolsas_compativeis(self, receptor_usuario_id: int,
                           hospital_id: Optional[int] = None) -> list[Bolsa]:
        receptor = self.diario.pessoa(receptor_usuario_id)
        if not receptor.tem_tipagem:
            raise ErroDeNegocio(f"{receptor.nome} não tem tipagem sanguínea no Diário.")
        with transacao(self.conexao) as cur:
            regras = self._regras_abo(cur)
        bolsas = self._bolsas_disponiveis(hospital_id)
        doadores = self.diario.pessoas(b.usuario_id for b in bolsas)
        return [b for b in bolsas
                if b.usuario_id in doadores and doadores[b.usuario_id].tem_tipagem
                and compat.sangue_compativel(doadores[b.usuario_id].tipo_sanguineo,
                                             doadores[b.usuario_id].fator_rh,
                                             receptor.tipo_sanguineo, receptor.fator_rh, regras)]

    def utilizar_bolsa(self, bolsa_id: int, receptor_usuario_id: int) -> Bolsa:
        compativeis = {b.id for b in self.bolsas_compativeis(receptor_usuario_id)}
        if bolsa_id not in compativeis:
            raise ErroDeNegocio(f"A bolsa {bolsa_id} não está disponível ou não é compatível "
                                "com o receptor.")
        with transacao(self.conexao) as cur:
            cur.execute("""UPDATE bolsa_sangue SET status = 'utilizada'
                            WHERE id = %s AND status = 'disponivel' RETURNING *""", (bolsa_id,))
            linha = cur.fetchone()
        if linha is None:
            raise ErroDeNegocio(f"A bolsa {bolsa_id} acabou de ser utilizada.")
        return Bolsa.de_linha(linha)

    def executar_manutencao(self) -> dict:
        with transacao(self.conexao) as cur:
            cur.execute("SELECT fn_atualizar_bolsas_vencidas() AS n")
            bolsas = cur.fetchone()["n"]
            cur.execute("SELECT fn_descartar_orgaos_expirados() AS n")
            orgaos = cur.fetchone()["n"]
        return {"bolsas_vencidas": bolsas, "orgaos_descartados": orgaos}

    def verificar_integridade(self) -> list[tuple[str, int]]:
        with transacao(self.conexao) as cur:
            cur.execute("""SELECT 'doador' AS origem, usuario_id FROM doador
                           UNION SELECT 'receptor', usuario_id FROM receptor
                           UNION SELECT 'bolsa_sangue', usuario_id FROM bolsa_sangue""")
            referencias = cur.fetchall()
        existentes = self.diario.ids_existentes(r["usuario_id"] for r in referencias)
        return sorted((r["origem"], r["usuario_id"]) for r in referencias
                      if r["usuario_id"] not in existentes)
