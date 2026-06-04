#!/bin/bash

# Cargar variables de entorno desde archivo local (no se sube a GitHub)
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "=============================================="
echo "🎬 Iniciando Video Generator Pro"
echo "=============================================="
echo "Cargando la API de Gemini..."

# Activar entorno virtual
if [ -d "venv" ]; then
    echo "Activando entorno virtual..."
    source venv/bin/activate
fi

# Primera vez: pedir autorización de YouTube antes de arrancar
if [ ! -f "youtube_token.pkl" ]; then
    echo ""
    echo "📺 Primera vez: Necesitas autorizar tu cuenta de YouTube."
    echo "   Se abrirá tu navegador. Inicia sesión con tu canal y da permisos."
    python youtube_uploader.py
    echo ""
fi

# Abrir el navegador automáticamente después de 2 segundos
(sleep 2 && xdg-open http://localhost:8000 2>/dev/null) &

# Iniciar el servidor local
python3 api_server.py
