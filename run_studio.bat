@echo off
cd /d "%~dp0"
call :findpy
if not defined PY (
  echo [ERROR] Python 3.10+ not found. Run setup.bat first, or install Python from https://www.python.org/downloads/
  pause & exit /b 1
)
echo Starting Apex Studio...  (a browser tab will open at http://127.0.0.1:5000)
"%PY%" apex_studio.py
pause
exit /b 0

REM --- locate Python without requiring it on PATH (py launcher -> PATH -> common install dirs) ---
:findpy
set "PY="
where py >nul 2>nul && (set "PY=py" & goto :eof)
where python >nul 2>nul && (set "PY=python" & goto :eof)
if exist "%LocalAppData%\Programs\Python\Python313\python.exe" (set "PY=%LocalAppData%\Programs\Python\Python313\python.exe" & goto :eof)
if exist "%ProgramFiles%\Python313\python.exe" (set "PY=%ProgramFiles%\Python313\python.exe" & goto :eof)
for /f "delims=" %%P in ('dir /b /s "%LocalAppData%\Programs\Python\python.exe" 2^>nul') do if not defined PY set "PY=%%P"
goto :eof
