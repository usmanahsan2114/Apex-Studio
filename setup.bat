@echo off
cd /d "%~dp0"
echo ============================================================
echo  Apex Studio - one-time setup (free, offline rendering)
echo ============================================================
echo.
echo [1/2] Installing Python packages...
python -m pip install flask kokoro-onnx soundfile imageio-ffmpeg scipy pillow
python -m pip install numpy==1.26.2
echo.
echo [2/2] Downloading the Kokoro voice model (~350 MB, one time)...
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
echo Setup complete. Ensure Google Chrome is installed, then run run_studio.bat
pause
