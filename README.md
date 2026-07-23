# 🎬 Video Generator Pro — n8n + LTX Video

> **Genera tutoriales en video con IA de principio a fin, sin escribir código.**

Pipeline automatizado para generar tutoriales en video usando **n8n** como orquestador de workflows y **LTX Video** (LTX-2.3 de Lightricks) como motor de generación de video con IA. Narración TTS, subtítulos automáticos, música de fondo y subida a YouTube — todo orquestado visualmente.

[![n8n](https://img.shields.io/badge/n8n-Workflow%20Automation-FF6D5A.svg?logo=n8n)](https://n8n.io)
[![LTX Video](https://img.shields.io/badge/LTX%20Video-AI%20Generation-blueviolet.svg)](https://github.com/Lightricks/ltx-video)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🏗️ Arquitectura (40/60 Split-Screen)

Para optimizar el uso de VRAM (8GB) y acelerar la renderización de tutoriales, el sistema emplea una técnica de pantalla dividida 40/60:

- **40% Izquierdo (Avatar)**: Renderizado dinámico de LTX-Video o imagen animada de un avatar (ej. estilo Ghibli).
- **60% Derecho (Código)**: El código generado por Qwen se renderiza automáticamente en una ventana de VS Code simulada (Pillow + Pygments) sin requerir IA generativa de video para esta zona estática.
- **FFmpeg Composite**: Une ambas partes con el audio TTS en un video HD final (1920x1080) en milisegundos.

```
┌─────────────────────────────────────────────────────────────────┐
│                       n8n (Orquestador)                         │
│  Webhook → Ollama (Qwen) → Split Scenes → LTX → Compose → YT    │
└──────────┬──────────────────────────────────┬────────────────┘
           │                                  │
    ┌──────▼──────┐                   ┌───────▼───────┐
    │ LTX Server  │                   │ Compose 40/60 │
    │ FastAPI     │                   │ Avatar + Code │
    │ :8080       │                   │ (ffmpeg+TTS)  │
    │ GPU (4060)  │                   └───────────────┘
    └─────────────┘
           │
    ┌──────▼──────┐    ┌─────────┐    ┌──────▼──────┐
    │ PostgreSQL  │    │  Redis  │    │   Ollama    │
    │   (n8n DB)  │    │ (Queue) │    │(Qwen2.5 7B) │
    └─────────────┘    └─────────┘    └─────────────┘
```

### Componentes

| Servicio | Descripción | Puerto |
|----------|-------------|--------|
| **n8n** | Orquestador de workflows visual | `5678` |
| **n8n-worker** | Ejecutor de tareas en cola | — |
| **ltx-inference** | API REST de generación de video (LTX-2.3) | `8080` |
| **Ollama** | Motor local para LLM (Qwen2.5-Coder) | `11434` |
| **PostgreSQL** | Base de datos persistente para n8n | `5432` |
| **Redis** | Cola de mensajes para ejecución distribuida | `6379` |

---

## 🚀 Inicio Rápido

### Requisitos

- **Docker** + **Docker Compose** v2+
- **NVIDIA GPU** con drivers instalados (RTX 4060 o superior)
- **NVIDIA Container Toolkit** ([instalación](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html))
- **Gemini API Key** ([obtener gratis](https://aistudio.google.com/app/apikey))

### 1. Clonar y configurar

```bash
git clone https://github.com/Medalcode/canal-tutorial-automation.git
cd canal-tutorial-automation
cp .env.example .env
```

Edita `.env` con tus valores:
```env
POSTGRES_PASSWORD=tu_password_seguro
N8N_ENCRYPTION_KEY=una_clave_aleatoria_larga
GEMINI_API_KEY=tu_clave_de_google_ai_studio
```

### 2. Levantar el stack

```bash
docker compose up -d
```

La primera vez tardará en descargar los modelos de LTX (~5GB).

### 3. Configurar n8n

1. Abre [http://localhost:5678](http://localhost:5678)
2. Crea tu cuenta de administrador
3. Ve a **Settings → Credentials** y añade tu Gemini API Key como "Query Auth" credential
4. Importa el workflow: **Settings → Import Workflow** → selecciona `n8n-workflows/01-generate-tutorial.json`

### 4. Generar un tutorial

Envía un POST al webhook:
```bash
curl -X POST http://localhost:5678/webhook/generate-tutorial \
  -H "Content-Type: application/json" \
  -d '{"topic": "Cómo funciona la inteligencia artificial", "num_scenes": 5}'
```

---

## 📁 Estructura del Proyecto

```
canal-tutorial-automation/
├── docker-compose.yml          # Stack completo (n8n + postgres + redis + ltx)
├── .env.example                # Template de variables de entorno
├── ltx-server/                 # Servidor de inferencia LTX Video
│   ├── main.py                 # FastAPI endpoints
│   ├── inference.py            # Pipeline LTX-2.3 (optimizado 8GB VRAM)
│   ├── Dockerfile              # Imagen CUDA + Python
│   └── requirements.txt        # Dependencias del servidor
├── compose/                    # Scripts de composición de video
│   ├── add_narration.py        # TTS con edge-tts (español)
│   ├── add_subtitles.py        # Subtítulos con faster-whisper
│   ├── add_music.py            # Mezcla de música de fondo
│   ├── concat_clips.py         # Concatenación con crossfade
│   ├── final_render.sh         # Pipeline completo de render
│   └── requirements.txt        # Dependencias de composición
├── n8n-workflows/              # Workflows exportados para n8n
│   └── 01-generate-tutorial.json
├── models/                     # Modelos LTX descargados (gitignored)
├── output/                     # Videos generados (gitignored)
└── assets/                     # Fuentes y música de fondo
```

---

## 🔧 API del Servidor LTX

El servidor de inferencia expone estos endpoints:

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/health` | Health check + estado GPU |
| `POST` | `/generate` | Generar video desde texto (async) |
| `POST` | `/generate/i2v` | Generar video desde imagen (async) |
| `GET` | `/status/{job_id}` | Estado de un job |
| `GET` | `/download/{job_id}` | Descargar video generado |
| `GET` | `/jobs` | Listar todos los jobs |

### Ejemplo: Text-to-Video

```bash
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Cinematic shot of a futuristic coding workspace with holographic displays, warm ambient lighting, camera slowly dollying in",
    "width": 512,
    "height": 320,
    "num_frames": 97,
    "num_inference_steps": 30
  }'
```

---

## ⚙️ Configuración de Hardware

### RTX 4060 (8GB VRAM) — Optimizaciones aplicadas:
- **Sequential CPU Offloading**: Imprescindible para cargar el gigantesco encoder de texto T5-XXL (22GB) por partes sin colapsar la VRAM de 8GB.
- **bfloat16 precision**: Para reducir a la mitad el tamaño del modelo principal.
- **Desactivación de VAE Tiling**: Fundamental para LTX-Video. El tiling daña los VAE 3D de video causando ruido estático (manchas de colores).
- **Resolución y Frames**: Establecido a 512×320 a 49 frames (~2s) para máxima estabilidad.
- **PyTorch Memory Fragmentation**: Se inyectó `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` para evitar colapsos por fragmentación.
- **Ollama Alternativo**: Ollama se configura con `OLLAMA_KEEP_ALIVE=0` para que el modelo Qwen libere la GPU instantáneamente antes de que LTX comience a renderizar.

### Rendimiento esperado:
| Resolución | Frames | Tiempo aprox. | Consumo VRAM |
|------------|--------|---------------|--------------|
| 512×320 | 49 (~2s) | ~59 segundos  | ~7.0 GB      |

---

## 🔒 Seguridad

Los siguientes archivos están en `.gitignore`:
- `.env` — Contraseñas y API Keys
- `models/` — Modelos de IA descargados
- `output/` — Videos generados
- `postgres_data/`, `redis_data/`, `n8n_data/` — Datos de Docker

---

## 📄 Licencia

MIT License — libre para uso personal y comercial.
