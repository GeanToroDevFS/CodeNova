@echo off
setlocal enabledelayedexpansion

REM ==============================
REM  CREAR Y ACTIVAR ENTORNO VIRTUAL
REM ==============================
echo 🌀 Creando entorno virtual "my_StockNova"...
python -m venv my_StockNova

if exist "my_StockNova\Scripts\activate" (
    call my_StockNova\Scripts\activate
) else (
    echo ❌ Error: No se pudo crear el entorno virtual.
    pause
    exit /b
)

REM ==============================
REM  ACTUALIZAR PIP
REM ==============================
echo 🔄 Actualizando pip...
python -m pip install --upgrade pip

REM ==============================
REM  DETECTAR requirements.txt
REM ==============================
set REQ_FILE=
if exist "requirements.txt" (
    set REQ_FILE=requirements.txt
) else if exist "Nova\requirements.txt" (
    set REQ_FILE=Nova\requirements.txt
)

if not defined REQ_FILE (
    echo ❌ No se encontró el archivo requirements.txt ni en la raíz ni en /Nova.
    pause
    exit /b
)

REM ==============================
REM  INSTALAR DEPENDENCIAS
REM ==============================
echo 📦 Instalando dependencias desde !REQ_FILE! ...
pip install -r !REQ_FILE!

REM ==============================
REM  FINALIZACIÓN
REM ==============================
echo -------------------------------------
echo ✅ Entorno virtual creado e instalado correctamente.
echo 🔹 Activa el entorno con:
echo    call my_StockNova\Scripts\activate
echo -------------------------------------
pause
endlocal
