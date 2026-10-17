/* ==========================================================================
   Inicializacao e navegacao entre as secoes
   ========================================================================== */
const Aplicacao = {
  secaoAtual: 'diario',
  iniciadas: {},

  async iniciar() {
    try {
      await API.carregarEnums();
    } catch (erro) {
      avisar(`Nao foi possivel falar com a API: ${erro.message}`, 'erro');
      return;
    }

    document.querySelectorAll('#navPrincipal .aba').forEach((botao) => {
      botao.onclick = () => this.trocarSecao(botao.dataset.secao, botao);
    });

    document.getElementById('modal').addEventListener('click', (evento) => {
      if (evento.target.id === 'modal') document.getElementById('btnCancelar').click();
    });
    document.addEventListener('keydown', (evento) => {
      const modal = document.getElementById('modal');
      if (evento.key === 'Escape' && !modal.classList.contains('oculto')) {
        document.getElementById('btnCancelar').click();
      }
    });

    await this.abrir('diario');
  },

  async abrir(secao) {
    const modulos = { diario: Diario, central: Central, integracao: Integracao };
    const modulo = modulos[secao];
    try {
      if (!this.iniciadas[secao]) {
        await modulo.iniciar();
        this.iniciadas[secao] = true;
      } else {
        await modulo.recarregar();
      }
    } catch (erro) {
      avisar(erro.message, 'erro');
    }
  },

  async trocarSecao(secao, botao) {
    this.secaoAtual = secao;
    document.querySelectorAll('#navPrincipal .aba').forEach((b) => b.classList.remove('ativa'));
    botao.classList.add('ativa');
    document.querySelectorAll('.secao').forEach((s) => s.classList.remove('ativa'));
    document.getElementById(`secao-${secao}`).classList.add('ativa');
    await this.abrir(secao);
  },
};

document.addEventListener('DOMContentLoaded', () => Aplicacao.iniciar());
