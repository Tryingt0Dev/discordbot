#!/bin/bash

# Instala las librerías de Python
pip install -r requirements.txt

# Instala FFmpeg (sin sudo)
echo "Instalando FFmpeg (sin sudo)..."
apt-get update -y
apt-get install -y ffmpeg

echo "Instalación de FFmpeg completada."