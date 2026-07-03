@echo off
chcp 65001 > nul
title Servidor Local - Bendito Taller

echo =======================================================
echo          SERVIDOR LOCAL - BENDITO TALLER
echo =======================================================
echo.
echo [1] Abriendo el catálogo en tu navegador PC...
start http://localhost:8000

echo.
echo [2] ¿Cómo visualizar la vista de celular?
echo    - Opción A (Recomendada): En tu navegador PC, presiona F12 (o clic derecho -^> Inspeccionar),
echo      y haz clic en el icono de celular/tablet (Device Toolbar) para simular pantallas.
echo    - Opción B (Celular Real): Conecta tu celular a la misma red Wi-Fi que esta PC.
echo      Luego abre el navegador de tu celular e ingresa la dirección IP de tu PC.
echo.
echo    Tus direcciones IP locales posibles son:
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /i "IPv4"') do (
    echo      http:%%i:8000
)
echo.
echo =======================================================
echo Presiona Ctrl+C en esta ventana para apagar el servidor.
echo =======================================================
echo.
python -m http.server 8000
pause
