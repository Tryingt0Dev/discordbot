#!/bin/bash

# Instala las librerías de Python
pip install -r requirements.txt

# Instala FFmpeg (AQUÍ ESTÁ EL ARREGLO)
echo "Instalando FFmpeg con sudo..."
sudo apt-get update -y
sudo apt-get install -y ffmpeg

echo "Instalación de FFmpeg completada."