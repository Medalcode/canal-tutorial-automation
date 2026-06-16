#!/bin/bash

# Cargar variables de entorno desde archivo local (no se sube a GitHub)
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "=============================================="
echo "🎬 Iniciando Video Generator Pro"
echo "=============================================="
echo "Cargando la API de Gemini..."

VENV_DIR="$HOME/.canal-tutorial-venv"

# Activar entorno virtual y crear si no existe
if [ ! -d "$VENV_DIR" ]; then
    echo "Creando entorno virtual en $VENV_DIR e instalando dependencias..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install -r requirements.txt
else
    echo "Activando entorno virtual..."
    source "$VENV_DIR/bin/activate"
fi

# Primera vez: pedir autorización de YouTube antes de arrancar
if [ ! -f "youtube_token.pkl" ]; then
    echo ""
    echo "📺 Primera vez: Necesitas autorizar tu cuenta de YouTube."
    echo "   Se abrirá tu navegador. Inicia sesión con tu canal y da permisos."
    python3 youtube_uploader.py
    echo ""
fi

# Abrir el navegador automáticamente después de 2 segundos
(sleep 2 && xdg-open http://localhost:8001 2>/dev/null) &

# Iniciar el servidor local
python3 api_server.py
