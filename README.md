# Diário de Saúde + Central de Transplantes

Desafio de Tecnologia RAITec 2026.2. São dois sistemas integrados, cada um com o seu **próprio banco PostgreSQL**:

- **Diário de Saúde Pessoal** (`diario_saude`): histórico clínico do usuário.
- **Central Hospitalar de Transplantes e Doação de Órgãos e Sangue** (`central_transplantes`): doadores, receptores, fila, órgãos, alocações e bolsas de sangue.

A Central se liga ao Diário **apenas pelo `usuario_id`**. Ela lê do Diário o nome, o tipo sanguíneo e as doenças no momento em que precisa, e nunca grava no Diário.

## Estrutura

```
sql/                         PARTE 2 — bancos de dados
  diario/01_criacao.sql        tabelas, ENUMs, restrições, índices, views
  diario/02_povoamento.sql     20 usuários fictícios + histórico
  diario/03_operacoes.sql      consultas e INSERT/UPDATE/DELETE de exemplo
  central/01_criacao.sql       tabelas, regras ABO, funções, gatilho, views
  central/02_povoamento.sql    hospitais, órgãos, doadores, filas, bolsas
  central/03_operacoes.sql     consultas e fluxo completo de uma doação
  integracao/04_integracao_fdw.sql   (opcional) integração só com SQL
  executar_tudo.bat / .sh      cria os bancos usando o psql

backend/                     BACKEND em Python
  conexao.py                   conexão com os 2 bancos (lê o .env)
  erros.py                     exceções + tradução dos erros do banco + transações
  base.py                      conversão linha do banco -> objeto
  diario/                      INTEGRANTE 2
    modelos.py                   estruturas de dados (dataclasses)
    validacao.py                 validação dos dados de entrada
    servico.py                   DiarioService: CRUD completo
  central/                     INTEGRANTE 3
    compatibilidade.py           ALGORITMO de compatibilidade (puro, sem banco)
    integracao_diario.py         DiarioGateway: leitura do Diário (somente leitura)
    modelos.py                   estruturas de dados
    servico.py                   CentralService: cadastros, seleção, alocação, sangue

criar_bancos.py              recria os 2 bancos via Python (não precisa do psql)
demo_backend.py              roteiro da demonstração (manual de uso do backend)
tests/                       41 testes automatizados (pytest)
```

## Como rodar (Windows)

**Pré-requisitos:** Python 3.10 ou superior e PostgreSQL 14 ou superior.

```bat
cd caminho\da\pasta\desafio_saude
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.exemplo .env
```

Abra o `.env` e coloque a senha do usuário `postgres` em `PGPASSWORD`. Depois:

```bat
python criar_bancos.py          :: cria e povoa os 2 bancos
python demo_backend.py          :: demonstração completa (recria os bancos antes)
python demo_backend.py --pausar :: idem, parando a cada passo (para apresentar)
python -m pytest -q             :: roda os testes (usa bancos *_teste separados)
```

No Linux ou macOS, os comandos são os mesmos. Troque `.venv\Scripts\activate` por `source .venv/bin/activate` e `copy` por `cp`.

## Arquitetura

```
           CLI (Integrante 4)
              │          │
     DiarioService    CentralService ── compatibilidade.py (algoritmo puro)
              │          │
              │     DiarioGateway (somente leitura)
              │          │
       [diario_saude] ◄──┘        [central_transplantes]
```

- **Toda operação é uma transação.** Ou grava tudo, ou nada (`erros.transacao`).
- **Todo SQL é parametrizado** (`%s`), o que protege contra SQL injection.
- **Toda falha prevista vira `ErroDeNegocio`**, com uma mensagem pronta para mostrar ao usuário.
- **Validação em duas camadas.** O Python valida para dar uma mensagem clara, e o banco (CHECK, ENUM, UNIQUE, FK, gatilho) é a garantia final.

## Seleção de receptores (`compatibilidade.py`)

1. **Tipagem:** o receptor precisa ter tipo sanguíneo registrado no Diário.
2. **ABO:** O→todos · A→A, AB · B→B, AB · AB→AB. Em órgãos sólidos, o Rh não é critério.
3. **Logística:** 1 h de preparo + deslocamento (terrestre a 60 km/h até 150 km; aéreo a 400 km/h acima disso). O resultado precisa ser menor ou igual ao tempo de isquemia restante.
4. **Ordem de prioridade:** urgência ↓ → mesmo tipo sanguíneo → dias de espera ↓ → distância ↑.

Na **transfusão de sangue**, vale ABO **+ Rh**: um receptor Rh- só recebe Rh-. A **triagem do doador de sangue** usa idade (16–69 anos), peso (≥ 50 kg, da última métrica do Diário), intervalo desde a última doação (60 dias para homens, 90 para mulheres) e doenças que impedem a doação.

## Métodos para a CLI (Integrante 4)

| Diário (`DiarioService`) | Central (`CentralService`) |
|---|---|
| `cadastrar_usuario`, `buscar_usuario`, `buscar_por_cpf`, `listar_usuarios` | `listar_hospitais`, `listar_tipos_orgao` |
| `atualizar_usuario`, `registrar_tipagem`, `excluir_usuario` | `cadastrar_receptor`, `incluir_na_fila`, `atualizar_urgencia`, `remover_da_fila`, `fila_ativa` |
| `adicionar_alergia`, `listar_alergias`, `remover_alergia` | `cadastrar_doador`, `listar_doadores`, `reavaliar_doadores` |
| `listar_catalogo_doencas`, `registrar_diagnostico`, `atualizar_status_doenca`, `listar_diagnosticos` | `registrar_orgao`, `orgaos_disponiveis` |
| `listar_catalogo_vacinas`, `registrar_vacina`, `cartao_vacinacao` | `selecionar_receptores`, `alocar_orgao`, `alocar_melhor_receptor` |
| `registrar_consulta`, `listar_consultas`, `registrar_exame`, `listar_exames` | `registrar_entrega`, `concluir_transplante`, `cancelar_alocacao`, `processos` |
| `registrar_metrica`, `historico_metrica`, `metricas_por_tipo`, `ultima_metrica` | `registrar_doacao_sangue`, `estoque_sangue`, `bolsas_compativeis`, `utilizar_bolsa` |
| `ficha`, `linha_do_tempo`, `prontuario` | `executar_manutencao`, `verificar_integridade` |

Padrão de uso na CLI:

```python
from backend.diario.servico import DiarioService
from backend.central.servico import CentralService
from backend.erros import ErroDeNegocio

with DiarioService() as diario, CentralService() as central:
    try:
        resultado = central.selecionar_receptores(int(input("Id do órgão: ")))
        ...
    except ErroDeNegocio as erro:
        print("Erro:", erro)
```

O `demo_backend.py` mostra cada método em uso e tem uma função `tabela()` que a CLI pode reaproveitar.

## Adições em relação ao DER original

- Tabela `compatibilidade_abo`: a regra ABO é guardada como dado.
- ENUMs `tipo_sanguineo` e `fator_rh` também na Central, para comparar os valores lidos do Diário.
- Índices únicos parciais:
  - um receptor não pode estar duas vezes aguardando o mesmo órgão;
  - o 1:1 entre órgão e alocação vale só para alocações não canceladas.
