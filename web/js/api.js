/* ==========================================================================
   Acesso a API HTTP (API/api.py)
   ========================================================================== */
const API = {

  async requisicao(rota, opcoes = {}) {
    const resposta = await fetch(`/api${rota}`, {
      headers: { 'Content-Type': 'application/json' },
      ...opcoes,
    });
    let dados = null;
    try {
      dados = await resposta.json();
    } catch (erro) {
      throw new Error(`Resposta invalida do servidor (HTTP ${resposta.status})`);
    }
    if (!resposta.ok) {
      throw new Error(dados && dados.erro ? dados.erro : `HTTP ${resposta.status}`);
    }
    return dados;
  },

  get(rota) {
    return this.requisicao(rota);
  },

  post(rota, corpo) {
    return this.requisicao(rota, { method: 'POST', body: JSON.stringify(corpo) });
  },

  patch(rota, corpo) {
    return this.requisicao(rota, { method: 'PATCH', body: JSON.stringify(corpo) });
  },

  // --- enums compartilhados pelos dois bancos ---------------------------
  enums: null,
  async carregarEnums() {
    if (!this.enums) {
      this.enums = await this.get('/enums');
    }
    return this.enums;
  },

  // --- Diario de Saude --------------------------------------------------
  diario: {
    resumo: () => API.get('/diario/resumo'),
    usuarios: (busca) => API.get(`/diario/usuarios${busca ? `?busca=${encodeURIComponent(busca)}` : ''}`),
    usuario: (id) => API.get(`/diario/usuarios/${id}`),
    colecao: (id, nome) => API.get(`/diario/usuarios/${id}/${nome}`),
    doencas: () => API.get('/diario/doencas'),
    vacinas: () => API.get('/diario/vacinas'),
    relatorios: () => API.get('/diario/relatorios'),
    criarUsuario: (dados) => API.post('/diario/usuarios', dados),
    criarEm: (id, nome, dados) => API.post(`/diario/usuarios/${id}/${nome}`, dados),
    criarDoenca: (dados) => API.post('/diario/doencas', dados),
    criarVacina: (dados) => API.post('/diario/vacinas', dados),
    atualizarUsuario: (id, dados) => API.patch(`/diario/usuarios/${id}`, dados),
    atualizarAlergia: (id, dados) => API.patch(`/diario/alergias/${id}`, dados),
    atualizarDiagnostico: (id, dados) => API.patch(`/diario/diagnosticos/${id}`, dados),
    atualizarConsulta: (id, dados) => API.patch(`/diario/consultas/${id}`, dados),
    lancarResultado: (id, dados) => API.patch(`/diario/exames/${id}`, dados),
  },

  // --- Central de Transplantes -----------------------------------------
  central: {
    painel: () => API.get('/central/painel'),
    hospitais: () => API.get('/central/hospitais'),
    tiposOrgao: () => API.get('/central/tipos-orgao'),
    doadores: () => API.get('/central/doadores'),
    receptores: () => API.get('/central/receptores'),
    orgaos: (status) => API.get(`/central/orgaos${status ? `?status=${status}` : ''}`),
    fila: (status, tipoOrgaoId) => {
      const partes = [];
      if (status) partes.push(`status=${status}`);
      if (tipoOrgaoId) partes.push(`tipo_orgao_id=${tipoOrgaoId}`);
      return API.get(`/central/fila${partes.length ? `?${partes.join('&')}` : ''}`);
    },
    transplantes: () => API.get('/central/transplantes'),
    compatibilidade: () => API.get('/central/compatibilidade'),
    compativeis: (orgaoId) => API.get(`/central/orgaos/${orgaoId}/compativeis`),
    candidatos: () => API.get('/central/candidatos'),
    semCompativel: () => API.get('/central/sem-compativel'),
    demanda: () => API.get('/central/demanda'),
    porHospital: () => API.get('/central/hospitais-transplantes'),
    regras: () => API.get('/central/regras'),
    criarDoador: (dados) => API.post('/central/doadores', dados),
    criarReceptor: (dados) => API.post('/central/receptores', dados),
    criarOrgao: (dados) => API.post('/central/orgaos', dados),
    inserirNaFila: (dados) => API.post('/central/fila', dados),
    efetivarTransplante: (dados) => API.post('/central/transplantes', dados),
    atualizarFila: (id, dados) => API.patch(`/central/fila/${id}`, dados),
    atualizarTransplante: (id, dados) => API.patch(`/central/transplantes/${id}`, dados),
  },

  // --- Integracao entre os dois bancos ---------------------------------
  integracao: {
    resumo: () => API.get('/integracao/resumo'),
    usuarios: () => API.get('/integracao/usuarios'),
    conferencia: () => API.get('/integracao/conferencia'),
    divergencias: () => API.get('/integracao/divergencias'),
    alertas: () => API.get('/integracao/alertas'),
    compatibilidadeUsuario: (id) => API.get(`/integracao/usuarios/${id}/compatibilidade`),
  },
};
