# -*- coding: utf-8 -*-
"""API HTTP do front web integrada aos serviços PostgreSQL."""

import json
import re
import sys
import traceback
from dataclasses import asdict, is_dataclass
from datetime import date, timedelta
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from backend.central import compatibilidade as compat
from backend.central.modelos import TIPOS_DOADOR
from backend.central.servico import CentralService
from backend.diario.modelos import (FATORES_RH, GRAVIDADES_ALERGIA, SEXOS,
                                    STATUS_DOENCA, TIPOS_SANGUINEOS)
from backend.diario.servico import DiarioService
from backend.erros import ErroDeNegocio

PASTA_WEB = RAIZ / "web"


class ErroHTTP(Exception):
    def __init__(self, codigo, mensagem):
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem


def _json(valor):
    if is_dataclass(valor):
        return asdict(valor)
    if isinstance(valor, (list, tuple)):
        return [_json(item) for item in valor]
    if isinstance(valor, dict):
        return {chave: _json(item) for chave, item in valor.items()}
    return valor


def _usuario(usuario):
    return {**_json(usuario), "idade": usuario.idade, "sangue": usuario.sangue}


def _exigir(corpo, *campos):
    faltando = [campo for campo in campos if corpo.get(campo) in (None, "")]
    if faltando:
        raise ErroHTTP(400, "Campos obrigatórios ausentes: " + ", ".join(faltando))


def _prioridade(valor):
    if isinstance(valor, str):
        rotulos = {"baixa": 1, "normal": 3, "alta": 4, "emergencia": 5}
        if valor.lower() in rotulos:
            return rotulos[valor.lower()]
    return int(valor)


def _perfil(servico, usuario_id):
    diagnosticos = servico.listar_diagnosticos(usuario_id)
    impedimentos = [d.doenca for d in diagnosticos if d.impede_doacao and d.status != "curada"]
    return {"impedimentos": len(impedimentos),
            "doencas_impeditivas": ", ".join(impedimentos)}


def _metricas(servico, usuario_id):
    return {tipo: serie for tipo, serie in servico.metricas_por_tipo(usuario_id).items()}


def _diario(metodo, partes, query, corpo, s):
    if metodo == "GET":
        if partes == ["usuarios"]:
            busca = query.get("busca", [""])[0].strip() or None
            return [_usuario(u) for u in s.listar_usuarios(busca)]
        if partes == ["resumo"]:
            usuarios = s.listar_usuarios()
            consultas = exames = doses = alergias = diagnosticos = impedidos = 0
            exames_pendentes = 0
            for u in usuarios:
                consultas += len(s.listar_consultas(u.id))
                lista_exames = s.listar_exames(u.id)
                exames += len(lista_exames)
                exames_pendentes += sum(e.resultado is None for e in lista_exames)
                doses += len(s.cartao_vacinacao(u.id))
                alergias += sum(a.gravidade in ("grave", "moderada")
                                for a in s.listar_alergias(u.id))
                ds = s.listar_diagnosticos(u.id)
                diagnosticos += len(ds)
                impedidos += any(d.impede_doacao and d.status != "curada" for d in ds)
            return {"usuarios": len(usuarios), "consultas": consultas, "exames": exames,
                    "exames_sem_resultado": exames_pendentes, "doses_aplicadas": doses,
                    "alergias_graves": alergias, "diagnosticos": diagnosticos,
                    "com_impedimento": impedidos}
        if partes == ["doencas"]:
            return _json(s.listar_catalogo_doencas())
        if partes == ["vacinas"]:
            return _json(s.listar_catalogo_vacinas())
        if partes == ["relatorios"]:
            alergias = []
            impedimentos = []
            pendentes = []
            distribuicao = {}
            especialidades = {}
            cobertura = {}
            perfil = []
            usuarios = s.listar_usuarios()
            for u in usuarios:
                alergias_usuario = [a.substancia for a in s.listar_alergias(u.id)
                                    if a.gravidade in ("grave", "moderada")]
                perfil.append({
                    "usuario_id": u.id, "nome": u.nome, "sangue": u.sangue,
                    **_perfil(s, u.id), "alergias_graves": ", ".join(alergias_usuario),
                })
                distribuicao[u.sangue] = distribuicao.get(u.sangue, 0) + 1
                for a in s.listar_alergias(u.id):
                    if a.gravidade in ("grave", "moderada"):
                        alergias.append({"usuario": u.nome, "substancia": a.substancia,
                                         "gravidade": a.gravidade})
                for d in s.listar_diagnosticos(u.id):
                    if d.impede_doacao and d.status != "curada":
                        impedimentos.append({"usuario": u.nome, "doenca": d.doenca,
                                             "cid": d.cid, "status": d.status})
                for e in s.listar_exames(u.id):
                    if not e.resultado:
                        pendentes.append({"usuario": u.nome, "tipo": e.tipo, "data": e.data})
                for dose in s.cartao_vacinacao(u.id):
                    v = cobertura.setdefault(dose.vacina, {
                        "vacina": dose.vacina, "usuarios": set(), "doses": 0,
                        "ultima_aplicacao": dose.data_aplicacao})
                    v["usuarios"].add(u.id)
                    v["doses"] += 1
                    v["ultima_aplicacao"] = max(v["ultima_aplicacao"], dose.data_aplicacao)
                for c in s.listar_consultas(u.id):
                    atual = especialidades.setdefault(c.especialidade, {
                        "total": 0, "ultima": c.data_hora})
                    atual["total"] += 1
                    atual["ultima"] = max(atual["ultima"], c.data_hora)
            return {
                "alergias_graves": alergias, "impedimentos": impedimentos,
                "exames_sem_resultado": pendentes,
                "cobertura_vacinal": [{**v, "usuarios": len(v["usuarios"])}
                                      for v in cobertura.values()],
                "distribuicao_sanguinea": [
                    {"sangue": k, "usuarios": n} for k, n in sorted(distribuicao.items())],
                "consultas_por_especialidade": [
                    {"especialidade": k, **v} for k, v in sorted(especialidades.items())],
                "perfil_doacao": perfil,
            }
        if len(partes) == 2 and partes[0] == "usuarios":
            usuario_id = int(partes[1])
            return {"usuario": _usuario(s.buscar_usuario(usuario_id)),
                    "perfil": _perfil(s, usuario_id)}
        if len(partes) == 3 and partes[0] == "usuarios":
            usuario_id, nome = int(partes[1]), partes[2]
            if nome == "alergias":
                return _json(s.listar_alergias(usuario_id))
            if nome == "doencas":
                return _json(s.listar_diagnosticos(usuario_id))
            if nome == "consultas":
                return _json(s.listar_consultas(usuario_id))
            if nome == "exames":
                return [{**_json(e), "consulta_origem": e.consulta_id}
                        for e in s.listar_exames(usuario_id)]
            if nome == "vacinas":
                return _json(s.cartao_vacinacao(usuario_id))
            if nome == "metricas":
                return [item for serie in _metricas(s, usuario_id).values()
                        for item in _json(serie)]
            if nome == "metricas-resumo":
                resultado = []
                for tipo, serie in _metricas(s, usuario_id).items():
                    resultado.append({
                        "tipo": tipo, "medicoes": len(serie),
                        "minimo": min(m.valor for m in serie),
                        "maximo": max(m.valor for m in serie),
                        "media": round(sum(m.valor for m in serie) / len(serie), 2),
                        "unidade": serie[-1].unidade, "ultima": serie[-1].data_hora,
                    })
                return resultado
            if nome == "timeline":
                return _json(s.linha_do_tempo(usuario_id))
            raise ErroHTTP(404, "Coleção desconhecida: " + nome)

    if metodo == "POST":
        if partes == ["usuarios"]:
            _exigir(corpo, "nome", "cpf", "data_nascimento", "sexo")
            novo = s.cadastrar_usuario(
                corpo["nome"], corpo["cpf"], corpo["data_nascimento"], corpo["sexo"],
                corpo.get("tipo_sanguineo"), corpo.get("fator_rh"), corpo.get("cidade"),
                corpo.get("uf"), corpo.get("email"), corpo.get("telefone"))
            return {"id": novo.id}
        if partes == ["doencas"]:
            _exigir(corpo, "nome")
            return {"id": s.cadastrar_doenca(
                corpo["nome"], corpo.get("cid"), bool(corpo.get("impede_doacao"))).id}
        if partes == ["vacinas"]:
            _exigir(corpo, "nome")
            return {"id": s.cadastrar_vacina(corpo["nome"], corpo.get("fabricante")).id}
        if len(partes) == 3 and partes[0] == "usuarios":
            usuario_id, nome = int(partes[1]), partes[2]
            if nome == "alergias":
                _exigir(corpo, "substancia", "gravidade")
                registro = s.adicionar_alergia(usuario_id, corpo["substancia"],
                                               corpo["gravidade"], corpo.get("observacao"))
            elif nome == "doencas":
                _exigir(corpo, "doenca_id", "data_diagnostico", "status")
                registro = s.registrar_diagnostico(
                    usuario_id, int(corpo["doenca_id"]), corpo["data_diagnostico"],
                    corpo["status"])
            elif nome == "consultas":
                _exigir(corpo, "data_hora", "especialidade")
                registro = s.registrar_consulta(
                    usuario_id, corpo["data_hora"], corpo["especialidade"],
                    corpo.get("profissional"), corpo.get("local"), corpo.get("observacoes"))
            elif nome == "exames":
                _exigir(corpo, "tipo", "data")
                registro = s.registrar_exame(
                    usuario_id, corpo["tipo"], corpo["data"], corpo.get("resultado"),
                    int(corpo["consulta_id"]) if corpo.get("consulta_id") else None)
            elif nome == "vacinas":
                _exigir(corpo, "vacina_id", "data_aplicacao", "dose")
                registro = s.registrar_vacina(
                    usuario_id, int(corpo["vacina_id"]), corpo["data_aplicacao"],
                    corpo["dose"], corpo.get("lote"))
            elif nome == "metricas":
                _exigir(corpo, "tipo", "valor", "unidade", "data_hora")
                registro = s.registrar_metrica(
                    usuario_id, corpo["tipo"], corpo["valor"], corpo["unidade"],
                    corpo["data_hora"])
            else:
                raise ErroHTTP(404, "Coleção desconhecida: " + nome)
            return {"id": registro.id}

    if metodo == "PATCH" and len(partes) == 2:
        identificador, alvo = int(partes[1]), partes[0]
        if alvo == "usuarios":
            campos_permitidos = {"nome", "data_nascimento", "sexo", "tipo_sanguineo",
                                 "fator_rh", "cidade", "uf", "email", "telefone"}
            campos = {k: v for k, v in corpo.items() if k in campos_permitidos}
            if not campos:
                raise ErroHTTP(400, "Informe os campos do usuário a atualizar.")
            return {"atualizado": s.atualizar_usuario(identificador, **campos).id}
        if alvo == "alergias":
            _exigir(corpo, "gravidade")
            return {"atualizado": s.atualizar_gravidade_alergia(
                identificador, corpo["gravidade"]).id}
        if alvo == "diagnosticos":
            _exigir(corpo, "status")
            return {"atualizado": s.atualizar_status_doenca(
                identificador, corpo["status"]).id}
        if alvo == "consultas":
            return {"atualizado": s.atualizar_consulta(
                identificador, corpo.get("observacoes")).id}
        if alvo == "exames":
            _exigir(corpo, "resultado")
            return {"atualizado": s.atualizar_resultado_exame(
                identificador, corpo["resultado"]).id}
    raise ErroHTTP(404, "Rota do Diário não encontrada.")


def _prioridade_label(valor):
    return {1: "baixa", 2: "normal", 3: "normal", 4: "alta", 5: "emergencia"}.get(
        int(valor), str(valor))


def _fila_item(item):
    return {"fila_id": item.fila_id, "receptor": item.nome,
            "receptor_usuario_id": item.receptor_usuario_id, "sangue": item.sangue,
            "orgao": item.orgao, "prioridade": _prioridade_label(item.urgencia),
            "urgencia": item.urgencia, "data_entrada": item.entrada,
            "dias_na_fila": item.dias_espera, "status": "aguardando",
            "hospital": item.hospital}


def _candidato(c):
    return {"fila_id": c.pedido.fila_id, "receptor": c.pedido.nome,
            "sangue_receptor": c.sangue, "prioridade": _prioridade_label(c.pedido.urgencia),
            "data_entrada": date.today() - timedelta(days=c.pedido.dias_espera),
            "dias_na_fila": c.pedido.dias_espera,
            "hospital_receptor": c.pedido.hospital, "distancia_km": c.distancia_km,
            "tempo_transporte_h": c.tempo_transporte_h,
            "motivo_exclusao": c.motivo_exclusao, "elegivel": c.elegivel}


def _orgaos(central, status=""):
    return central.listar_orgaos(status or None)


def _cruzamentos(central):
    resultado = []
    for orgao in central.orgaos_disponiveis():
        selecao = central.selecionar_receptores(orgao.orgao_id)
        for c in selecao.elegiveis:
            resultado.append({
                "orgao": orgao.orgao, "doador": orgao.doador_nome,
                "sangue_doador": orgao.doador_sangue, "receptor": c.pedido.nome,
                "sangue_receptor": c.sangue, "prioridade": _prioridade_label(c.pedido.urgencia),
                "dias_na_fila": c.pedido.dias_espera,
            })
    return resultado


def _painel(central):
    doadores = central.listar_doadores()
    receptores = central.listar_receptores()
    orgaos = central.listar_orgaos()
    fila = central.fila_ativa()
    processos = central.processos()
    return {
        "doadores": len(doadores), "receptores": len(receptores),
        "orgaos_disponiveis": sum(o["status"] == "disponivel" for o in orgaos),
        "orgaos_reservados": 0, "na_fila": len(fila),
        "emergencias": sum(f.urgencia == 5 for f in fila),
        "transplantes": sum(p.status_logistica == "realizado" for p in processos),
        "cruzamentos_compativeis": len(_cruzamentos(central)),
    }


def _demanda(central):
    fila, orgaos = central.fila_ativa(), central.listar_orgaos("disponivel")
    resultado = []
    for tipo in central.listar_tipos_orgao():
        entradas = [f for f in fila if f.orgao == tipo.nome]
        resultado.append({
            "orgao": tipo.nome, "aguardando": len(entradas),
            "emergencias": sum(f.urgencia == 5 for f in entradas),
            "media_dias": round(sum(f.dias_espera for f in entradas) / len(entradas), 1)
                if entradas else 0,
            "disponiveis": sum(o["tipo_orgao_id"] == tipo.id for o in orgaos),
        })
    return resultado


def _candidatos_resumo(central):
    return [{
        "orgao_id": o.orgao_id, "orgao": o.orgao,
        "sangue_doador": o.doador_sangue, "data_captacao": o.data_hora_captacao,
        "candidatos": len(central.selecionar_receptores(o.orgao_id).elegiveis),
    } for o in central.orgaos_disponiveis()]


def _sem_compativel(central):
    fila = central.fila_ativa()
    aptos = {c.pedido.fila_id for orgao in central.orgaos_disponiveis()
             for c in central.selecionar_receptores(orgao.orgao_id).elegiveis}
    return [{"receptor": f.nome, "sangue": f.sangue, "orgao": f.orgao,
             "prioridade": _prioridade_label(f.urgencia), "dias_na_fila": f.dias_espera}
            for f in fila if f.fila_id not in aptos]


def _integracao_usuarios(central):
    doadores = {d.usuario_id for d in central.listar_doadores()}
    receptores = {r.usuario_id for r in central.listar_receptores()}
    resultado = []
    with DiarioService() as diario:
        for u in diario.listar_usuarios():
            impedimentos = central.diario.restricoes_doacao(u.id)
            resultado.append({
                "usuario_id": u.id, "nome": u.nome, "sangue": u.sangue,
                "cidade": u.cidade, "impedimentos": len(impedimentos),
                "doencas_impeditivas": ", ".join(impedimentos),
                "e_doador": u.id in doadores, "e_receptor": u.id in receptores,
            })
    return resultado


def _central(metodo, partes, query, corpo, s):
    if metodo == "GET":
        if partes == ["painel"]:
            return _painel(s)
        if partes == ["hospitais"]:
            return _json(s.listar_hospitais())
        if partes == ["tipos-orgao"]:
            return [{**_json(t), "tempo_isquemia_horas": t.tempo_max_isquemia_horas}
                    for t in s.listar_tipos_orgao()]
        if partes == ["doadores"]:
            hospitais = {h.id: h.nome for h in s.listar_hospitais()}
            orgaos = s.listar_orgaos()
            resultado = []
            for d in s.listar_doadores():
                pessoa = s.diario.pessoa(d.usuario_id)
                resultado.append({
                    **_json(d), "tipo_doador": d.tipo, "sangue": pessoa.sangue,
                    "hospital": hospitais.get(d.hospital_id), "data_registro": d.data_cadastro,
                    "usuario_diario_id": d.usuario_id,
                    "orgaos": sum(o["doador_id"] == d.id for o in orgaos),
                })
            return resultado
        if partes == ["receptores"]:
            hospitais = {h.id: h.nome for h in s.listar_hospitais()}
            fila = s.fila_ativa()
            resultado = []
            for r in s.listar_receptores():
                pessoa = s.diario.pessoa(r.usuario_id)
                resultado.append({
                    **_json(r), "sangue": pessoa.sangue,
                    "usuario_diario_id": r.usuario_id,
                    "hospital": hospitais.get(r.hospital_id), "contato": None,
                    "filas_ativas": sum(f.receptor_usuario_id == r.usuario_id for f in fila),
                })
            return resultado
        if partes == ["orgaos"]:
            return _orgaos(s, query.get("status", [""])[0])
        if partes == ["fila"]:
            status = query.get("status", [""])[0]
            if status and status != "aguardando":
                raise ErroHTTP(400, "A API lista posições aguardando; não há histórico de fila.")
            tipo = query.get("tipo_orgao_id", [None])[0]
            return [_fila_item(f) for f in s.fila_ativa(int(tipo) if tipo else None)]
        if partes == ["transplantes"]:
            return [{
                **_json(p), "id": p.alocacao_id, "orgao": p.orgao,
                "doador": p.doador_nome, "receptor": p.receptor_nome,
                "data_cirurgia": p.alocado_em, "resultado": p.status_logistica,
                "hospital": p.hospital_destino,
            } for p in s.processos()]
        if partes == ["compatibilidade"]:
            return _cruzamentos(s)
        if partes == ["candidatos"]:
            return _candidatos_resumo(s)
        if partes == ["sem-compativel"]:
            return _sem_compativel(s)
        if partes == ["demanda"]:
            return _demanda(s)
        if partes == ["hospitais-transplantes"]:
            por_hospital = {}
            for p in s.processos():
                item = por_hospital.setdefault(p.hospital_destino, {
                    "hospital": p.hospital_destino, "transplantes": 0, "sucessos": 0})
                item["transplantes"] += 1
                item["sucessos"] += p.status_logistica == "realizado"
            return list(por_hospital.values())
        if partes == ["regras"]:
            abo = [{"abo_doador": a, "pode_doar_para": b}
                   for a, b in sorted(compat.REGRAS_ABO)]
            matriz = []
            for doador in ("O", "A", "B", "AB"):
                for rh_d in ("negativo", "positivo"):
                    for receptor in ("O", "A", "B", "AB"):
                        for rh_r in ("negativo", "positivo"):
                            if compat.sangue_compativel(doador, rh_d, receptor, rh_r):
                                matriz.append({
                                    "doador": doador + ("-" if rh_d == "negativo" else "+"),
                                    "receptor": receptor + ("-" if rh_r == "negativo" else "+"),
                                })
            return {"abo": abo, "matriz": matriz}
        if len(partes) == 3 and partes[0] == "orgaos" and partes[2] == "compativeis":
            selecao = s.selecionar_receptores(int(partes[1]))
            return [{**_candidato(c), "orgao": selecao.oferta.tipo_orgao}
                    for c in selecao.candidatos]

    if metodo == "POST":
        if partes == ["doadores"]:
            _exigir(corpo, "usuario_diario_id", "tipo_doador", "hospital_id")
            d = s.cadastrar_doador(int(corpo["usuario_diario_id"]),
                                   corpo["tipo_doador"], int(corpo["hospital_id"]))
            return {"id": d.id, "nome": d.nome}
        if partes == ["receptores"]:
            _exigir(corpo, "usuario_diario_id", "hospital_id")
            r = s.cadastrar_receptor(int(corpo["usuario_diario_id"]),
                                     int(corpo["hospital_id"]))
            return {"id": r.id, "nome": r.nome}
        if partes == ["orgaos"]:
            _exigir(corpo, "doador_id", "tipo_orgao_id")
            o = s.registrar_orgao(int(corpo["doador_id"]), int(corpo["tipo_orgao_id"]),
                                  int(corpo["hospital_id"]) if corpo.get("hospital_id") else None,
                                  corpo.get("data_hora_captacao"))
            return {"id": o.id}
        if partes == ["fila"]:
            _exigir(corpo, "receptor_id", "tipo_orgao_id")
            urgencia = _prioridade(corpo.get("urgencia", corpo.get("prioridade", 3)))
            return {"id": s.incluir_na_fila(int(corpo["receptor_id"]),
                                            int(corpo["tipo_orgao_id"]), urgencia).id}
        if partes == ["transplantes"]:
            _exigir(corpo, "orgao_id", "fila_id")
            return {"id": s.alocar_orgao(int(corpo["orgao_id"]),
                                         int(corpo["fila_id"])).id}

    if metodo == "PATCH" and len(partes) == 2:
        alvo, identificador = partes[0], int(partes[1])
        if alvo == "fila":
            atualizado = None
            if corpo.get("urgencia") is not None or corpo.get("prioridade") is not None:
                atualizado = s.atualizar_urgencia(
                    identificador, _prioridade(corpo.get("urgencia", corpo.get("prioridade"))))
            if corpo.get("status") == "removido":
                atualizado = s.remover_da_fila(identificador)
            if atualizado is None:
                raise ErroHTTP(400, "Informe urgência ou status 'removido'.")
            return {"atualizado": atualizado.id}
        if alvo == "transplantes":
            status = corpo.get("resultado", corpo.get("status"))
            if status in ("cancelado", "cancelada"):
                resultado = s.cancelar_alocacao(identificador)
            elif status in ("realizado", "sucesso"):
                s.registrar_entrega(identificador)
                resultado = s.concluir_transplante(identificador)
            elif status == "entregue":
                resultado = s.registrar_entrega(identificador)
            else:
                raise ErroHTTP(400, "Use status entregue, realizado/sucesso ou cancelado.")
            return {"atualizado": resultado.id}
        if alvo == "orgaos":
            raise ErroHTTP(400, "O status do órgão é controlado pelo fluxo de alocação.")
        if alvo == "doadores":
            raise ErroHTTP(400, "O vínculo ao Diário é definido no cadastro.")
    raise ErroHTTP(404, "Rota da Central não encontrada.")


def _enums():
    return {
        "sexo": list(SEXOS), "tipo_sanguineo": list(TIPOS_SANGUINEOS),
        "fator_rh": list(FATORES_RH), "gravidade_alergia": list(GRAVIDADES_ALERGIA),
        "status_doenca": list(STATUS_DOENCA),
        "status_orgao": ["disponivel", "alocado", "descartado"],
        "status_fila": ["aguardando"],
        "prioridade_fila": ["baixa", "normal", "alta", "emergencia"],
        "tipo_doador": list(TIPOS_DOADOR),
        "resultado_transplante": ["entregue", "realizado", "cancelado"],
    }


def _integracao_rotear(metodo, partes, central):
    if metodo != "GET":
        raise ErroHTTP(405, "Somente GET nesta rota.")
    if partes == ["usuarios"] or partes == ["resumo"] or partes == ["conferencia"]:
        usuarios = _integracao_usuarios(central)
    if partes == ["usuarios"]:
        return usuarios
    if partes == ["resumo"]:
        return {
            "usuarios_diario": len(usuarios),
            "doadores_vinculados": sum(u["e_doador"] for u in usuarios),
            "receptores_vinculados": sum(u["e_receptor"] for u in usuarios),
            "com_impedimento": sum(u["impedimentos"] > 0 for u in usuarios),
        }
    if partes == ["conferencia"]:
        indexed = {u["usuario_id"]: u for u in usuarios}
        def linhas(ids):
            return [{
                "nome": indexed[i]["nome"], "sangue_central": "não armazenado",
                "sangue_diario": indexed[i]["sangue"], "situacao": "vinculado por ID",
                "doencas_impeditivas": indexed[i]["doencas_impeditivas"],
            } for i in ids if i in indexed]
        return {"doadores": linhas(d.usuario_id for d in central.listar_doadores()),
                "receptores": linhas(r.usuario_id for r in central.listar_receptores())}
    if partes == ["divergencias"]:
        return []
    if partes == ["alertas"]:
        alertas = []
        for o in central.listar_orgaos("disponivel"):
            restricoes = central.diario.restricoes_doacao(o["doador_usuario_id"])
            if restricoes:
                alertas.append({
                    "orgao_id": o["id"], "orgao": o["orgao"], "doador": o["doador"],
                    "sangue": o["sangue"], "status": o["status"],
                    "doencas_impeditivas": ", ".join(restricoes), "alergias_graves": "",
                })
        return {"orgaos": alertas,
                "doadores": [u for u in _integracao_usuarios(central) if u["impedimentos"]]}
    if len(partes) == 3 and partes[0] == "usuarios" and partes[2] == "compatibilidade":
        resultado = []
        for o in central.listar_orgaos("disponivel"):
            if o["doador_usuario_id"] == int(partes[1]):
                selecao = central.selecionar_receptores(o["id"])
                resultado.extend({
                    "receptor": c.pedido.nome, "sangue_receptor": c.sangue,
                    "orgao": o["orgao"], "prioridade": _prioridade_label(c.pedido.urgencia),
                    "dias_na_fila": c.pedido.dias_espera, "hospital": c.pedido.hospital,
                } for c in selecao.elegiveis)
        return resultado
    raise ErroHTTP(404, "Rota de integração não encontrada.")
class Manipulador(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PASTA_WEB), **kwargs)

    def log_message(self, formato, *args):
        sys.stdout.write(f"  {self.command} {self.path}\n")

    def end_headers(self):
        if not self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def _responder(self, dados, codigo=200):
        payload = json.dumps(dados, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _ler_corpo(self):
        tamanho = int(self.headers.get("Content-Length") or 0)
        if not tamanho:
            return {}
        try:
            corpo = json.loads(self.rfile.read(tamanho).decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as erro:
            raise ErroHTTP(400, "Corpo da requisição não é um JSON válido.") from erro
        if not isinstance(corpo, dict):
            raise ErroHTTP(400, "O corpo deve ser um objeto JSON.")
        return corpo

    def _despachar(self, metodo):
        url = urlparse(self.path)
        if not url.path.startswith("/api/"):
            if metodo == "GET":
                return SimpleHTTPRequestHandler.do_GET(self)
            raise ErroHTTP(404, "Rota não encontrada.")
        partes = [p for p in url.path[len("/api/"):].split("/") if p]
        query = parse_qs(url.query)
        corpo = self._ler_corpo() if metodo in ("POST", "PATCH") else {}
        if any(not re.fullmatch(r"[\w-]+", parte) for parte in partes):
            raise ErroHTTP(400, "Segmento inválido na rota.")
        if partes == ["enums"]:
            return self._responder(_enums())
        if not partes:
            raise ErroHTTP(404, "Grupo da API não informado.")
        if partes[0] == "diario":
            with DiarioService() as servico:
                resultado = _diario(metodo, partes[1:], query, corpo, servico)
        elif partes[0] == "central":
            with CentralService() as servico:
                resultado = _central(metodo, partes[1:], query, corpo, servico)
        elif partes[0] == "integracao":
            with CentralService() as servico:
                resultado = _integracao_rotear(metodo, partes[1:], servico)
        else:
            raise ErroHTTP(404, "Grupo desconhecido: " + partes[0])
        self._responder(resultado, 201 if metodo == "POST" else 200)

    def _executar(self, metodo):
        try:
            self._despachar(metodo)
        except ErroHTTP as erro:
            self._responder({"erro": erro.mensagem}, erro.codigo)
        except ErroDeNegocio as erro:
            self._responder({"erro": str(erro)}, 400)
        except (ValueError, TypeError) as erro:
            self._responder({"erro": "Valor inválido: " + str(erro)}, 400)
        except Exception:
            traceback.print_exc()
            self._responder({"erro": "Erro interno ao processar a solicitação."}, 500)

    def do_GET(self):
        self._executar("GET")

    def do_POST(self):
        self._executar("POST")

    def do_PATCH(self):
        self._executar("PATCH")


def principal(porta=8000):
    servidor = ThreadingHTTPServer(("127.0.0.1", porta), Manipulador)
    print(f"Gestão Hospitalar disponível em http://localhost:{porta}")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    principal(int(sys.argv[1]) if len(sys.argv) > 1 else 8000)
