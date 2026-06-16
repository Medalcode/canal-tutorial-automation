# 🎬 Video Generator Pro - Canal Tutorial Automation

> **De una idea a YouTube en un solo clic, sin escribir código.**

Pipeline automatizado para generar tutoriales en video con IA, narración, subtítulos, música y calidad 1080p @ 5Mbps, con subida automática a YouTube. Interfaz web intuitiva, FastAPI backend, Gemini 2.5 IA.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()
[![Vercel](https://img.shields.io/badge/Vercel-Deployed-black.svg?logo=vercel)](https://canal-tutorial-automation.vercel.app)

---

## ✨ Características

### 🤖 Inteligencia Artificial (Gemini 2.5)
- ✅ Generación automática de guiones con Gemini 2.5 Flash
- ✅ Generación de **Título optimizado para YouTube** (SEO)
- ✅ Generación de **Descripción** detallada para YouTube
- ✅ Generación de **Etiquetas/Hashtags** relevantes
- ✅ Estructura automática con intro, desarrollo y outro

### 📺 Subida Automática a YouTube
- ✅ Integración con YouTube Data API v3
- ✅ Subida directa sin salir de la aplicación
- ✅ Videos publicados como **Públicos** automáticamente
- ✅ Marcados como **Contenido apto para niños**
- ✅ Autenticación OAuth 2.0 segura (token guardado localmente)

### 🎙️ Audio & Narración
- ✅ Voces naturales en español con edge-tts
- ✅ Normalización y compresión de audio automática
- ✅ Música de fondo balanceada (descarga automática si no existe)
- ✅ Bitrate 192kbps (calidad superior)

### 📝 Subtítulos & Texto
- ✅ Subtítulos sincronizados (word-level)
- ✅ Detección automática con faster-whisper
- ✅ Títulos de escenas con fuente profesional
- ✅ Overlay estilo terminal (código verde)

### 🎬 Video & Composición (MoviePy)
- ✅ Composición 100% nativa en Python con MoviePy (sin dependencias Node.js)
- ✅ Soporte para concurrencia masiva (múltiples renderizados simultáneos)
- ✅ Base de Datos local (SQLite) integrada para historial de trabajos
- ✅ Renderizado optimizado de pantalla dividida con avatares e IDE animado
- ✅ Resolución 1920x1080 Full HD a 30 FPS

### 🌐 Interfaz Web
- ✅ Panel de control moderno (dark mode)
- ✅ Dashboard con estadísticas en vivo
- ✅ Monitor de progreso en tiempo real
- ✅ Responsive (desktop/mobile)

### 📦 Deployment
- ✅ Docker support
- ✅ Vercel + Railway ready

---

## 🚀 Inicio Rápido (Local)

### 1. Clonar y preparar el entorno

```bash
git clone https://github.com/Medalcode/canal-tutorial-automation.git
cd canal-tutorial-automation
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar las claves

Crea un archivo `.env` en la raíz del proyecto:

```env
GEMINI_API_KEY=tu_clave_de_google_ai_studio
```

Obtén tu clave gratis en: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

### 3. Configurar YouTube (primera vez)

Para habilitar la subida automática a YouTube necesitas:

1. Ir a [Google Cloud Console](https://console.cloud.google.com/) y crear un proyecto.
2. Habilitar la **YouTube Data API v3**.
3. Crear credenciales **OAuth 2.0 Client ID** (tipo: Aplicación de escritorio).
4. Descargar el JSON y guardarlo como `client_secret.json` en la raíz del proyecto.
5. En la Pantalla de Consentimiento OAuth, añadir tu correo como **Usuario de Prueba**.

### 4. Lanzar la aplicación

**Opción A — Doble clic (más fácil):**

Haz doble clic en el archivo `iniciar.sh` y selecciona "Ejecutar como programa".
La primera vez te pedirá autorizar tu cuenta de YouTube en el navegador.

**Opción B — Terminal:**

```bash
source venv/bin/activate
python api_server.py
```

Luego abre [http://localhost:8001](http://localhost:8001) en tu navegador.

---

## 🎯 Flujo de Uso

```
1. Escribe tus ideas en el cuadro de texto
        ↓
2. Pulsa "Que la IA haga el Guion"
   (Gemini genera guion + título + descripción + etiquetas)
        ↓
3. Revisa y edita el título y descripción si lo deseas
        ↓
4. Pulsa "🔴 Crear Video y Subir a YouTube"
        ↓
5. El video se genera y se sube automáticamente como Público
```

---

## 📁 Estructura del Proyecto

```
canal-tutorial-automation/
├── api_server.py          # Backend FastAPI con Base de Datos SQLite
├── generate_video.py      # Motor de video optimizado con MoviePy
├── ide_simulator.py       # Simulación de IDE visual
├── script_generator_pro.py# Generación de guion con Gemini 2.5
├── youtube_uploader.py    # Módulo de subida a YouTube
├── database.sqlite        # Historial de trabajos y metadatos
├── iniciar.sh             # Script de inicio
├── requirements.txt       # Dependencias Python
├── web/
│   ├── index.html         # Interfaz web
│   └── app.js             # Lógica del frontend
├── assets/                # Fuentes y música de fondo
├── output/                # Videos generados (ignorado por git)
├── .env                   # Claves secretas (NO subir a GitHub)
└── client_secret.json     # Credenciales OAuth (NO subir a GitHub)
```

---

## 🔒 Seguridad

Los siguientes archivos están en `.gitignore` y **nunca** se suben a GitHub:
- `.env` — API Keys
- `client_secret.json` — Credenciales OAuth de Google
- `youtube_token.pkl` — Token de acceso de YouTube
- `output/` — Videos generados

---

## 🛠️ Requisitos

- Python 3.10+
- ffmpeg (instalado en el sistema)
- Cuenta de Google AI Studio (Gemini API key gratuita)
- Cuenta de YouTube con canal propio

---

## 📄 Licencia

MIT License — libre para uso personal y comercial.
