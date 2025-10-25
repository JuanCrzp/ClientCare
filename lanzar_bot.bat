@echo off
setlocal
set "WORKDIR=%~dp0"
cd /d "%WORKDIR%"

REM Prefer py -3 si existe
set "PY=python"
where py >nul 2>nul && set "PY=py -3"
set PYTHONUNBUFFERED=1

start "AtencionCliente Telegram" /D "%WORKDIR%" cmd /k %PY% -m src.connectors.telegram_polling
start "AtencionCliente API" /D "%WORKDIR%" cmd /k %PY% -m uvicorn src.app.server:app --host 0.0.0.0 --port 8082 --reload --log-level debug

echo Lanzado en dos ventanas (Telegram + API). Puedes cerrar esta ventana.
exit /b 0
