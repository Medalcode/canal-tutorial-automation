# 🎬 Video Generator Pro - Canal Tutorial Automation

> **Crea videos educativos profesionales sin escribir código.**

Pipeline automatizado para generar tutoriales en video con IA, narración, subtítulos, música y calidad 1080p @ 5Mbps. Interfaz web intuitiva, FastAPI backend, Gemini IA.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()
[![Vercel](https://img.shields.io/badge/Vercel-Deployed-black.svg?logo=vercel)](https://canal-tutorial-automation.vercel.app)
---

## ✨ Características

### 🎙️ Audio & Narración
- ✅ Voces naturales en español con edge-tts
- ✅ Normalización y compresión de audio automática
- ✅ Música de fondo balanceada
- ✅ Bitrate 192kbps (calidad superior)

### 📝 Subtítulos & Texto
- ✅ Subtítulos sincronizados (word-level)
- ✅ Detección automática con faster-whisper
- ✅ Títulos de escenas con fuente profesional
- ✅ Overlay estilo terminal (código verde)

### 🎬 Video & Composición
- ✅ Múltiples escenas por guión
- ✅ Intro animada y outro con call-to-action
- ✅ Resolución 1920x1080 Full HD
- ✅ 30 FPS (fluido)
- ✅ Bitrate 5Mbps (máxima fidelidad)

### 🤖 Inteligencia Artificial
- ✅ Generación automática de guiones con Gemini IA
- ✅ Detección de temas y estructura
- ✅ Editor interactivo de escenas
- ✅ Validación de guiones

### 🌐 Interfaz Web
- ✅ Panel de control moderno (dark mode)
- ✅ Dashboard con estadísticas en vivo
- ✅ Monitor de progreso en tiempo real
- ✅ Responsive (desktop/mobile)
- ✅ Sin dependencias externas

### 📦 Deployment
- ✅ Docker support
- ✅ Vercel + Railway ready
- ✅ Arquitectura híbrida optimizada
- ✅ Costos bajos ($5-10/mes)

---

## 🚀 Quick Start

### Opción 1: En Navegador (Recomendado)

```bash
# 1. Instalar
pip install -r requirements.txt

# 2. Iniciar servidor
python api_server.py

# 3. Abrir en navegador
open http://localhost:8000
```

**¡Eso es todo! Ahora puedes:**
- Generar videos con Gemini IA
- Editar guiones sin código
- Monitorear progreso
- Descargar videos

### Opción 2: Con Docker

```bash
# Instalar Docker y Docker Compose

# Iniciar
docker-compose up

# Abrir
open http://localhost:8000
```

### Opción 3: Línea de Comandos

```bash
# Generar guión con IA
export GEMINI_API_KEY="tu_clave"
python script_generator_pro.py --topic "FastAPI para principiantes"

# Generar video
python generate_video.py

# Resultado en output/video_con_musica.mp4
```

---

## 📋 Requisitos

| Componente | Versión | Requerido |
|-----------|---------|----------|
| Python | 3.10+ | ✅ |
| FFmpeg | Cualquiera | ✅ |
| Gemini API Key | - | ⭕ (opcional) |
| Node.js | 16+ | ⭕ (solo deploy) |

---

## 📚 Documentación

### Guías Rápidas
- **[INICIO_RAPIDO.md](INICIO_RAPIDO.md)** - 60 segundos para empezar
- **[WEB_INTERFACE.md](WEB_INTERFACE.md)** - Guía completa de la interfaz

### Guías de Deployment
- **[DEPLOY_VERCEL_RAILWAY.md](DEPLOY_VERCEL_RAILWAY.md)** - 🔥 Lee esto si quieres producción
- **[DEPLOY_PASO_A_PASO.md](DEPLOY_PASO_A_PASO.md)** - Instrucciones detalladas
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Todas las opciones

### Documentación Técnica
- **[MEJORAS.md](MEJORAS.md)** - Mejoras de calidad implementadas
- **[VIDEO_COMPLETADO.md](VIDEO_COMPLETADO.md)** - Ejemplo de video generado

---

## 🎯 Casos de Uso

```bash
# Caso 1: Generar video sobre tema específico
Topic: "Docker para principiantes"
Resultado: Video 1080p @ 5Mbps en 40 minutos

# Caso 2: Crear tutorial desde markdown
Subir archivo .md estructurado
Resultado: Video automático

# Caso 3: Batch processing
10 temas → 10 videos (paralelo)
Resultado: Librería de videos

# Caso 4: Documentación en video
Documentación técnica → Videos
Resultado: Documentación interactiva
```

---

## 🏗️ Arquitectura

### Backend (FastAPI)
```
api_server.py
├── /api/scripts/generate      → Generar con Gemini IA
├── /api/scripts/{id}          → Ver/editar guión
├── /api/videos/generate       → Generar video (async)
├── /api/jobs/{id}             → Ver estado de trabajo
├── /api/files                 → Listar/descargar videos
└── Static files               → Servir frontend
```

### Frontend (HTML/CSS/JS)
```
web/
├── index.html    → 191 líneas (interfaz)
├── styles.css    → 600 líneas (diseño)
└── app.js        → 400 líneas (lógica)
```

### Generación de Videos
```
generate_video.py
├── Audio synthesis (edge-tts)
├── Transcription (faster-whisper)
├── Video composition (moviepy)
├── Audio mixing (FFmpeg)
└── Upscaling (FFmpeg)
```

---

## 📊 Especificaciones Técnicas

| Parámetro | Valor |
|-----------|-------|
| **Resolución** | 1920x1080 (Full HD) |
| **FPS** | 30 |
| **Bitrate Video** | 5 Mbps |
| **Bitrate Audio** | 192 kbps |
| **Codec Video** | H.264 |
| **Codec Audio** | AAC |
| **Duración típica** | 8-12 minutos |
| **Tiempo de generación** | 30-60 minutos |
| **Tamaño típico** | 150-300 MB |

---

## 🎨 Stack Tecnológico

### Backend
- **FastAPI** - Framework REST
- **Uvicorn** - ASGI Server
- **Pydantic** - Validación de datos
- **Python 3.10+** - Lenguaje

### Audio & Video
- **edge-tts** - Síntesis de voz
- **faster-whisper** - Transcripción
- **moviepy** - Composición
- **FFmpeg** - Procesamiento media

### Frontend
- **HTML5** - Estructura
- **CSS3** - Diseño (dark mode, responsive)
- **JavaScript Vanilla** - Lógica (sin dependencias)

### IA
- **Google Gemini API** - Generación de guiones

### Deployment
- **Docker** - Containerización
- **Vercel** - Frontend hosting
- **Railway** - Backend hosting

---

## 💻 Instalación Detallada

### 1. Clonar repositorio

```bash
git clone https://github.com/Medalcode/canal-tutorial-automation.git
cd canal-tutorial-automation
```

### 2. Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate      # macOS/Linux
# o
venv\Scripts\activate          # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Gemini (Opcional)

```bash
export GEMINI_API_KEY="tu_clave_aqui"
# Obtén una clave gratis en: https://aistudio.google.com/
```

### 5. Iniciar servidor

```bash
python api_server.py
```

### 6. Abrir en navegador

```
http://localhost:8000
```

---

## 📖 Uso

### Desde la Web UI (Recomendado)

1. **Dashboard** - Ver estadísticas y trabajos recientes
2. **Generar Video**:
   - Con IA: Ingresar tema → Gemini genera guión → Generar video
   - Manual: Seleccionar guión → Generar video
3. **Mis Videos** - Descargar videos generados
4. **Trabajos** - Ver estado de cada generación

### Desde CLI

```bash
# Generar guión
python script_generator_pro.py --topic "Tu tema"

# Generar video
python generate_video.py

# Resultado en output/video_con_musica.mp4
```

### Desde API

```bash
# Generar con IA
curl -X POST http://localhost:8000/api/scripts/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "FastAPI", "num_scenes": 5}'

# Generar video
curl -X POST http://localhost:8000/api/videos/generate \
  -H "Content-Type: application/json" \
  -d '{"script_id": "abc123"}'

# Ver estado
curl http://localhost:8000/api/jobs/{job_id}
```

---

## 🔧 Personalización

### Cambiar Voz

En `generate_video.py` (línea 24):

```python
VOICE = "es-MX-DaliaNeural"  # Cambiar aquí

# Voces disponibles:
# es-ES-AlvaroNeural
# es-MX-JorgeNeural
# es-AR-ElMariano
# Y más...
```

### Cambiar Música

Reemplaza `assets/musica_fondo.mp3` con tu archivo MP3.

### Cambiar Colores/Fondo

En `generate_video.py`:

```python
BG_COLOR = (20, 22, 28)       # Color RGB del fondo
FONT_SIZE = 44                # Tamaño de títulos
FONT_COLOR = "white"          # Color de texto
```

---

## 📊 Ejemplos

### Ejemplo 1: Tutorial FastAPI

```bash
# Input
Topic: "FastAPI - Crear una API REST en 10 minutos"
Escenas: 8
Duración: ~12 minutos

# Output
- video_con_musica.mp4 (1080p @ 5Mbps)
- narracion.mp3 (narración clara)
- thumbnail.png (portada automática)
```

### Ejemplo 2: Docker Basics

```bash
# Input
Topic: "Docker para principiantes"
Escenas: 6
Duración: ~10 minutos

# Output
- Video profesional
- Subtítulos en español
- Música de fondo balanceada
```

---

## 🚀 Deployment

### Local (Desarrollo)

```bash
python api_server.py
# o
docker-compose up
```

### Producción (Vercel + Railway)

Ver: [DEPLOY_VERCEL_RAILWAY.md](DEPLOY_VERCEL_RAILWAY.md)

**Frontend En Vivo:** [https://canal-tutorial-automation.vercel.app](https://canal-tutorial-automation.vercel.app)

**Resumen:**
- Frontend: Vercel ($0 gratis)
- Backend: Railway ($5-10/mes)
- Total: ~$5-10/mes

```bash
# Railway
railway login
railway init  # Elegir Python
railway up

# Vercel
vercel --prod
```

---

## 📈 Performance

| Operación | Tiempo |
|-----------|--------|
| Generar guión (Gemini) | 10-15s |
| Generar audio | 1-2 min |
| Transcribir | 2-3 min |
| Componer video | 15-20 min |
| Upscale 1080p | 5-10 min |
| Total | **30-60 min** |

---

## 🐛 Troubleshooting

### El servidor no inicia

```bash
# Verificar puerto 8000 disponible
lsof -i :8000
# Si está en uso, cambiar puerto en api_server.py

# Reinstalar dependencias
pip install --force-reinstall -r requirements.txt
```

### Generar video falla

```bash
# Ver logs
python api_server.py  # Ve los mensajes de error

# Verificar FFmpeg
ffmpeg -version

# Reinstalar
pip install moviepy imageio-ffmpeg --force-reinstall
```

### Gemini API Key no funciona

```bash
# Verificar variable
echo $GEMINI_API_KEY

# Configurar nuevamente
export GEMINI_API_KEY="tu_clave_aqui"

# Obtener clave en: https://aistudio.google.com/
```

---

## 📊 Roadmap

### ✅ Completado
- [x] Múltiples escenas
- [x] Narración automática
- [x] Subtítulos sincronizados
- [x] Intro/Outro animadas
- [x] Upscale 1080p
- [x] Generación con IA
- [x] Interfaz web sin código
- [x] Dashboard en vivo
- [x] Deployment ready

### 🔜 Próximo
- [ ] Avatar/persona en video
- [ ] Soporte YouTube upload
- [ ] Batch processing
- [ ] Más lenguajes (English, Português)
- [ ] Editor visual de guiones
- [ ] Plantillas personalizadas

---

## 💰 Costos

| Servicio | Costo |
|----------|-------|
| **Vercel** (Frontend) | $0 (gratis) |
| **Railway** (Backend) | $5-10/mes |
| **Gemini API** | $0 (gratis con límites) |
| **Total** | **~$5-10/mes** |

---

## 📄 Licencia

MIT License - Libre para uso personal y comercial.

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📞 Contacto & Soporte

- 📧 Email: medal.code@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/Medalcode/canal-tutorial-automation/issues)
- 💬 Discussiones: [GitHub Discussions](https://github.com/Medalcode/canal-tutorial-automation/discussions)

---

## 🎯 Estadísticas del Proyecto

```
📝 Líneas de código: 2000+
📚 Documentación: 1600+ líneas
🎬 Vídeos generados: 1 demo
⚡ Tiempo de setup: 5 minutos
💾 Tamaño repo: ~2 MB
```

---

## 🌟 Características Destacadas

```
┌─────────────────────────────────────┐
│  🎬 VIDEO GENERATOR PRO             │
├─────────────────────────────────────┤
│ ✨ Interfaz sin código              │
│ 🤖 Generación automática con IA     │
│ 📊 Dashboard en vivo                │
│ 🎨 Diseño moderno (dark mode)       │
│ 📱 Responsive                       │
│ 🚀 Deployment ready                 │
│ 💰 Costo bajo ($5-10/mes)          │
│ 🔧 Fácil de personalizar            │
└─────────────────────────────────────┘
```

---

## 🎓 Aprendimiento

Este proyecto enseña:

- 🎬 Procesamiento de video con Python
- 🎙️ Síntesis de voz y procesamiento de audio
- 🤖 Integración con APIs de IA
- 🌐 Desarrollo full-stack (FastAPI + Frontend)
- 🐳 Containerización con Docker
- ☁️ Deployment en la nube
- 📊 Monitoreo en tiempo real

---

## 🏆 Logros

✅ **Video profesional 1080p @ 5Mbps**  
✅ **Interfaz web intuitiva**  
✅ **Generación automática con Gemini IA**  
✅ **Deployment en producción**  
✅ **Costo <$1/mes**  
✅ **Totalmente automatizado**  

---

**¡Crea videos educativos profesionales sin escribir código!** 🎬✨

**[Empieza aquí →](INICIO_RAPIDO.md)**

