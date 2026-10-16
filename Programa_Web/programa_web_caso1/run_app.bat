@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_app.ps1" -OpenBrowser
if errorlevel 1 (
  echo.
  echo No se pudo iniciar la aplicacion. Revisa el mensaje anterior.
  pause
)
endlocal
