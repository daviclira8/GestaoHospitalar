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

Menu inicial, que abre qualquer uma das três interfaces:

```bat
python main.py
```

Interface gráfica:

```bat
python gui.py
```

Front web e API HTTP:

```bat
python API\api.py
```

Abra `http://localhost:8000`. O servidor atende somente em `127.0.0.1`.

Menus de terminal (também acessíveis pelo `main.py`):

```bat
python -m terminal.diario
python -m terminal.central
```

Backend de demonstração e testes:

```bat
python demo_backend.py
python -m pytest -q
```

Os testes usam bancos de teste separados e as credenciais PostgreSQL de `.env`.

## Estrutura

```text
backend/       Serviços, modelos, validação, integração e conexão PostgreSQL
API/           API HTTP do front web
web/           Aplicação web
terminal/      Menus interativos de terminal dos dois sistemas
gui.py         Interface gráfica (abas em backend/*/interface.py)
main.py        Menu inicial: escolhe a interface
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

## Menus de terminal

Terceira interface do projeto, ao lado da janela Tkinter e do front web. Como
as outras, não escreve SQL: tudo passa por `DiarioService`, `CentralService` e
`DiarioGateway`.

| Módulo | Conteúdo |
|---|---|
| `terminal/ui.py` | menus numerados, leitura validada (datas, números, opções) e tabelas alinhadas; aceita as dataclasses do backend |
| `terminal/enums.py` | lê os `ENUM` do PostgreSQL (`pg_enum`) |
| `terminal/diario.py` | usuários, alergias, doenças, consultas e exames, vacinas e métricas |
| `terminal/central.py` | doadores, fila de espera, órgãos, seleção de receptores, logística e banco de sangue |
| `terminal/tk_ausente.py` | explica a falta do Tk quando `gui.py` não consegue abrir |

As opções de sexo, tipo sanguíneo, fator RH, gravidade, status de doença e tipo
de doador **não estão escritas no código das telas**: vêm de `pg_enum`, então um
valor novo no banco aparece sozinho nos menus.

O menu de compatibilidade mostra os candidatos elegíveis na ordem de alocação e,
logo abaixo, os descartados com o motivo devolvido pelo backend — por exemplo
`Incompatível ABO (A → B)` ou `Inviável: transporte de 9.0 h > 2.9 h restantes`.
