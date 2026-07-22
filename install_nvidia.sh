#!/bin/bash
set -e

echo "Instalando nvidia-container-toolkit desde los repositorios de Arch Linux..."
pacman -Sy --noconfirm nvidia-container-toolkit

echo "Configurando Docker para usar NVIDIA..."
nvidia-ctk runtime configure --runtime=docker

echo "Reiniciando el servicio de Docker..."
systemctl restart docker

echo "¡Instalación completada con éxito para CachyOS/Arch!"
