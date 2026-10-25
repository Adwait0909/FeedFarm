@echo off
REM One-time setup for Windows 10/11. Double-click, or run in Command Prompt / PowerShell.
setlocal
cd /d "%~dp0"

echo ==^> Looking for Python 3.11 or 3.12...
set "PYCMD="
for %%V in (3.12 3.11) do (
  if not defined PYCMD (
    py -%%V -c "import sys" >nul 2>&1 && set "PYCMD=py -%%V"
  )
)
if not defined PYCMD (
  python -c "import sys; sys.exit(0 if (3,11)<=sys.version_info[:2]<=(3,12) else 1)" >nul 2>&1 && set "PYCMD=python"
)
if not defined PYCMD (
  echo.
  echo Python 3.11 or 3.12 was not found. ^(Python 3.13+ and 3.10 will NOT work.^)
  echo Install Python 3.12 from https://www.python.org/downloads/release/python-3128/
  echo and tick "Add python.exe to PATH" in the installer, then run setup_windows.bat again.
  pause
  exit /b 1
)
echo     Using: %PYCMD%

if exist .venv\Scripts\python.exe (
  .venv\Scripts\python.exe -c "import sys" >nul 2>&1 || (
    echo ==^> Existing .venv is broken or was created on another computer - recreating it...
    rmdir /s /q .venv
  )
)
if not exist .venv\Scripts\python.exe (
  echo ==^> Creating virtual environment in .venv ...
  %PYCMD% -m venv .venv
  if errorlevel 1 goto :fail
) else (
  echo ==^> Reusing existing virtual environment in .venv ...
)
call .venv\Scripts\activate.bat

echo ==^> Installing packages ^(PyTorch is large; this can take several minutes^)...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :fail
python -m pip install -r requirements.txt
if errorlevel 1 goto :fail

echo ==^> Preparing .env ...
python scripts\make_env.py
if errorlevel 1 goto :fail

echo ==^> Securing doctor accounts that still use a published demo password...
set PYTHONUTF8=1
python scripts\reset_doctor_passwords.py --known-defaults-only
if errorlevel 1 echo     ^(could not reset doctor passwords; run scripts\reset_doctor_passwords.py later^)

echo ==^> Verifying the installation...
python scripts\verify_install.py
if errorlevel 1 echo     ^(see the message above; the app may still start^)

echo.
echo Setup complete. Start the app by double-clicking run_windows.bat
pause
exit /b 0

:fail
echo.
echo Setup failed. Read the error above. Common fixes are in README.md ^(Troubleshooting^).
pause
exit /b 1
