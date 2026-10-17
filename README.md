# Gestão Hospitalar

Aplicação com dois bancos PostgreSQL integrados pelo identificador do usuário:

- **Diário de Saúde Pessoal**: dados cadastrais, tipagem, alergias, diagnósticos,
  consultas, exames, vacinas e métricas.
- **Central Hospitalar**: doadores, receptores, fila de espera, órgãos,
  compatibilidade, alocações e estoque de sangue.

O backend e os testes automatizados são os da branch `main`. A interface
Tkinter e a API/front web mantidos nesta branch usam os mesmos serviços.

## Configuração

Requisitos: Python 3.10 ou superior e PostgreSQL 14 ou superior.

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.exemplo .env
```

Inicie o serviço PostgreSQL no Windows (em `services.msc`, procure
`postgresql-x64-*`) e configure em `.env` o usuário e a senha definidos na
instalação. `PGHOST=127.0.0.1` evita diferenças de resolução IPv4/IPv6 em
`localhost`. Depois crie e povoe os bancos:

```bat
python criar_bancos.py
```

O script recria `diario_saude` e `central_transplantes`. Não o execute se
precisar preservar dados existentes.

## Executar

Interface gráfica:

```bat
python main.py
```

Front web e API HTTP:

```bat
python API\api.py
```

Abra `http://localhost:8000`. O servidor atende somente em `127.0.0.1`.

Backend de demonstração e testes:

```bat
python demo_backend.py
python -m pytest -q
```

Os testes usam bancos de teste separados e as credenciais PostgreSQL de `.env`.

## Estrutura

```text
backend/       Serviços, modelos, validação, integração e conexão PostgreSQL
DiarioPessoal/ Interface gráfica do Diário
CentralHospitalar/ Interface gráfica da Central
API/           API HTTP do front web
web/           Aplicação web
sql/           Esquemas, dados de exemplo e operações SQL
tests/         Testes do backend
criar_bancos.py  Criação e povoamento dos bancos
```

## Integração e regras

A Central armazena o `usuario_id` e consulta os dados clínicos no Diário por
meio de um gateway somente de leitura. Não há cópia local de tipagem ou dados
clínicos na Central; por isso divergências entre cópias de sangue não se
aplicam. Restrições clínicas são consultadas durante a triagem e na seleção de
doadores.

A seleção de órgãos considera compatibilidade ABO, urgência, semelhança do tipo
sanguíneo, tempo em fila, distância e tempo de isquemia. Para transfusão de
sangue também é considerado o fator Rh.
