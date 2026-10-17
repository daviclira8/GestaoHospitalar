/* ==========================================================================
   Componentes de interface: tabela, cartoes, modal de formulario e avisos
   ========================================================================== */

/** Escapa texto antes de inserir no HTML. */
function esc(valor) {
  if (valor === null || valor === undefined || valor === '') return '';
  return String(valor)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

/**
 * Monta uma tabela HTML.
 * colunas: [{ chave, titulo, formato? }]
 * opcoes: { vazio, urgente(linha), aoClicar(linha, tr), idChave }
 */
function montarTabela(destino, dados, colunas, opcoes = {}) {
  const alvo = typeof destino === 'string' ? document.getElementById(destino) : destino;
  if (!alvo) return;

  if (!dados || dados.length === 0) {
    alvo.innerHTML = `<p class="vazio">${esc(opcoes.vazio || 'Nenhum registro encontrado.')}</p>`;
    return;
  }

  const cabecalho = colunas.map((c) => `<th>${esc(c.titulo)}</th>`).join('');
  const corpo = dados.map((linha, indice) => {
    const celulas = colunas.map((c) => {
      const bruto = linha[c.chave];
      const conteudo = c.formato ? c.formato(bruto, linha) : esc(bruto);
      return `<td>${conteudo}</td>`;
    }).join('');
    const classes = [];
    if (opcoes.urgente && opcoes.urgente(linha)) classes.push('urgente');
    if (opcoes.aoClicar) classes.push('clicavel');
    return `<tr data-indice="${indice}" class="${classes.join(' ')}">${celulas}</tr>`;
  }).join('');

  alvo.innerHTML = `<table><thead><tr>${cabecalho}</tr></thead><tbody>${corpo}</tbody></table>`;

  if (opcoes.aoClicar) {
    alvo.querySelectorAll('tbody tr').forEach((tr) => {
      tr.addEventListener('click', () => {
        alvo.querySelectorAll('tbody tr').forEach((o) => o.classList.remove('selecionada'));
        tr.classList.add('selecionada');
        opcoes.aoClicar(dados[Number(tr.dataset.indice)], tr);
      });
    });
  }
}

/** Cartoes de indicadores a partir de [{ rotulo, valor, destaque }]. */
function montarCartoes(destino, itens) {
  const alvo = typeof destino === 'string' ? document.getElementById(destino) : destino;
  if (!alvo) return;
  alvo.innerHTML = itens.map((i) => `
    <div class="cartao ${i.destaque ? 'destaque' : ''}">
      <div class="valor">${esc(i.valor)}</div>
      <div class="rotulo">${esc(i.rotulo)}</div>
    </div>`).join('');
}

/** Etiqueta colorida para status/prioridade/gravidade. */
function etiqueta(valor) {
  if (valor === null || valor === undefined || valor === '') return '';
  const texto = String(valor);
  const vermelhas = ['grave', 'emergencia', 'ativa', 'obito', 'rejeicao', 'DIVERGENTE'];
  const amarelas = ['moderada', 'alta', 'reservado', 'suspenso', 'controlada',
                    'em_acompanhamento'];
  const verdes = ['leve', 'disponivel', 'sucesso', 'curada', 'confere'];
  let cor = 'cinza';
  if (vermelhas.includes(texto)) cor = 'vermelha';
  else if (amarelas.includes(texto)) cor = 'amarela';
  else if (verdes.includes(texto)) cor = 'verde';
  return `<span class="etiqueta ${cor}">${esc(texto)}</span>`;
}

/** Sim/nao a partir de 0/1. */
function simNao(valor) {
  return Number(valor) ? '<span class="etiqueta vermelha">sim</span>'
                       : '<span class="etiqueta cinza">nao</span>';
}

/* ------------------------------------------------------------------ avisos */
let temporizadorAviso = null;
function avisar(mensagem, tipo = 'ok') {
  const caixa = document.getElementById('aviso');
  caixa.textContent = mensagem;
  caixa.className = `aviso ${tipo}`;
  clearTimeout(temporizadorAviso);
  temporizadorAviso = setTimeout(() => caixa.classList.add('oculto'), 4500);
}

/* ------------------------------------------------------------------- modal */
/**
 * Abre um formulario modal e devolve uma Promise com os dados ou null.
 * campos: [{ chave, rotulo, tipo, opcoes, itens, padrao, obrigatorio }]
 *   tipo: texto | memo | data | data_hora | numero | opcao | lista
 */
function abrirFormulario(titulo, campos) {
  return new Promise((resolve) => {
    const modal = document.getElementById('modal');
    const formulario = document.getElementById('modalFormulario');
    document.getElementById('modalTitulo').textContent = titulo;

    formulario.innerHTML = campos.map((campo) => {
      const obrigatorio = campo.obrigatorio !== false;
      const rotulo = `<span>${esc(campo.rotulo)}${obrigatorio ? ' *' : ''}</span>`;
      const valor = campo.padrao === null || campo.padrao === undefined
        ? '' : String(campo.padrao);

      if (campo.tipo === 'opcao' || campo.tipo === 'lista') {
        const itens = campo.tipo === 'opcao'
          ? campo.opcoes.map((o) => ({ valor: o, texto: o }))
          : campo.itens.map((i) => ({ valor: i[0], texto: `${i[0]} - ${i[1]}` }));
        const opcoes = itens.map((i) => {
          const selecionado = String(i.valor) === valor ? ' selected' : '';
          return `<option value="${esc(i.valor)}"${selecionado}>${esc(i.texto)}</option>`;
        }).join('');
        return `<label>${rotulo}<select name="${esc(campo.chave)}">${opcoes}</select></label>`;
      }
      if (campo.tipo === 'memo') {
        return `<label>${rotulo}<textarea name="${esc(campo.chave)}">${esc(valor)}</textarea></label>`;
      }
      const marcador = campo.tipo === 'data' ? 'YYYY-MM-DD'
        : campo.tipo === 'data_hora' ? 'YYYY-MM-DD HH:MM' : '';
      const tipoEntrada = campo.tipo === 'numero' ? 'number' : 'text';
      const passo = campo.tipo === 'numero' ? ' step="any"' : '';
      return `<label>${rotulo}<input type="${tipoEntrada}"${passo} name="${esc(campo.chave)}"
                 value="${esc(valor)}" placeholder="${marcador}"></label>`;
    }).join('');

    const fechar = (resultado) => {
      modal.classList.add('oculto');
      document.getElementById('btnSalvar').onclick = null;
      document.getElementById('btnCancelar').onclick = null;
      formulario.onsubmit = null;
      resolve(resultado);
    };

    const salvar = () => {
      const dados = {};
      for (const campo of campos) {
        const elemento = formulario.elements[campo.chave];
        let valor = elemento ? String(elemento.value).trim() : '';
        if (!valor) {
          if (campo.obrigatorio !== false) {
            avisar(`Preencha o campo "${campo.rotulo}".`, 'erro');
            if (elemento) elemento.focus();
            return;
          }
          dados[campo.chave] = null;
          continue;
        }
        if (campo.tipo === 'data' && !/^\d{4}-\d{2}-\d{2}$/.test(valor)) {
          avisar(`Use o formato YYYY-MM-DD em "${campo.rotulo}".`, 'erro');
          return;
        }
        if (campo.tipo === 'data_hora' && !/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(valor)) {
          avisar(`Use o formato YYYY-MM-DD HH:MM em "${campo.rotulo}".`, 'erro');
          return;
        }
        if (campo.tipo === 'lista') valor = Number(valor);
        if (campo.tipo === 'numero') valor = Number(String(valor).replace(',', '.'));
        dados[campo.chave] = valor;
      }
      fechar(dados);
    };

    document.getElementById('btnSalvar').onclick = salvar;
    document.getElementById('btnCancelar').onclick = () => fechar(null);
    formulario.onsubmit = (evento) => { evento.preventDefault(); salvar(); };

    modal.classList.remove('oculto');
    const primeiro = formulario.querySelector('input, select, textarea');
    if (primeiro) primeiro.focus();
  });
}

/** Executa uma acao assincrona tratando o erro em um aviso. */
async function tentar(acao, mensagemOk) {
  try {
    const resultado = await acao();
    if (mensagemOk) avisar(mensagemOk, 'ok');
    return resultado;
  } catch (erro) {
    avisar(erro.message, 'erro');
    return null;
  }
}

/** Preenche um <select> com valores simples. */
function preencherSelect(elemento, valores, selecionado) {
  elemento.innerHTML = valores.map((v) => {
    const texto = typeof v === 'object' ? v.texto : v;
    const valor = typeof v === 'object' ? v.valor : v;
    return `<option value="${esc(valor)}"${String(valor) === String(selecionado) ? ' selected' : ''}>${esc(texto)}</option>`;
  }).join('');
}

/** Data de hoje em YYYY-MM-DD. */
function hoje() {
  return new Date().toISOString().slice(0, 10);
}
