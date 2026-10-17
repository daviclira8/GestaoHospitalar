/* ==========================================================================
   Seção Integração: a Central consulta o Diário por um gateway somente de leitura.
   ========================================================================== */
const Integracao = {

  async iniciar() {
    await this.recarregar();
  },

  async recarregar() {
    const [resumo, usuarios, conferencia, alertas, divergencias] = await Promise.all([
      API.integracao.resumo(),
      API.integracao.usuarios(),
      API.integracao.conferencia(),
      API.integracao.alertas(),
      API.integracao.divergencias(),
    ]);

    montarCartoes('cartoesIntegracao', [
      { rotulo: 'Usuarios no Diario', valor: resumo.usuarios_diario },
      { rotulo: 'Doadores vinculados', valor: resumo.doadores_vinculados },
      { rotulo: 'Receptores vinculados', valor: resumo.receptores_vinculados },
      { rotulo: 'Com impedimento', valor: resumo.com_impedimento,
        destaque: resumo.com_impedimento > 0 },
      { rotulo: 'Divergencias de sangue', valor: divergencias.length,
        destaque: divergencias.length > 0 },
    ]);

    montarTabela('tabelaUsuariosDiario', usuarios, [
      { chave: 'usuario_id', titulo: 'ID' },
      { chave: 'nome', titulo: 'Nome' },
      { chave: 'sangue', titulo: 'Sangue' },
      { chave: 'cidade', titulo: 'Cidade' },
      { chave: 'impedimentos', titulo: 'Impedimentos' },
      { chave: 'doencas_impeditivas', titulo: 'Doencas impeditivas' },
      { chave: 'e_doador', titulo: 'Doador', formato: (v) => simNao(v) },
      { chave: 'e_receptor', titulo: 'Receptor', formato: (v) => simNao(v) },
    ], {
      vazio: 'Nenhum usuario no Diario de Saude.',
      urgente: (l) => l.impedimentos > 0,
      aoClicar: (linha) => this.compatibilidadeUsuario(linha),
    });

    const todos = conferencia.doadores.map((d) => ({ ...d, origem: 'doador' }))
      .concat(conferencia.receptores.map((r) => ({ ...r, origem: 'receptor' })));
    montarTabela('tabelaConferencia', todos, [
      { chave: 'origem', titulo: 'Origem' },
      { chave: 'nome', titulo: 'Nome' },
      { chave: 'sangue_central', titulo: 'Tipagem na Central' },
      { chave: 'sangue_diario', titulo: 'Sangue no Diario' },
      { chave: 'situacao', titulo: 'Situacao', formato: (v) => etiqueta(v) },
      { chave: 'doencas_impeditivas', titulo: 'Doencas impeditivas' },
    ], {
      vazio: 'Nenhum cadastro vinculado ao Diario.',
      urgente: (l) => l.situacao === 'divergente',
    });

    montarTabela('tabelaAlertas', alertas.orgaos, [
      { chave: 'orgao_id', titulo: 'Orgao' },
      { chave: 'orgao', titulo: 'Tipo' },
      { chave: 'doador', titulo: 'Doador' },
      { chave: 'sangue', titulo: 'Sangue' },
      { chave: 'status', titulo: 'Status', formato: (v) => etiqueta(v) },
      { chave: 'doencas_impeditivas', titulo: 'Doencas impeditivas' },
      { chave: 'alergias_graves', titulo: 'Alergias graves' },
    ], {
      vazio: 'Nenhum orgao disponivel de doador com impedimento.',
      urgente: () => true,
    });
  },

  async compatibilidadeUsuario(usuario) {
    const dados = await API.integracao.compatibilidadeUsuario(usuario.usuario_id);
    const alerta = usuario.impedimentos > 0
      ? `<div class="alerta">O Diario registra impedimento para doacao:
           ${esc(usuario.doencas_impeditivas)}</div>` : '';
    document.getElementById('painelCompatUsuario').innerHTML = `
      <h2>Compatibilidade de ${esc(usuario.nome)} (${esc(usuario.sangue)})</h2>
      <p class="nota">Receptores da fila que poderiam receber um orgao desta pessoa,
         usando o tipo sanguineo registrado no Diario de Saude e a regra ABO
         <code>compatibilidade_abo</code>. O fator Rh e aplicado nas transfusoes,
         nao na compatibilidade para transplante de orgaos.</p>
      ${alerta}
      <div id="tabelaCompatUsuario"></div>`;
    montarTabela('tabelaCompatUsuario', dados, [
      { chave: 'receptor', titulo: 'Receptor' },
      { chave: 'sangue_receptor', titulo: 'Sangue' },
      { chave: 'orgao', titulo: 'Orgao aguardado' },
      { chave: 'prioridade', titulo: 'Prioridade', formato: (v) => etiqueta(v) },
      { chave: 'dias_na_fila', titulo: 'Dias na fila' },
      { chave: 'hospital', titulo: 'Hospital' },
    ], {
      vazio: 'Nenhum receptor compativel na fila de espera.',
      urgente: (l) => l.prioridade === 'emergencia',
    });
    document.getElementById('painelCompatUsuario').scrollIntoView({ behavior: 'smooth' });
  },
};
