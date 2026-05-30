@echo off
REM Script de inicialización para Windows
REM Ejecutar: setup_project.bat

echo.
echo ==========================================
echo  CutLess - Setup del Proyecto
echo ==========================================
echo.

REM Verificar si Python está disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python no está instalado o no está en PATH
    echo Por favor, instala Python desde https://www.python.org/
    pause
    exit /b 1
)

REM Ejecutar el script de setup
echo Iniciando setup...
echo.
python setup_project.py

if errorlevel 1 (
    echo.
    echo Error durante el setup
    pause
    exit /b 1
)

pause
