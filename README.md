# Gestao Hospitalar

Trabalho de Banco de Dados com dois sistemas relacionais independentes:

1. **Diario de Saude Pessoal** - historico de saude do usuario (tipo sanguineo,
   fator RH, alergias, consultas, exames e vacinas).
2. **Central Hospitalar de Transplantes** - doadores, receptores, orgaos
   disponiveis, filas de espera e identificacao de compatibilidades.

Cada sistema pode ser usado por **menus interativos de terminal** ou pela
**interface grafica em Python (Tkinter)**.

- **SGBD:** SQLite 3 (embutido no Python, nao precisa de servidor)
- **Linguagem:** Python 3 (apenas biblioteca padrao)
- **Modelagem (DER/MER):** [docs/DER.md](docs/DER.md)

---

## Como executar

Nao ha dependencias para instalar. Na raiz do projeto:

```bash
python3 main.py
```

O menu inicial permite abrir os menus de terminal dos dois sistemas, a
interface grafica ou apenas criar/verificar os bancos.

Tambem e possivel iniciar cada parte diretamente:

```bash
python3 DiarioPessoal/DiarioPessoal.py        # menus do Sistema 1 (terminal)
python3 CentralHospitalar/CentralHospitalar.py # menus do Sistema 2 (terminal)
python3 gui.py                                 # interface grafica (Tkinter)
```

Na primeira execucao os bancos sao criados automaticamente em `data/`,
executando os scripts SQL e carregando os dados ficticios.

---

## Estrutura

```
GestaoHospitalar/
├── main.py                         menu inicial do projeto
├── gui.py                          interface grafica (as duas abas)
├── core/
│   ├── db.py                       conexao, criacao e execucao de SQL
│   ├── ui.py                       menus, leitura validada e tabelas (terminal)
│   └── widgets.py                  tabela e formulario reutilizaveis (Tkinter)
├── DiarioPessoal/
│   ├── bdDiarioPessoal.sql         DDL + INSERTs + exemplos de consulta
│   ├── repositorio.py              todo o SQL do Sistema 1
│   ├── DiarioPessoal.py            menus de terminal
│   └── interface.py                aba grafica
├── CentralHospitalar/
│   ├── bdCentralHospitalar.sql     DDL + INSERTs + views + exemplos
│   ├── repositorio.py              todo o SQL do Sistema 2
│   ├── CentralHospitalar.py        menus de terminal
│   └── interface.py                aba grafica
├── docs/DER.md                     diagramas entidade-relacionamento
└── data/                           bancos .db gerados (criado na execucao)
```

O SQL fica concentrado nos arquivos `repositorio.py` de cada sistema; o
terminal e a interface grafica consomem as mesmas funcoes, sem duplicar
consultas.

---

## Sistema 1 - Diario de Saude Pessoal

**Tabelas:** `usuario`, `profissional`, `alergia`, `usuario_alergia` (N:N),
`vacina`, `consulta`, `exame`, `vacinacao`.

**Menus de terminal:** Usuarios, Alergias, Consultas, Exames, Vacinas,
Relatorios e Manutencao do banco.

**Interface grafica:** lista de usuarios a esquerda e, a direita, as abas
Linha do tempo, Alergias, Consultas, Exames, Vacinas e Relatorios do usuario
selecionado.

Operacoes demonstradas:

- **Insercao:** novo usuario, consulta, exame, dose de vacina, alergia do
  usuario, profissional.
- **Consulta:** ficha completa, historico por usuario, linha do tempo unindo
  consultas/exames/vacinas (`UNION ALL`), alergias graves, exames pendentes,
  esquemas vacinais incompletos (`GROUP BY` + `HAVING`), distribuicao por tipo
  sanguineo.
- **Atualizacao:** contato, correcao de tipo sanguineo/RH, diagnostico da
  consulta, lancamento de resultado de exame (passa a `CONCLUIDO`), gravidade
  de alergia.

## Sistema 2 - Central Hospitalar de Transplantes

**Tabelas:** `hospital`, `tipo_orgao`, `doador`, `receptor`,
`orgao_disponivel`, `fila_espera`, `transplante`, `compat_abo`, `compat_rh`.
**Views:** `vw_compatibilidade`, `vw_fila_detalhada`.

**Menus de terminal:** Doadores, Receptores, Orgaos, Fila de espera,
Compatibilidade, Transplantes, Painel/Relatorios e Manutencao.

**Interface grafica:** abas Painel, Compatibilidade, Orgaos, Fila de espera,
Doadores, Receptores e Transplantes.

Operacoes demonstradas:

- **Insercao:** doador, receptor, orgao captado, entrada na fila, transplante.
- **Consulta:** orgaos disponiveis com tempo decorrido x tempo de isquemia,
  fila ordenada por prioridade e tempo de espera, **receptores compativeis com
  um orgao**, quantidade de candidatos por orgao, receptores sem nenhuma opcao
  compativel (`NOT IN`), indicadores do painel, transplantes por hospital.
- **Atualizacao:** status do orgao, prioridade e situacao na fila, desfecho do
  transplante.

### Criterio de compatibilidade

Um orgao e compativel com um receptor quando:

1. o **tipo de orgao** aguardado na fila e o mesmo do orgao captado;
2. o **tipo sanguineo ABO** do doador pode doar para o do receptor
   (O -> todos; A -> A e AB; B -> B e AB; AB -> AB);
3. o **fator RH** e compativel (negativo doa para ambos; positivo somente para
   positivo);
4. o orgao esta `DISPONIVEL` e o receptor esta `AGUARDANDO`.

As regras 2 e 3 estao armazenadas nas tabelas `compat_abo` e `compat_rh` e sao
aplicadas pela view `vw_compatibilidade`, ou seja, a compatibilidade e resolvida
pelo proprio banco. A ordem sugerida de alocacao e prioridade
(EMERGENCIA > ALTA > NORMAL) e, em caso de empate, maior tempo de espera.

A efetivacao do transplante roda em uma **transacao**: insere em `transplante`
e atualiza o status do orgao e da fila; qualquer falha desfaz tudo
(`ROLLBACK`).

---

## Recriar os bancos

- Terminal: menu *Manutencao do banco -> Recriar banco*.
- Interface grafica: menu *Arquivo -> Recriar banco...*.
- Manualmente: apague os arquivos de `data/` e execute o projeto novamente.
