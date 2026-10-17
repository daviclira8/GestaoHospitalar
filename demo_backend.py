import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

from backend.central.servico import CentralService
from backend.diario.servico import DiarioService
from backend.erros import ErroDeNegocio

PAUSAR = "--pausar" in sys.argv


def titulo(texto: str) -> None:
    if PAUSAR:
        input("\n[ENTER para continuar]")
    print("\n" + "=" * 78 + f"\n {texto}\n" + "=" * 78)


def tabela(cabecalhos: list[str], linhas: list[list]) -> None:
    linhas = [["" if v is None else str(v) for v in linha] for linha in linhas]
    larguras = [max(len(c), *(len(l[i]) for l in linhas)) if linhas else len(c)
                for i, c in enumerate(cabecalhos)]
    formato = "  ".join(f"{{:<{w}}}" for w in larguras)
    print(formato.format(*cabecalhos))
    print("  ".join("-" * w for w in larguras))
    for linha in linhas:
        print(formato.format(*linha))


def tentar(descricao: str, acao) -> None:
    try:
        acao()
        print(f"  ✘ {descricao}: NÃO foi bloqueado (verificar!)")
    except ErroDeNegocio as erro:
        print(f"  ✔ {descricao}\n      → bloqueado: {erro}")


def mostrar_selecao(resultado) -> None:
    o = resultado.oferta
    print(f"Órgão {o.orgao_id}: {o.tipo_orgao} | doador {o.doador_nome} (tipo {o.doador_sangue}) | "
          f"{o.hospital} | restam {o.horas_restantes:.1f} h\n")
    tabela(["Pos", "Fila", "Receptor", "Sangue", "Urg", "Espera", "Dist km", "Modal",
            "Transp h", "Resultado"],
           [[c.posicao or "-", c.pedido.fila_id, c.pedido.nome, c.sangue, c.pedido.urgencia,
             f"{c.pedido.dias_espera} d", c.distancia_km, c.modal, c.tempo_transporte_h,
             "ELEGÍVEL" if c.elegivel else c.motivo_exclusao]
            for c in resultado.candidatos])
    if resultado.indicado:
        print(f"\n>> Receptor indicado: {resultado.indicado.pedido.nome} "
              f"(fila {resultado.indicado.pedido.fila_id})")


def main() -> None:
    if "--sem-recriar" not in sys.argv:
        from criar_bancos import criar_bancos
        criar_bancos()

    with DiarioService() as diario, CentralService() as central:

        titulo("1. DIÁRIO — cadastro de um novo usuário e do seu histórico")
        nova = diario.buscar_por_cpf("10000000099") or diario.cadastrar_usuario(
            nome="Renata Albuquerque Sales", cpf="100.000.000-99", data_nascimento="22/08/1994",
            sexo="feminino", cidade="Fortaleza", uf="CE", email="renata.sales@exemplo.com",
            telefone="(85) 90000-0099")
        print(f"Usuária cadastrada: id {nova.id} | {nova.nome} | {nova.idade} anos | "
              f"sangue: {nova.sangue}")
        nova = diario.registrar_tipagem(nova.id, "O", "negativo")
        print(f"Exame de tipagem registrado → cadastro atualizado: sangue {nova.sangue}")
        diario.registrar_metrica(nova.id, "peso", 63.5, "kg")
        consulta = diario.registrar_consulta(nova.id, "10/10/2026 09:00", "Clínica geral",
                                             "Dr. João Batista", "UBS Messejana", "Check-up")
        diario.registrar_exame(nova.id, "Hemograma completo", "10/10/2026", "Sem alterações",
                               consulta_id=consulta.id)
        diario.adicionar_alergia(nova.id, "Dipirona", "leve")
        print("Registrados: peso, consulta, exame vinculado à consulta e alergia.")

        titulo("2. DIÁRIO — prontuário e acompanhamento ao longo do tempo (Juliana)")
        p = diario.prontuario(10)
        print(f"{p.usuario.nome} | {p.usuario.idade} anos | sangue {p.usuario.sangue}")
        print("Alergias:", ", ".join(f"{a.substancia} ({a.gravidade})" for a in p.alergias))
        print("Doenças: ", ", ".join(f"{d.doenca} [{d.status}]" for d in p.diagnosticos))
        print("\nLinha do tempo:")
        tabela(["Data", "Evento", "Descrição"],
               [[e.data.strftime("%d/%m/%Y"), e.evento, e.descricao] for e in p.linha_do_tempo])
        print("\nEvolução do peso:")
        tabela(["Data", "Valor", "Variação"],
               [[m.data_hora.strftime("%d/%m/%Y"), f"{m.valor} {m.unidade}",
                 "" if m.variacao is None else f"{m.variacao:+}"] for m in p.metricas["peso"]])

        titulo("3. CENTRAL — órgãos disponíveis (doação do Carlos, captada agora)")
        tabela(["Órgão", "Tipo", "Doador (Diário)", "Sangue", "Origem", "Restam (h)"],
               [[o.orgao_id, o.orgao, o.doador_nome, o.doador_sangue, o.hospital_origem,
                 o.horas_restantes] for o in central.orgaos_disponiveis()])

        titulo("4. CENTRAL — seleção de receptores para o CORAÇÃO")
        resultado = central.selecionar_receptores(6)
        mostrar_selecao(resultado)

        titulo("5. CENTRAL — alocação e logística do coração")
        tentar("Alocar o coração para Igor (B-), 1º da fila",
               lambda: central.alocar_orgao(6, 9))
        alocacao, escolhido = central.alocar_melhor_receptor(6)
        print(f"\nAlocado para {escolhido.pedido.nome}: alocação {alocacao.id} → "
              f"{alocacao.status_logistica}")
        tentar("Alocar o mesmo coração de novo", lambda: central.alocar_orgao(6, 10))
        print(f"Entrega registrada  → {central.registrar_entrega(alocacao.id).status_logistica}")
        print(f"Transplante feito   → {central.concluir_transplante(alocacao.id).status_logistica}")

        titulo("6. CENTRAL — os dois rins: alocação, intercorrência e realocação")
        mostrar_selecao(central.selecionar_receptores(3))
        aloc_rim1, rec1 = central.alocar_melhor_receptor(3)
        aloc_rim2, rec2 = central.alocar_melhor_receptor(4)
        print(f"\nRim 3 → {rec1.pedido.nome} (alocação {aloc_rim1.id})")
        print(f"Rim 4 → {rec2.pedido.nome} (alocação {aloc_rim2.id}) — a 1ª já tinha órgão a caminho")
        print(f"\nIntercorrência: {rec2.pedido.nome} teve uma infecção e não pode operar.")
        central.cancelar_alocacao(aloc_rim2.id)
        central.remover_da_fila(rec2.pedido.fila_id)
        print("  → alocação CANCELADA (o rim 4 volta a ficar disponível) e receptora retirada da fila.")
        aloc_rim2, rec2 = central.alocar_melhor_receptor(4)
        print(f"  → rim 4 realocado para {rec2.pedido.nome} (alocação {aloc_rim2.id}).")

        titulo("7. INTEGRAÇÃO — o histórico do Diário decide na Central")
        rafael = diario.ficha(13)
        print(f"{rafael.nome}: restrição de doação no Diário = {rafael.restricao_doacao}")
        tentar("Captar rim do doador vivo Rafael (hepatite C ativa no Diário)",
               lambda: central.registrar_orgao(doador_id=3, tipo_orgao_id=1))
        tentar("Cadastrar Vanessa como receptora (sem tipagem no Diário)",
               lambda: central.cadastrar_receptor(16, hospital_id=1))
        diario.registrar_tipagem(16, "AB", "positivo")
        print("\n→ Tipagem de Vanessa registrada NO DIÁRIO (AB+). Tentando de novo na Central:")
        receptora = (central.buscar_receptor_por_usuario(16)
                     or central.cadastrar_receptor(16, hospital_id=1))
        entrada = central.incluir_na_fila(receptora.id, tipo_orgao_id=6, urgencia=2)
        print(f"  ✔ {receptora.nome} cadastrada (receptor {receptora.id}) e na fila de "
              f"córnea (fila {entrada.id}).\n")
        mostrar_selecao(central.selecionar_receptores(7))

        titulo("8. CENTRAL — doação e transfusão de sangue")
        tentar("Paulo doar de novo (doou há poucos dias)",
               lambda: central.registrar_doacao_sangue(19, hospital_id=1))
        tentar("Rafael doar sangue (hepatite C ativa no Diário)",
               lambda: central.registrar_doacao_sangue(13, hospital_id=1))
        bolsa = central.registrar_doacao_sangue(nova.id, hospital_id=1)
        print(f"  ✔ {nova.nome} doou: bolsa {bolsa.id}, {bolsa.sangue}, "
              f"validade {bolsa.data_validade:%d/%m/%Y}")
        manut = central.executar_manutencao()
        print(f"\nManutenção: {manut['bolsas_vencidas']} bolsa(s) marcada(s) como vencida(s), "
              f"{manut['orgaos_descartados']} órgão(s) descartado(s).")
        print("\nEstoque disponível por tipo (tipo lido do Diário):")
        tabela(["Sangue", "Bolsas", "Volume (mL)"],
               [[t, e["bolsas"], e["volume_ml"]] for t, e in central.estoque_sangue().items()])
        print("\nBolsas compatíveis para Juliana (O-), da que vence primeiro:")
        tabela(["Bolsa", "Sangue", "Hospital", "Validade", "Dias p/ vencer"],
               [[b.id, b.sangue, b.hospital, f"{b.data_validade:%d/%m/%Y}", b.dias_ate_vencer]
                for b in central.bolsas_compativeis(10)])

        titulo("9. CENTRAL — situação dos processos e auditoria da integração")
        tabela(["Aloc", "Órgão", "Doador", "Receptor", "Destino", "Km", "Logística", "Fila"],
               [[p.alocacao_id, p.orgao, p.doador_nome, p.receptor_nome, p.hospital_destino,
                 p.distancia_km, p.status_logistica, p.status_fila] for p in central.processos()])
        orfaos = central.verificar_integridade()
        print("\nIntegridade Central → Diário:",
              "OK, todo usuario_id existe no Diário." if not orfaos else orfaos)


if __name__ == "__main__":
    try:
        main()
    except ErroDeNegocio as erro:
        sys.exit(f"\nERRO: {erro}\n(Rodou com --sem-recriar? A demonstração espera os dados iniciais.)")
