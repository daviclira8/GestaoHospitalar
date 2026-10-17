#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
PSQL="psql -v ON_ERROR_STOP=1 -q"
export PGCLIENTENCODING=UTF8

echo ">> Criando bancos"
$PSQL -d postgres -c "DROP DATABASE IF EXISTS diario_saude"
$PSQL -d postgres -c "DROP DATABASE IF EXISTS central_transplantes"
$PSQL -d postgres -c "CREATE DATABASE diario_saude ENCODING 'UTF8'"
$PSQL -d postgres -c "CREATE DATABASE central_transplantes ENCODING 'UTF8'"

echo ">> Diário de Saúde"
$PSQL -d diario_saude -f diario/01_criacao.sql      2>&1 | grep -v NOTICE || true
$PSQL -d diario_saude -f diario/02_povoamento.sql

echo ">> Central de Transplantes"
$PSQL -d central_transplantes -f central/01_criacao.sql 2>&1 | grep -v NOTICE || true
$PSQL -d central_transplantes -f central/02_povoamento.sql

echo ">> Pronto. Para ver as operações:"
echo "   psql -d diario_saude         -f diario/03_operacoes.sql"
echo "   psql -d central_transplantes -f central/03_operacoes.sql"
