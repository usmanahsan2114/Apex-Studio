@echo off
cd /d "%~dp0"
call :findpy
if not defined PY (
  echo [ERROR] Python 3.10+ not found. Install it from https://www.python.org/downloads/
  echo         ^(tick "Add python.exe to PATH" during install^), then re-run setup.bat.
  pause & exit /b 1
)
echo ============================================================
echo  Apex Studio - one-time setup (free, offline rendering)
echo ============================================================
echo  Python: %PY%
echo.
echo [1/3] Installing Python packages...
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 ( echo [ERROR] pip install failed. & pause & exit /b 1 )
echo.
echo [2/3] Downloading the Kokoro voice model (~350 MB, one time)...
if not exist "assets\kokoro" mkdir "assets\kokoro"
if not exist "assets\kokoro\kokoro-v1.0.onnx" (
  echo   - kokoro-v1.0.onnx
  curl -L -o "assets\kokoro\kokoro-v1.0.onnx" "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
) else ( echo   - kokoro-v1.0.onnx already present )
if not exist "assets\kokoro\voices-v1.0.bin" (
  echo   - voices-v1.0.bin
  curl -L -o "assets\kokoro\voices-v1.0.bin" "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
) else ( echo   - voices-v1.0.bin already present )
echo.
echo [3/3] Fetching premium design assets (fonts + icons, one time)...
"%PY%" fetch_assets.py
if errorlevel 1 ( echo [WARN] asset fetch failed. You can run fetch_assets.py later. )
echo.
echo Setup complete. Ensure Google Chrome is installed, then run run_studio.bat
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
