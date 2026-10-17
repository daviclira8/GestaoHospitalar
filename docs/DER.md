# Modelo de dados

Os esquemas PostgreSQL são definidos diretamente nos scripts de criação:

- [Diário de Saúde](../sql/diario/01_criacao.sql)
- [Central Hospitalar](../sql/central/01_criacao.sql)

Esses scripts são a referência para tabelas, tipos, restrições, funções e
visões; este documento resume as relações entre os bancos.

## Diário de Saúde

`usuario` é a entidade central. Alergias, consultas, exames e métricas
referenciam um usuário. `usuario_doenca` relaciona usuários e doenças,
registrando data e status do diagnóstico. `aplicacao_vacina` relaciona usuários
e vacinas e guarda cada dose. Um exame pode referenciar opcionalmente uma
consulta.

## Central Hospitalar

`doador` e `receptor` guardam o identificador do usuário do Diário e o hospital
associado. Doadores podem originar vários `orgao_disponivel`; receptores podem
ter entradas em `fila_espera`. `alocacao` conecta um órgão a uma posição da
fila e controla as etapas logísticas. `bolsa_sangue` registra doações de sangue
e sua disponibilidade. `compatibilidade_abo` mantém a regra ABO como dado.

## Integração

Os bancos são independentes. A Central referencia o Diário somente por
`usuario_id` e consulta nome, tipagem e restrições clínicas por meio de
`backend/central/integracao_diario.py`, em conexão somente de leitura. Dados
clínicos e tipagem não são copiados para a Central.
