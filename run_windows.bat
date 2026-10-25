@echo off
REM Starts the Farm2Feed server on Windows 10/11.
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\activate.bat (
  echo Run setup_windows.bat first.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
set PYTHONUTF8=1
set "PORT_VALUE=5001"
if exist .env (
  for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if /i "%%A"=="PORT" set "PORT_VALUE=%%B"
  )
)
echo Farm2Feed is starting. Open http://localhost:%PORT_VALUE%  ^(press Ctrl+C to stop^)
python -m uvicorn asgi:application --host 0.0.0.0 --port %PORT_VALUE%
pause
