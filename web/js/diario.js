/* ==========================================================================
   Secao Diario de Saude Pessoal
   ========================================================================== */
const Diario = {
  usuarioId: null,
  painelAtual: 'timeline',

  async iniciar() {
    document.getElementById('btnBuscar').onclick = () => this.carregarUsuarios();
    document.getElementById('btnLimparBusca').onclick = () => {
      document.getElementById('buscaUsuario').value = '';
      this.carregarUsuarios();
    };
    document.getElementById('buscaUsuario').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') this.carregarUsuarios();
    });
    document.querySelectorAll('#abasDiario .aba-interna').forEach((botao) => {
      botao.onclick = () => this.trocarPainel(botao.dataset.painel, botao);
    });
    document.querySelector('[data-form="usuario"]').onclick = () => this.novoUsuario();
    await this.recarregar();
  },

  async recarregar() {
    await Promise.all([this.carregarCartoes(), this.carregarUsuarios()]);
  },

  async carregarCartoes() {
    const r = await API.diario.resumo();
    montarCartoes('cartoesDiario', [
      { rotulo: 'Usuarios', valor: r.usuarios },
      { rotulo: 'Consultas', valor: r.consultas },
      { rotulo: 'Exames', valor: r.exames },
      { rotulo: 'Sem resultado', valor: r.exames_sem_resultado,
        destaque: r.exames_sem_resultado > 0 },
      { rotulo: 'Doses de vacina', valor: r.doses_aplicadas },
      { rotulo: 'Alergias graves', valor: r.alergias_graves,
        destaque: r.alergias_graves > 0 },
      { rotulo: 'Diagnosticos', valor: r.diagnosticos },
      { rotulo: 'Impedimentos', valor: r.com_impedimento,
        destaque: r.com_impedimento > 0 },
    ]);
  },

  async carregarUsuarios() {
    const busca = document.getElementById('buscaUsuario').value.trim();
    const usuarios = await API.diario.usuarios(busca);
    montarTabela('listaUsuarios', usuarios, [
      { chave: 'id', titulo: 'ID' },
      { chave: 'nome', titulo: 'Nome' },
      { chave: 'sangue', titulo: 'Sangue' },
    ], {
      vazio: 'Nenhum usuario encontrado.',
      aoClicar: (linha) => this.selecionar(linha.id),
    });
    if (usuarios.length > 0) {
      const alvo = usuarios.some((u) => u.id === this.usuarioId)
        ? this.usuarioId : usuarios[0].id;
      const primeiraLinha = document.querySelector(
        `#listaUsuarios tbody tr[data-indice="${usuarios.findIndex((u) => u.id === alvo)}"]`);
      if (primeiraLinha) primeiraLinha.classList.add('selecionada');
      await this.selecionar(alvo);
    } else {
      this.usuarioId = null;
      document.getElementById('fichaUsuario').innerHTML =
        '<p class="vazio">Nenhum usuario para exibir.</p>';
    }
  },

  async selecionar(id) {
    this.usuarioId = id;
    const { usuario, perfil } = await API.diario.usuario(id);
    const alerta = perfil.impedimentos > 0
      ? `<div class="alerta">Impedimento para doacao de orgaos:
           ${esc(perfil.doencas_impeditivas)}</div>` : '';
    document.getElementById('fichaUsuario').innerHTML = `
      <h3>${esc(usuario.nome)}</h3>
      <dl>
        <div><dt>CPF</dt><dd>${esc(usuario.cpf)}</dd></div>
        <div><dt>Nascimento</dt><dd>${esc(usuario.data_nascimento)} (${esc(usuario.idade)} anos)</dd></div>
        <div><dt>Sexo</dt><dd>${esc(usuario.sexo)}</dd></div>
        <div><dt>Tipo sanguineo</dt><dd><strong>${esc(usuario.sangue)}</strong>
             (${esc(usuario.tipo_sanguineo)} / ${esc(usuario.fator_rh)})</dd></div>
        <div><dt>Cidade / UF</dt><dd>${esc(usuario.cidade || '-')} / ${esc(usuario.uf || '-')}</dd></div>
        <div><dt>Telefone</dt><dd>${esc(usuario.telefone || '-')}</dd></div>
        <div><dt>E-mail</dt><dd>${esc(usuario.email || '-')}</dd></div>
        <div><dt>Cadastrado em</dt><dd>${esc(usuario.criado_em)}</dd></div>
      </dl>
      ${alerta}
      <div class="acoes">
        <button class="btn pequeno" id="btnEditarContato">Editar contato</button>
        <button class="btn pequeno secundario" id="btnEditarSangue">Corrigir sangue</button>
      </div>`;
    document.getElementById('btnEditarContato').onclick = () => this.editarContato(usuario);
    document.getElementById('btnEditarSangue').onclick = () => this.editarSangue(usuario);
    await this.carregarPainel();
  },

  trocarPainel(nome, botao) {
    this.painelAtual = nome;
    document.querySelectorAll('#abasDiario .aba-interna')
      .forEach((b) => b.classList.remove('ativa'));
    botao.classList.add('ativa');
    document.querySelectorAll('#secao-diario .painel-interno')
      .forEach((p) => p.classList.remove('ativo'));
    document.getElementById(`painel-${nome}`).classList.add('ativo');
    this.carregarPainel();
  },

  async carregarPainel() {
    if (this.painelAtual === 'relatorios') return this.painelRelatorios();
    if (!this.usuarioId) return;
    const metodos = {
      timeline: () => this.painelTimeline(),
      alergias: () => this.painelAlergias(),
      doencas: () => this.painelDoencas(),
      consultas: () => this.painelConsultas(),
      exames: () => this.painelExames(),
      vacinas: () => this.painelVacinas(),
      metricas: () => this.painelMetricas(),
    };
    await metodos[this.painelAtual]();
  },

  _barra(botoes) {
    return `<div class="acoes">${botoes.map((b) =>
      `<button class="btn pequeno ${b.secundario ? 'secundario' : ''}" id="${b.id}">${esc(b.texto)}</button>`
    ).join('')}</div>`;
  },

  async painelTimeline() {
    const dados = await API.diario.colecao(this.usuarioId, 'timeline');
    const alvo = document.getElementById('painel-timeline');
    alvo.innerHTML = '<div id="tabelaTimeline"></div>';
    montarTabela('tabelaTimeline', dados, [
      { chave: 'data', titulo: 'Data' },
      { chave: 'evento', titulo: 'Evento', formato: (v) => etiqueta(v.toLowerCase()) },
      { chave: 'descricao', titulo: 'Descricao' },
      { chave: 'detalhe', titulo: 'Detalhe' },
    ], { vazio: 'Nenhum evento registrado.' });
  },

  async painelAlergias() {
    const dados = await API.diario.colecao(this.usuarioId, 'alergias');
    const alvo = document.getElementById('painel-alergias');
    alvo.innerHTML = `<div id="tabelaAlergias"></div>
      ${this._barra([{ id: 'btnNovaAlergia', texto: 'Registrar alergia' }])}`;
    montarTabela('tabelaAlergias', dados, [
      { chave: 'id', titulo: 'ID' },
      { chave: 'substancia', titulo: 'Substancia' },
      { chave: 'gravidade', titulo: 'Gravidade', formato: (v) => etiqueta(v) },
      { chave: 'observacao', titulo: 'Observacao' },
      { chave: 'acao', titulo: '', formato: (_, l) =>
        `<button class="btn pequeno secundario" data-alergia="${l.id}">Gravidade</button>` },
    ], { vazio: 'Nenhuma alergia registrada.', urgente: (l) => l.gravidade === 'grave' });
    document.getElementById('btnNovaAlergia').onclick = () => this.novaAlergia();
    alvo.querySelectorAll('[data-alergia]').forEach((botao) => {
      botao.onclick = (e) => {
        e.stopPropagation();
        this.alterarGravidade(Number(botao.dataset.alergia));
      };
    });
  },

  async painelDoencas() {
    const dados = await API.diario.colecao(this.usuarioId, 'doencas');
    const alvo = document.getElementById('painel-doencas');
    alvo.innerHTML = `<div id="tabelaDoencasUsuario"></div>
      ${this._barra([
        { id: 'btnNovoDiagnostico', texto: 'Registrar diagnostico' },
        { id: 'btnNovaDoenca', texto: 'Nova doenca no catalogo', secundario: true },
      ])}`;
    montarTabela('tabelaDoencasUsuario', dados, [
      { chave: 'id', titulo: 'ID' },
      { chave: 'doenca', titulo: 'Doenca' },
      { chave: 'cid', titulo: 'CID' },
      { chave: 'data_diagnostico', titulo: 'Diagnostico' },
      { chave: 'status', titulo: 'Status', formato: (v) => etiqueta(v) },
      { chave: 'impede_doacao', titulo: 'Impede doacao', formato: (v) => simNao(v) },
      { chave: 'acao', titulo: '', formato: (_, l) =>
        `<button class="btn pequeno secundario" data-diagnostico="${l.id}">Status</button>` },
    ], {
      vazio: 'Nenhum diagnostico registrado.',
      urgente: (l) => Number(l.impede_doacao) === 1 && l.status !== 'curada',
    });
    document.getElementById('btnNovoDiagnostico').onclick = () => this.novoDiagnostico();
    document.getElementById('btnNovaDoenca').onclick = () => this.novaDoenca();
    alvo.querySelectorAll('[data-diagnostico]').forEach((botao) => {
      botao.onclick = (e) => {
        e.stopPropagation();
        this.alterarStatusDoenca(Number(botao.dataset.diagnostico));
      };
    });
  },

  async painelConsultas() {
    const dados = await API.diario.colecao(this.usuarioId, 'consultas');
    const alvo = document.getElementById('painel-consultas');
    alvo.innerHTML = `<div id="tabelaConsultas"></div>
      ${this._barra([{ id: 'btnNovaConsulta', texto: 'Nova consulta' }])}`;
    montarTabela('tabelaConsultas', dados, [
      { chave: 'id', titulo: 'ID' },
      { chave: 'data_hora', titulo: 'Data/hora' },
      { chave: 'especialidade', titulo: 'Especialidade' },
      { chave: 'profissional', titulo: 'Profissional' },
      { chave: 'local', titulo: 'Local' },
      { chave: 'observacoes', titulo: 'Observacoes' },
      { chave: 'acao', titulo: '', formato: (_, l) =>
        `<button class="btn pequeno secundario" data-consulta="${l.id}">Editar</button>` },
    ], { vazio: 'Nenhuma consulta registrada.' });
    document.getElementById('btnNovaConsulta').onclick = () => this.novaConsulta();
    alvo.querySelectorAll('[data-consulta]').forEach((botao) => {
      botao.onclick = (e) => {
        e.stopPropagation();
        this.editarConsulta(Number(botao.dataset.consulta));
      };
    });
  },

  async painelExames() {
    const dados = await API.diario.colecao(this.usuarioId, 'exames');
    const alvo = document.getElementById('painel-exames');
    alvo.innerHTML = `<div id="tabelaExames"></div>
      ${this._barra([{ id: 'btnNovoExame', texto: 'Novo exame' }])}`;
    montarTabela('tabelaExames', dados, [
      { chave: 'id', titulo: 'ID' },
      { chave: 'tipo', titulo: 'Tipo' },
      { chave: 'data', titulo: 'Data' },
      { chave: 'resultado', titulo: 'Resultado',
        formato: (v) => (v ? esc(v) : '<span class="etiqueta amarela">aguardando</span>') },
      { chave: 'consulta_origem', titulo: 'Consulta de origem' },
      { chave: 'acao', titulo: '', formato: (_, l) =>
        `<button class="btn pequeno secundario" data-exame="${l.id}">Resultado</button>` },
    ], { vazio: 'Nenhum exame registrado.', urgente: (l) => !l.resultado });
    document.getElementById('btnNovoExame').onclick = () => this.novoExame();
    alvo.querySelectorAll('[data-exame]').forEach((botao) => {
      botao.onclick = (e) => {
        e.stopPropagation();
        this.lancarResultado(Number(botao.dataset.exame));
      };
    });
  },

  async painelVacinas() {
    const dados = await API.diario.colecao(this.usuarioId, 'vacinas');
    const alvo = document.getElementById('painel-vacinas');
    alvo.innerHTML = `<div id="tabelaCarteira"></div>
      ${this._barra([
        { id: 'btnNovaDose', texto: 'Registrar dose' },
        { id: 'btnNovaVacina', texto: 'Nova vacina no catalogo', secundario: true },
      ])}`;
    montarTabela('tabelaCarteira', dados, [
      { chave: 'vacina', titulo: 'Vacina' },
      { chave: 'fabricante', titulo: 'Fabricante' },
      { chave: 'dose', titulo: 'Dose' },
      { chave: 'data_aplicacao', titulo: 'Aplicacao' },
      { chave: 'lote', titulo: 'Lote' },
    ], { vazio: 'Nenhuma dose registrada.' });
    document.getElementById('btnNovaDose').onclick = () => this.novaDose();
    document.getElementById('btnNovaVacina').onclick = () => this.novaVacina();
  },

  async painelMetricas() {
    const [dados, resumo] = await Promise.all([
      API.diario.colecao(this.usuarioId, 'metricas'),
      API.diario.colecao(this.usuarioId, 'metricas-resumo'),
    ]);
    const alvo = document.getElementById('painel-metricas');
    alvo.innerHTML = `
      <h2>Medicoes registradas</h2>
      <div id="tabelaMetricas"></div>
      <h2 style="margin-top:16px">Resumo por tipo</h2>
      <div id="tabelaResumoMetricas"></div>
      ${this._barra([{ id: 'btnNovaMetrica', texto: 'Registrar metrica' }])}`;
    montarTabela('tabelaMetricas', dados, [
      { chave: 'tipo', titulo: 'Tipo' },
      { chave: 'valor', titulo: 'Valor' },
      { chave: 'unidade', titulo: 'Unidade' },
      { chave: 'data_hora', titulo: 'Data/hora' },
    ], { vazio: 'Nenhuma metrica registrada.' });
    montarTabela('tabelaResumoMetricas', resumo, [
      { chave: 'tipo', titulo: 'Tipo' },
      { chave: 'medicoes', titulo: 'Medicoes' },
      { chave: 'minimo', titulo: 'Minimo' },
      { chave: 'maximo', titulo: 'Maximo' },
      { chave: 'media', titulo: 'Media' },
      { chave: 'unidade', titulo: 'Unidade' },
      { chave: 'ultima', titulo: 'Ultima' },
    ], { vazio: 'Nenhuma metrica registrada.' });
    document.getElementById('btnNovaMetrica').onclick = () => this.novaMetrica();
  },

  async painelRelatorios() {
    const r = await API.diario.relatorios();
    document.getElementById('painel-relatorios').innerHTML = `
      <div class="grade-dois">
        <div class="painel"><h2>Alergias graves e moderadas</h2><div id="relAlergias"></div></div>
        <div class="painel"><h2>Impedimentos para doacao</h2><div id="relImpedimentos"></div></div>
        <div class="painel"><h2>Exames aguardando resultado</h2><div id="relExames"></div></div>
        <div class="painel"><h2>Cobertura vacinal</h2><div id="relVacinas"></div></div>
        <div class="painel"><h2>Distribuicao por tipo sanguineo</h2><div id="relSangue"></div></div>
        <div class="painel"><h2>Consultas por especialidade</h2><div id="relEspecialidades"></div></div>
      </div>
      <div class="painel"><h2>Perfil de doacao (view compartilhada com a Central)</h2>
        <div id="relPerfil"></div></div>`;
    montarTabela('relAlergias', r.alergias_graves, [
      { chave: 'usuario', titulo: 'Usuario' },
      { chave: 'substancia', titulo: 'Substancia' },
      { chave: 'gravidade', titulo: 'Gravidade', formato: (v) => etiqueta(v) },
    ], { urgente: (l) => l.gravidade === 'grave' });
    montarTabela('relImpedimentos', r.impedimentos, [
      { chave: 'usuario', titulo: 'Usuario' },
      { chave: 'doenca', titulo: 'Doenca' },
      { chave: 'cid', titulo: 'CID' },
      { chave: 'status', titulo: 'Status', formato: (v) => etiqueta(v) },
    ], { vazio: 'Nenhum impedimento registrado.' });
    montarTabela('relExames', r.exames_sem_resultado, [
      { chave: 'usuario', titulo: 'Usuario' },
      { chave: 'tipo', titulo: 'Exame' },
      { chave: 'data', titulo: 'Data' },
    ], { vazio: 'Nenhum exame pendente.' });
    montarTabela('relVacinas', r.cobertura_vacinal, [
      { chave: 'vacina', titulo: 'Vacina' },
      { chave: 'usuarios', titulo: 'Usuarios' },
      { chave: 'doses', titulo: 'Doses' },
      { chave: 'ultima_aplicacao', titulo: 'Ultima' },
    ]);
    montarTabela('relSangue', r.distribuicao_sanguinea, [
      { chave: 'sangue', titulo: 'Sangue' },
      { chave: 'usuarios', titulo: 'Usuarios' },
    ]);
    montarTabela('relEspecialidades', r.consultas_por_especialidade, [
      { chave: 'especialidade', titulo: 'Especialidade' },
      { chave: 'total', titulo: 'Total' },
      { chave: 'ultima', titulo: 'Ultima' },
    ]);
    montarTabela('relPerfil', r.perfil_doacao, [
      { chave: 'usuario_id', titulo: 'ID' },
      { chave: 'nome', titulo: 'Nome' },
      { chave: 'sangue', titulo: 'Sangue' },
      { chave: 'impedimentos', titulo: 'Impedimentos' },
      { chave: 'doencas_impeditivas', titulo: 'Doencas impeditivas' },
      { chave: 'alergias_graves', titulo: 'Alergias graves' },
    ], { urgente: (l) => l.impedimentos > 0 });
  },

  /* ----------------------------------------------------------- acoes */
  async novoUsuario() {
    const e = API.enums;
    const dados = await abrirFormulario('Novo usuario', [
      { chave: 'nome', rotulo: 'Nome completo' },
      { chave: 'cpf', rotulo: 'CPF (somente digitos)' },
      { chave: 'data_nascimento', rotulo: 'Nascimento', tipo: 'data' },
      { chave: 'sexo', rotulo: 'Sexo', tipo: 'opcao', opcoes: e.sexo },
      { chave: 'tipo_sanguineo', rotulo: 'Tipo sanguineo', tipo: 'opcao', opcoes: e.tipo_sanguineo },
      { chave: 'fator_rh', rotulo: 'Fator RH', tipo: 'opcao', opcoes: e.fator_rh },
      { chave: 'cidade', rotulo: 'Cidade', obrigatorio: false },
      { chave: 'uf', rotulo: 'UF', obrigatorio: false },
      { chave: 'email', rotulo: 'E-mail', obrigatorio: false },
      { chave: 'telefone', rotulo: 'Telefone', obrigatorio: false },
    ]);
    if (!dados) return;
    const criado = await tentar(() => API.diario.criarUsuario(dados), 'Usuario cadastrado.');
    if (criado) {
      this.usuarioId = criado.id;
      await this.recarregar();
    }
  },

  async editarContato(usuario) {
    const dados = await abrirFormulario('Atualizar contato', [
      { chave: 'telefone', rotulo: 'Telefone', obrigatorio: false, padrao: usuario.telefone },
      { chave: 'email', rotulo: 'E-mail', obrigatorio: false, padrao: usuario.email },
      { chave: 'cidade', rotulo: 'Cidade', obrigatorio: false, padrao: usuario.cidade },
      { chave: 'uf', rotulo: 'UF', obrigatorio: false, padrao: usuario.uf },
    ]);
    if (!dados) return;
    if (await tentar(() => API.diario.atualizarUsuario(usuario.id, dados), 'Contato atualizado.')) {
      await this.selecionar(usuario.id);
    }
  },

  async editarSangue(usuario) {
    const e = API.enums;
    const dados = await abrirFormulario('Corrigir tipo sanguineo', [
      { chave: 'tipo_sanguineo', rotulo: 'Tipo sanguineo', tipo: 'opcao',
        opcoes: e.tipo_sanguineo, padrao: usuario.tipo_sanguineo },
      { chave: 'fator_rh', rotulo: 'Fator RH', tipo: 'opcao',
        opcoes: e.fator_rh, padrao: usuario.fator_rh },
    ]);
    if (!dados) return;
    if (await tentar(() => API.diario.atualizarUsuario(usuario.id, dados), 'Tipo sanguineo atualizado.')) {
      await this.recarregar();
    }
  },

  async novaAlergia() {
    const dados = await abrirFormulario('Registrar alergia', [
      { chave: 'substancia', rotulo: 'Substancia' },
      { chave: 'gravidade', rotulo: 'Gravidade', tipo: 'opcao',
        opcoes: API.enums.gravidade_alergia },
      { chave: 'observacao', rotulo: 'Observacao', tipo: 'memo', obrigatorio: false },
    ]);
    if (!dados) return;
    if (await tentar(() => API.diario.criarEm(this.usuarioId, 'alergias', dados),
                     'Alergia registrada.')) {
      await this.painelAlergias();
      await this.carregarCartoes();
    }
  },

  async alterarGravidade(id) {
    const dados = await abrirFormulario('Alterar gravidade', [
      { chave: 'gravidade', rotulo: 'Gravidade', tipo: 'opcao',
        opcoes: API.enums.gravidade_alergia },
    ]);
    if (!dados) return;
    if (await tentar(() => API.diario.atualizarAlergia(id, dados), 'Gravidade atualizada.')) {
      await this.painelAlergias();
      await this.carregarCartoes();
    }
  },

  async novaDoenca() {
    const dados = await abrirFormulario('Nova doenca no catalogo', [
      { chave: 'nome', rotulo: 'Nome da doenca' },
      { chave: 'cid', rotulo: 'CID', obrigatorio: false },
      { chave: 'impede_doacao', rotulo: 'Impede doacao de orgaos', tipo: 'opcao',
        opcoes: ['nao', 'sim'] },
    ]);
    if (!dados) return;
    dados.impede_doacao = dados.impede_doacao === 'sim' ? 1 : 0;
    await tentar(() => API.diario.criarDoenca(dados), 'Doenca cadastrada no catalogo.');
  },

  async novoDiagnostico() {
    const doencas = await API.diario.doencas();
    if (doencas.length === 0) {
      avisar('Cadastre uma doenca no catalogo primeiro.', 'erro');
      return;
    }
    const dados = await abrirFormulario('Registrar diagnostico', [
      { chave: 'doenca_id', rotulo: 'Doenca', tipo: 'lista',
        itens: doencas.map((d) => [d.id, `${d.nome}${d.cid ? ` (${d.cid})` : ''}` +
          `${Number(d.impede_doacao) ? ' [impede doacao]' : ''}`]) },
      { chave: 'data_diagnostico', rotulo: 'Data do diagnostico', tipo: 'data', padrao: hoje() },
      { chave: 'status', rotulo: 'Status', tipo: 'opcao', opcoes: API.enums.status_doenca },
    ]);
    if (!dados) return;
    if (await tentar(() => API.diario.criarEm(this.usuarioId, 'doencas', dados),
                     'Diagnostico registrado.')) {
      await this.selecionar(this.usuarioId);
      await this.carregarCartoes();
    }
  },

  async alterarStatusDoenca(id) {
    const dados = await abrirFormulario('Alterar status do diagnostico', [
      { chave: 'status', rotulo: 'Status', tipo: 'opcao', opcoes: API.enums.status_doenca },
    ]);
    if (!dados) return;
    if (await tentar(() => API.diario.atualizarDiagnostico(id, dados), 'Status atualizado.')) {
      await this.selecionar(this.usuarioId);
      await this.carregarCartoes();
    }
  },

  async novaConsulta() {
    const dados = await abrirFormulario('Nova consulta', [
      { chave: 'data_hora', rotulo: 'Data e hora', tipo: 'data_hora', padrao: `${hoje()} 09:00` },
      { chave: 'especialidade', rotulo: 'Especialidade' },
      { chave: 'profissional', rotulo: 'Profissional', obrigatorio: false },
      { chave: 'local', rotulo: 'Local', obrigatorio: false },
      { chave: 'observacoes', rotulo: 'Observacoes', tipo: 'memo', obrigatorio: false },
    ]);
    if (!dados) return;
    if (await tentar(() => API.diario.criarEm(this.usuarioId, 'consultas', dados),
                     'Consulta registrada.')) {
      await this.painelConsultas();
      await this.carregarCartoes();
    }
  },

  async editarConsulta(id) {
    const dados = await abrirFormulario('Atualizar observacoes', [
      { chave: 'observacoes', rotulo: 'Observacoes', tipo: 'memo' },
    ]);
    if (!dados) return;
    if (await tentar(() => API.diario.atualizarConsulta(id, dados), 'Consulta atualizada.')) {
      await this.painelConsultas();
    }
  },

  async novoExame() {
    const consultas = await API.diario.colecao(this.usuarioId, 'consultas');
    const itens = [[0, '(sem vinculo com consulta)']].concat(
      consultas.map((c) => [c.id, `${c.data_hora} - ${c.especialidade || 'consulta'}`]));
    const dados = await abrirFormulario('Novo exame', [
      { chave: 'tipo', rotulo: 'Tipo de exame' },
      { chave: 'data', rotulo: 'Data', tipo: 'data', padrao: hoje() },
      { chave: 'resultado', rotulo: 'Resultado', tipo: 'memo', obrigatorio: false },
      { chave: 'consulta_id', rotulo: 'Consulta de origem', tipo: 'lista', itens },
    ]);
    if (!dados) return;
    if (!dados.consulta_id) dados.consulta_id = null;
    if (await tentar(() => API.diario.criarEm(this.usuarioId, 'exames', dados),
                     'Exame registrado.')) {
      await this.painelExames();
      await this.carregarCartoes();
    }
  },

  async lancarResultado(id) {
    const dados = await abrirFormulario(`Lancar resultado do exame ${id}`, [
      { chave: 'resultado', rotulo: 'Resultado', tipo: 'memo' },
    ]);
    if (!dados) return;
    if (await tentar(() => API.diario.lancarResultado(id, dados), 'Resultado lancado.')) {
      await this.painelExames();
      await this.carregarCartoes();
    }
  },

  async novaVacina() {
    const dados = await abrirFormulario('Nova vacina no catalogo', [
      { chave: 'nome', rotulo: 'Nome da vacina' },
      { chave: 'fabricante', rotulo: 'Fabricante', obrigatorio: false },
    ]);
    if (!dados) return;
    await tentar(() => API.diario.criarVacina(dados), 'Vacina cadastrada.');
  },

  async novaDose() {
    const vacinas = await API.diario.vacinas();
    if (vacinas.length === 0) {
      avisar('Cadastre uma vacina no catalogo primeiro.', 'erro');
      return;
    }
    const dados = await abrirFormulario('Registrar dose de vacina', [
      { chave: 'vacina_id', rotulo: 'Vacina', tipo: 'lista',
        itens: vacinas.map((v) => [v.id, `${v.nome}${v.fabricante ? ` - ${v.fabricante}` : ''}`]) },
      { chave: 'dose', rotulo: 'Dose (1a dose, reforco, anual...)', padrao: '1a dose' },
      { chave: 'data_aplicacao', rotulo: 'Data de aplicacao', tipo: 'data', padrao: hoje() },
      { chave: 'lote', rotulo: 'Lote', obrigatorio: false },
    ]);
    if (!dados) return;
    if (await tentar(() => API.diario.criarEm(this.usuarioId, 'vacinas', dados),
                     'Dose registrada.')) {
      await this.painelVacinas();
      await this.carregarCartoes();
    }
  },

  async novaMetrica() {
    const dados = await abrirFormulario('Registrar metrica de saude', [
      { chave: 'tipo', rotulo: 'Tipo (Peso, Glicemia, Pressao...)' },
      { chave: 'valor', rotulo: 'Valor', tipo: 'numero' },
      { chave: 'unidade', rotulo: 'Unidade (kg, mg/dL, mmHg)' },
      { chave: 'data_hora', rotulo: 'Data e hora', tipo: 'data_hora', padrao: `${hoje()} 08:00` },
    ]);
    if (!dados) return;
    if (await tentar(() => API.diario.criarEm(this.usuarioId, 'metricas', dados),
                     'Metrica registrada.')) {
      await this.painelMetricas();
      await this.carregarCartoes();
    }
  },
};
