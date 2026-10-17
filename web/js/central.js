/* ==========================================================================
   Secao Central Hospitalar de Transplantes
   ========================================================================== */
const Central = {
  painelAtual: 'compatibilidade',
  orgaoSelecionado: null,
  filaSelecionada: null,
  alertas: [],

  async iniciar() {
    document.querySelectorAll('#abasCentral .aba-interna').forEach((botao) => {
      botao.onclick = () => this.trocarPainel(botao.dataset.painel, botao);
    });
    const e = API.enums;
    preencherSelect(document.getElementById('filtroStatusOrgao'),
                    ['todos'].concat(e.status_orgao), 'disponivel');
    preencherSelect(document.getElementById('filtroStatusFila'),
                    ['todas'].concat(e.status_fila), 'aguardando');
    document.getElementById('filtroStatusOrgao').onchange = () => this.painelOrgaos();
    document.getElementById('filtroStatusFila').onchange = () => this.painelFila();
    document.getElementById('seletorOrgao').onchange = (ev) => {
      this.orgaoSelecionado = Number(ev.target.value);
      this.carregarCompativeis();
    };
    document.getElementById('btnRegras').onclick = () => this.mostrarRegras();
    document.querySelector('[data-form="doador"]').onclick = () => this.novoDoador();
    document.querySelector('[data-form="receptor"]').onclick = () => this.novoReceptor();
    document.querySelector('[data-form="orgao"]').onclick = () => this.novoOrgao();
    document.querySelector('[data-form="fila"]').onclick = () => this.inserirNaFila();
    await this.recarregar();
  },

  async recarregar() {
    const [painel, alertas] = await Promise.all([
      API.central.painel(),
      API.integracao.alertas(),
    ]);
    this.alertas = alertas.orgaos;
    montarCartoes('cartoesCentral', [
      { rotulo: 'Doadores', valor: painel.doadores },
      { rotulo: 'Receptores', valor: painel.receptores },
      { rotulo: 'Orgaos disponiveis', valor: painel.orgaos_disponiveis },
      { rotulo: 'Reservados', valor: painel.orgaos_reservados },
      { rotulo: 'Na fila', valor: painel.na_fila },
      { rotulo: 'Emergencias', valor: painel.emergencias, destaque: painel.emergencias > 0 },
      { rotulo: 'Transplantes', valor: painel.transplantes },
      { rotulo: 'Cruzamentos compativeis', valor: painel.cruzamentos_compativeis },
    ]);
    await this.carregarPainel();
  },

  trocarPainel(nome, botao) {
    this.painelAtual = nome;
    document.querySelectorAll('#abasCentral .aba-interna')
      .forEach((b) => b.classList.remove('ativa'));
    botao.classList.add('ativa');
    document.querySelectorAll('#secao-central .painel-interno')
      .forEach((p) => p.classList.remove('ativo'));
    document.getElementById(`painel-${nome}`).classList.add('ativo');
    this.carregarPainel();
  },

  async carregarPainel() {
    const metodos = {
      compatibilidade: () => this.painelCompatibilidade(),
      orgaos: () => this.painelOrgaos(),
      fila: () => this.painelFila(),
      doadores: () => this.painelDoadores(),
      receptores: () => this.painelReceptores(),
      transplantes: () => this.painelTransplantes(),
      'painel-central': () => this.painelIndicadores(),
    };
    await metodos[this.painelAtual]();
  },

  /* -------------------------------------------------- compatibilidade */
  async painelCompatibilidade() {
    const [orgaos, cruzamentos] = await Promise.all([
      API.central.orgaos('disponivel'),
      API.central.compatibilidade(),
    ]);
    const seletor = document.getElementById('seletorOrgao');
    if (orgaos.length === 0) {
      seletor.innerHTML = '<option value="">Nenhum orgao disponivel</option>';
      document.getElementById('tabelaCompativeis').innerHTML =
        '<p class="vazio">Nenhum orgao disponivel.</p>';
      document.getElementById('alertaOrgao').classList.add('oculto');
    } else {
      preencherSelect(seletor, orgaos.map((o) => ({
        valor: o.id,
        texto: `${o.id} - ${o.orgao} | doador ${o.doador} (${o.sangue}) | ${o.hospital}`,
      })), this.orgaoSelecionado);
      if (!orgaos.some((o) => o.id === this.orgaoSelecionado)) {
        this.orgaoSelecionado = orgaos[0].id;
        seletor.value = String(this.orgaoSelecionado);
      }
      await this.carregarCompativeis();
    }
    montarTabela('tabelaCruzamentos', cruzamentos, [
      { chave: 'orgao', titulo: 'Orgao' },
      { chave: 'doador', titulo: 'Doador' },
      { chave: 'sangue_doador', titulo: 'Sangue doador' },
      { chave: 'receptor', titulo: 'Receptor' },
      { chave: 'sangue_receptor', titulo: 'Sangue receptor' },
      { chave: 'prioridade', titulo: 'Prioridade', formato: (v) => etiqueta(v) },
      { chave: 'dias_na_fila', titulo: 'Dias' },
    ], {
      vazio: 'Nenhum cruzamento compativel no momento.',
      urgente: (l) => l.prioridade === 'emergencia',
    });
  },

  async carregarCompativeis() {
    if (!this.orgaoSelecionado) return;
    const dados = await API.central.compativeis(this.orgaoSelecionado);
    this.filaSelecionada = dados.length ? dados[0].fila_id : null;
    montarTabela('tabelaCompativeis', dados, [
      { chave: 'fila_id', titulo: 'Fila' },
      { chave: 'receptor', titulo: 'Receptor' },
      { chave: 'sangue_receptor', titulo: 'Sangue' },
      { chave: 'prioridade', titulo: 'Prioridade', formato: (v) => etiqueta(v) },
      { chave: 'data_entrada', titulo: 'Entrada' },
      { chave: 'dias_na_fila', titulo: 'Dias' },
      { chave: 'hospital_receptor', titulo: 'Hospital' },
      { chave: 'acao', titulo: '', formato: (_, l) =>
        `<button class="btn pequeno" data-transplante="${l.fila_id}">Efetivar</button>` },
    ], {
      vazio: 'Nenhum receptor compativel aguardando este orgao.',
      urgente: (l) => l.prioridade === 'emergencia',
      aoClicar: (linha) => { this.filaSelecionada = linha.fila_id; },
    });
    document.querySelectorAll('[data-transplante]').forEach((botao) => {
      botao.onclick = (e) => {
        e.stopPropagation();
        this.efetivarTransplante(Number(botao.dataset.transplante));
      };
    });
    // alerta de impedimento vindo do Diario de Saude do doador
    const alerta = this.alertas.find((a) => a.orgao_id === this.orgaoSelecionado);
    const caixa = document.getElementById('alertaOrgao');
    if (alerta) {
      caixa.innerHTML = `Atencao: o Diario de Saude do doador
        <strong>${esc(alerta.doador)}</strong> registra
        <strong>${esc(alerta.doencas_impeditivas)}</strong>, que impede a doacao.`;
      caixa.classList.remove('oculto');
    } else {
      caixa.classList.add('oculto');
    }
  },

  /* ------------------------------------------------------------ orgaos */
  async painelOrgaos() {
    const status = document.getElementById('filtroStatusOrgao').value;
    const dados = await API.central.orgaos(status === 'todos' ? '' : status);
    montarTabela('tabelaOrgaos', dados, [
      { chave: 'id', titulo: 'ID' },
      { chave: 'orgao', titulo: 'Orgao' },
      { chave: 'doador', titulo: 'Doador' },
      { chave: 'sangue', titulo: 'Sangue' },
      { chave: 'tipo_doador', titulo: 'Doacao' },
      { chave: 'data_captacao', titulo: 'Captacao' },
      { chave: 'horas_decorridas', titulo: 'H. decorridas' },
      { chave: 'isquemia_h', titulo: 'Isquemia (h)' },
      { chave: 'status', titulo: 'Status', formato: (v) => etiqueta(v) },
      { chave: 'hospital', titulo: 'Hospital' },
    ], {
      vazio: 'Nenhum orgao encontrado.',
      urgente: (l) => l.status === 'disponivel' && l.horas_decorridas > l.isquemia_h,
    });
  },

  /* -------------------------------------------------------------- fila */
  async painelFila() {
    const status = document.getElementById('filtroStatusFila').value;
    const dados = await API.central.fila(status === 'todas' ? '' : status);
    montarTabela('tabelaFila', dados, [
      { chave: 'fila_id', titulo: 'ID' },
      { chave: 'receptor', titulo: 'Receptor' },
      { chave: 'sangue', titulo: 'Sangue' },
      { chave: 'orgao', titulo: 'Orgao' },
      { chave: 'prioridade', titulo: 'Prioridade', formato: (v) => etiqueta(v) },
      { chave: 'data_entrada', titulo: 'Entrada' },
      { chave: 'dias_na_fila', titulo: 'Dias' },
      { chave: 'status', titulo: 'Situacao', formato: (v) => etiqueta(v) },
      { chave: 'hospital', titulo: 'Hospital' },
      { chave: 'acao', titulo: '', formato: (_, l) =>
        `<button class="btn pequeno secundario" data-fila="${l.fila_id}">Prioridade</button>
         <button class="btn pequeno secundario" data-remover-fila="${l.fila_id}">Remover</button>` },
    ], {
      vazio: 'Fila vazia.',
      urgente: (l) => l.prioridade === 'emergencia',
    });
    document.querySelectorAll('[data-fila]').forEach((botao) => {
      botao.onclick = (e) => {
        e.stopPropagation();
        this.editarFila(Number(botao.dataset.fila));
      };
    });
    document.querySelectorAll('[data-remover-fila]').forEach((botao) => {
      botao.onclick = (e) => {
        e.stopPropagation();
        this.removerFila(Number(botao.dataset.removerFila));
      };
    });
  },

  /* ---------------------------------------------------------- doadores */
  async painelDoadores() {
    const dados = await API.central.doadores();
    montarTabela('tabelaDoadores', dados, [
      { chave: 'id', titulo: 'ID' },
      { chave: 'nome', titulo: 'Nome' },
      { chave: 'sangue', titulo: 'Sangue' },
      { chave: 'tipo_doador', titulo: 'Tipo' },
      { chave: 'hospital', titulo: 'Hospital' },
      { chave: 'data_registro', titulo: 'Registro' },
      { chave: 'orgaos', titulo: 'Orgaos' },
      { chave: 'usuario_diario_id', titulo: 'Diario',
        formato: (v) => (v ? `<span class="etiqueta verde">usuario ${esc(v)}</span>`
                            : '<span class="etiqueta cinza">sem vinculo</span>') },
    ], { vazio: 'Nenhum doador cadastrado.' });
  },

  async painelReceptores() {
    const dados = await API.central.receptores();
    montarTabela('tabelaReceptores', dados, [
      { chave: 'id', titulo: 'ID' },
      { chave: 'nome', titulo: 'Nome' },
      { chave: 'sangue', titulo: 'Sangue' },
      { chave: 'hospital', titulo: 'Hospital' },
      { chave: 'contato', titulo: 'Contato' },
      { chave: 'filas_ativas', titulo: 'Filas ativas' },
      { chave: 'usuario_diario_id', titulo: 'Diario',
        formato: (v) => (v ? `<span class="etiqueta verde">usuario ${esc(v)}</span>`
                            : '<span class="etiqueta cinza">sem vinculo</span>') },
      { chave: 'acao', titulo: '', formato: (_, l) =>
        `<button class="btn pequeno secundario" data-fila-receptor="${l.id}">Inserir na fila</button>` },
    ], { vazio: 'Nenhum receptor cadastrado.' });
    document.querySelectorAll('[data-fila-receptor]').forEach((botao) => {
      botao.onclick = (e) => {
        e.stopPropagation();
        this.inserirNaFila(Number(botao.dataset.filaReceptor));
      };
    });
  },

  async painelTransplantes() {
    const dados = await API.central.transplantes();
    montarTabela('tabelaTransplantes', dados, [
      { chave: 'id', titulo: 'ID' },
      { chave: 'orgao', titulo: 'Orgao' },
      { chave: 'doador', titulo: 'Doador' },
      { chave: 'receptor', titulo: 'Receptor' },
      { chave: 'data_cirurgia', titulo: 'Cirurgia' },
      { chave: 'cirurgiao', titulo: 'Cirurgiao' },
      { chave: 'resultado', titulo: 'Resultado', formato: (v) => etiqueta(v) },
      { chave: 'hospital', titulo: 'Hospital' },
      { chave: 'acao', titulo: '', formato: (_, l) =>
        `<button class="btn pequeno secundario" data-desfecho="${l.id}">Desfecho</button>` },
    ], { vazio: 'Nenhum transplante registrado.' });
    document.querySelectorAll('[data-desfecho]').forEach((botao) => {
      botao.onclick = (e) => {
        e.stopPropagation();
        this.atualizarDesfecho(Number(botao.dataset.desfecho));
      };
    });
  },

  async painelIndicadores() {
    const [demanda, candidatos, semCompativel, hospitais] = await Promise.all([
      API.central.demanda(), API.central.candidatos(),
      API.central.semCompativel(), API.central.porHospital(),
    ]);
    montarTabela('tabelaDemanda', demanda, [
      { chave: 'orgao', titulo: 'Orgao' },
      { chave: 'aguardando', titulo: 'Aguardando' },
      { chave: 'emergencias', titulo: 'Emergencias' },
      { chave: 'media_dias', titulo: 'Media de dias' },
      { chave: 'disponiveis', titulo: 'Disponiveis' },
    ], { urgente: (l) => l.emergencias > 0 });
    montarTabela('tabelaCandidatos', candidatos, [
      { chave: 'orgao_id', titulo: 'ID' },
      { chave: 'orgao', titulo: 'Orgao' },
      { chave: 'sangue_doador', titulo: 'Sangue doador' },
      { chave: 'data_captacao', titulo: 'Captacao' },
      { chave: 'candidatos', titulo: 'Candidatos' },
    ], { urgente: (l) => l.candidatos === 0 });
    montarTabela('tabelaSemCompativel', semCompativel, [
      { chave: 'receptor', titulo: 'Receptor' },
      { chave: 'sangue', titulo: 'Sangue' },
      { chave: 'orgao', titulo: 'Orgao' },
      { chave: 'prioridade', titulo: 'Prioridade', formato: (v) => etiqueta(v) },
      { chave: 'dias_na_fila', titulo: 'Dias' },
    ], { vazio: 'Todos os receptores possuem alguma opcao compativel.',
         urgente: (l) => l.prioridade === 'emergencia' });
    montarTabela('tabelaHospitais', hospitais, [
      { chave: 'hospital', titulo: 'Hospital' },
      { chave: 'transplantes', titulo: 'Transplantes' },
      { chave: 'sucessos', titulo: 'Sucessos' },
    ]);
  },

  /* ------------------------------------------------------------- acoes */
  async _itensHospitais() {
    const hospitais = await API.central.hospitais();
    return hospitais.map((h) => [h.id, `${h.nome} (${h.cidade}/${h.uf})`]);
  },

  async _itensTiposOrgao() {
    const tipos = await API.central.tiposOrgao();
    return tipos.map((t) => [t.id, `${t.nome} - isquemia ${t.tempo_isquemia_horas}h`]);
  },

  async _itensUsuariosDiario() {
    const usuarios = await API.integracao.usuarios();
    return usuarios.filter((u) => u.sangue && u.sangue !== 'não informado')
      .map((u) => [u.usuario_id, `${u.nome} (${u.sangue})`]);
  },

  async novoDoador() {
    const usuarios = await this._itensUsuariosDiario();
    if (usuarios.length === 0) {
      avisar('Cadastre e informe a tipagem do usuario no Diario primeiro.', 'erro');
      return;
    }
    const e = API.enums;
    const dados = await abrirFormulario('Cadastrar doador', [
      { chave: 'tipo_doador', rotulo: 'Tipo de doador', tipo: 'opcao', opcoes: e.tipo_doador },
      { chave: 'hospital_id', rotulo: 'Hospital', tipo: 'lista', itens: await this._itensHospitais() },
      { chave: 'usuario_diario_id', rotulo: 'Usuario do Diario', tipo: 'lista',
        itens: usuarios },
    ]);
    if (!dados) return;
    if (await tentar(() => API.central.criarDoador(dados), 'Doador cadastrado.')) {
      await this.recarregar();
      if (Aplicacao.secaoAtual === 'integracao') await Integracao.recarregar();
    }
  },

  async novoReceptor() {
    const usuarios = await this._itensUsuariosDiario();
    if (usuarios.length === 0) {
      avisar('Cadastre e informe a tipagem do usuario no Diario primeiro.', 'erro');
      return;
    }
    const dados = await abrirFormulario('Cadastrar receptor', [
      { chave: 'hospital_id', rotulo: 'Hospital', tipo: 'lista', itens: await this._itensHospitais() },
      { chave: 'usuario_diario_id', rotulo: 'Usuario do Diario', tipo: 'lista',
        itens: usuarios },
    ]);
    if (!dados) return;
    const criado = await tentar(() => API.central.criarReceptor(dados), 'Receptor cadastrado.');
    if (criado) {
      await this.recarregar();
      await this.inserirNaFila(criado.id);
    }
  },

  async novoOrgao() {
    const doadores = await API.central.doadores();
    if (doadores.length === 0) {
      avisar('Cadastre um doador primeiro.', 'erro');
      return;
    }
    const dados = await abrirFormulario('Registrar orgao captado', [
      { chave: 'doador_id', rotulo: 'Doador', tipo: 'lista',
        itens: doadores.map((d) => [d.id, `${d.nome} (${d.sangue}, ${d.hospital})`]) },
      { chave: 'tipo_orgao_id', rotulo: 'Tipo de orgao', tipo: 'lista',
        itens: await this._itensTiposOrgao() },
      { chave: 'hospital_id', rotulo: 'Hospital do orgao', tipo: 'lista',
        itens: await this._itensHospitais() },
      { chave: 'data_hora_captacao', rotulo: 'Data/hora da captacao', tipo: 'data_hora',
        padrao: `${hoje()} 08:00` },
    ]);
    if (!dados) return;
    if (await tentar(() => API.central.criarOrgao(dados), 'Orgao registrado.')) {
      await this.recarregar();
    }
  },

  async inserirNaFila(receptorId) {
    const campos = [];
    if (!receptorId) {
      const receptores = await API.central.receptores();
      if (receptores.length === 0) {
        avisar('Cadastre um receptor primeiro.', 'erro');
        return;
      }
      campos.push({ chave: 'receptor_id', rotulo: 'Receptor', tipo: 'lista',
        itens: receptores.map((r) => [r.id, `${r.nome} (${r.sangue})`]) });
    }
    campos.push(
      { chave: 'tipo_orgao_id', rotulo: 'Orgao aguardado', tipo: 'lista',
        itens: await this._itensTiposOrgao() },
      { chave: 'prioridade', rotulo: 'Prioridade', tipo: 'opcao',
        opcoes: API.enums.prioridade_fila, padrao: 'normal' },
    );
    const dados = await abrirFormulario('Inserir receptor na fila de espera', campos);
    if (!dados) return;
    if (receptorId) dados.receptor_id = receptorId;
    if (await tentar(() => API.central.inserirNaFila(dados), 'Receptor inserido na fila.')) {
      await this.recarregar();
    }
  },

  async editarFila(id) {
    const e = API.enums;
    const dados = await abrirFormulario(`Editar fila ${id}`, [
      { chave: 'prioridade', rotulo: 'Prioridade', tipo: 'opcao', opcoes: e.prioridade_fila },
    ]);
    if (!dados) return;
    if (await tentar(() => API.central.atualizarFila(id, dados), 'Fila atualizada.')) {
      await this.recarregar();
    }
  },

  async removerFila(id) {
    if (await tentar(() => API.central.atualizarFila(id, { status: 'removido' }),
                     'Posicao removida da fila.')) {
      await this.recarregar();
    }
  },

  async efetivarTransplante(filaId) {
    const alerta = this.alertas.find((a) => a.orgao_id === this.orgaoSelecionado);
    if (alerta) {
      avisar(`Alocacao bloqueada: o Diario do doador ${alerta.doador} registra ` +
             `"${alerta.doencas_impeditivas}".`, 'erro');
      return;
    }
    const criado = await tentar(() => API.central.efetivarTransplante({
      orgao_id: this.orgaoSelecionado, fila_id: filaId,
    }));
    if (criado) {
      avisar(`Alocacao ${criado.id} registrada.`, 'ok');
      this.orgaoSelecionado = null;
      await this.recarregar();
    }
  },

  async atualizarDesfecho(id) {
    const dados = await abrirFormulario('Atualizar desfecho do transplante', [
      { chave: 'resultado', rotulo: 'Resultado', tipo: 'opcao',
        opcoes: API.enums.resultado_transplante },
    ]);
    if (!dados) return;
    if (await tentar(() => API.central.atualizarTransplante(id, dados), 'Desfecho atualizado.')) {
      await this.painelTransplantes();
    }
  },

  async mostrarRegras() {
    const regras = await API.central.regras();
    const porDoador = {};
    regras.matriz.forEach((r) => {
      porDoador[r.doador] = porDoador[r.doador] || [];
      porDoador[r.doador].push(r.receptor);
    });
    const linhasAbo = regras.abo.map((r) =>
      `<tr><td><strong>${esc(r.abo_doador)}</strong></td><td>${esc(r.pode_doar_para)}</td></tr>`).join('');
    const linhasMatriz = Object.keys(porDoador).sort().map((d) =>
      `<tr><td><strong>${esc(d)}</strong></td><td>${esc(porDoador[d].sort().join(', '))}</td></tr>`).join('');
    const modal = document.getElementById('modal');
    document.getElementById('modalTitulo').textContent = 'Regras de compatibilidade';
    document.getElementById('modalFormulario').innerHTML = `
      <h3 style="font-size:14px;margin:0 0 6px">Tabela compatibilidade_abo</h3>
      <table><thead><tr><th>Doador</th><th>Pode doar para</th></tr></thead>
        <tbody>${linhasAbo}</tbody></table>
      <h3 style="font-size:14px;margin:14px 0 6px">Compatibilidade para transfusao (ABO + RH)</h3>
      <table><thead><tr><th>Doador</th><th>Receptores</th></tr></thead>
        <tbody>${linhasMatriz}</tbody></table>
      <p class="nota" style="margin-top:12px">
        ABO: O doa para todos | A &rarr; A e AB | B &rarr; B e AB | AB &rarr; AB.<br>
        RH: negativo doa para ambos | positivo somente para positivo.<br>
        Os valores sao os mesmos enums do Diario (<code>A/B/AB/O</code> e
        <code>positivo/negativo</code>), por isso as duas bases se comparam
        diretamente.</p>`;
    document.getElementById('btnSalvar').classList.add('oculto');
    document.getElementById('btnCancelar').textContent = 'Fechar';
    document.getElementById('btnCancelar').onclick = () => {
      modal.classList.add('oculto');
      document.getElementById('btnSalvar').classList.remove('oculto');
      document.getElementById('btnCancelar').textContent = 'Cancelar';
    };
    modal.classList.remove('oculto');
  },
};
