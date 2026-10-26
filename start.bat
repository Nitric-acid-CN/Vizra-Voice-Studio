@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
set HF_HUB_OFFLINE=1
set TRANSFORMERS_OFFLINE=1
set GRADIO_ANALYTICS_ENABLED=False
set HF_HOME=%~dp0cache\huggingface
set GRADIO_TEMP_DIR=%~dp0cache\gradio
set TEMP=%~dp0cache\temp
set TMP=%TEMP%
if not exist "%TEMP%" mkdir "%TEMP%"
if not exist ".venv\Scripts\python.exe" (
  echo Missing Python virtual environment.
  pause
  exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" "%~dp0launcher.pyw"
exit /b 0
