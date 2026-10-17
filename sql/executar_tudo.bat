@echo off
setlocal
cd /d "%~dp0"
chcp 65001 > nul
set PGCLIENTENCODING=UTF8

where psql >nul 2>nul
if not errorlevel 1 goto psql_ok

for /d %%D in ("%ProgramFiles%\PostgreSQL\*") do if exist "%%D\bin\psql.exe" set "PGBIN=%%D\bin"
if defined PGBIN goto psql_achado

echo.
echo Nao encontrei o psql.exe em "%ProgramFiles%\PostgreSQL\".
echo Verifique se o PostgreSQL esta instalado. Se estiver em outra pasta,
echo informe abaixo o caminho da pasta bin (ex.: D:\PostgreSQL\16\bin)
set /p PGBIN=Pasta bin do PostgreSQL:
if not exist "%PGBIN%\psql.exe" goto sem_psql

:psql_achado
set "PATH=%PGBIN%;%PATH%"
echo Usando o psql de: %PGBIN%

:psql_ok
if "%PGUSER%"=="" set PGUSER=postgres
if "%PGHOST%"=="" set PGHOST=localhost
echo.
set /p PGPASSWORD=Senha do usuario "%PGUSER%" do PostgreSQL (a definida na instalacao):

echo.
echo [1/3] Criando os bancos...
psql -v ON_ERROR_STOP=1 -q -d postgres -c "DROP DATABASE IF EXISTS diario_saude" || goto erro
psql -v ON_ERROR_STOP=1 -q -d postgres -c "DROP DATABASE IF EXISTS central_transplantes" || goto erro
psql -v ON_ERROR_STOP=1 -q -d postgres -c "CREATE DATABASE diario_saude ENCODING 'UTF8' TEMPLATE template0" || goto erro
psql -v ON_ERROR_STOP=1 -q -d postgres -c "CREATE DATABASE central_transplantes ENCODING 'UTF8' TEMPLATE template0" || goto erro

echo [2/3] Diario de Saude...
psql -v ON_ERROR_STOP=1 -q -d diario_saude -c "SET client_min_messages = warning" -f diario\01_criacao.sql || goto erro
psql -v ON_ERROR_STOP=1 -q -d diario_saude -f diario\02_povoamento.sql || goto erro

echo [3/3] Central de Transplantes...
psql -v ON_ERROR_STOP=1 -q -d central_transplantes -c "SET client_min_messages = warning" -f central\01_criacao.sql || goto erro
psql -v ON_ERROR_STOP=1 -q -d central_transplantes -f central\02_povoamento.sql || goto erro

echo.
echo ============================================================
echo  Bancos criados e povoados com sucesso!
echo  Para ver as operacoes, rode no Prompt (nesta pasta):
echo    psql -U postgres -d diario_saude -f diario\03_operacoes.sql
echo    psql -U postgres -d central_transplantes -f central\03_operacoes.sql
echo ============================================================
pause
exit /b 0

:sem_psql
echo.
echo psql.exe nao encontrado em "%PGBIN%". Instale o PostgreSQL ou use o pgAdmin
echo (veja o README.md, secao "Como executar").
pause
exit /b 1

:erro
echo.
echo ERRO na execucao. Verifique a mensagem acima.
echo Dica: "autenticacao do tipo senha falhou" = senha errada.
pause
exit /b 1
