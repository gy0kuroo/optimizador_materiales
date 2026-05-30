#!/bin/bash
# Script de inicialización para Linux/Mac
# Ejecutar: bash setup_project.sh

set -e

echo ""
echo "=========================================="
echo "  CutLess - Setup del Proyecto"
echo "=========================================="
echo ""

# Verificar si Python está disponible
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 no está instalado"
    echo "Por favor, instala Python desde https://www.python.org/"
    exit 1
fi

# Ejecutar el script de setup
echo "Iniciando setup..."
echo ""
python3 setup_project.py

echo ""
