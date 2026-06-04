# 🎬 Video Generator Pro - Web Interface

Panel de control web para generar videos automáticamente sin código.

## ✨ Características

- 🎨 **Interfaz moderna** - Dark mode, responsive, intuitiva
- 🤖 **Generación con IA** - Gemini API para guiones automáticos
- 📝 **Editor de guiones** - Editar escenas en vivo
- 🎬 **Generación de videos** - Con todas las mejoras de calidad
- 📊 **Dashboard** - Estadísticas en tiempo real
- ⏳ **Monitor de progreso** - Seguimiento en vivo de trabajos
- 📥 **Descargas** - Acceso a todos los videos generados
- 🔄 **Actualizaciones en vivo** - Auto-refresh de estados

## 🚀 Instalación

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar Gemini IA (opcional)

Para generar guiones con IA automáticamente:

```bash
export GEMINI_API_KEY="tu_clave_api_aqui"
```

Obtén una clave gratis en: https://aistudio.google.com/

### 3. Iniciar el servidor

```bash
python api_server.py
```

Luego abre en tu navegador: **http://localhost:8000**

## 🎯 Uso

### Panel Principal (Dashboard)

Al abrir la interfaz, verás:
- 📊 Estadísticas: Videos, Guiones, Trabajos, Espacio usado
- 📋 Últimos trabajos con estado
- 🔄 Botones de actualización

### Generar un Video

#### Opción 1: Desde Guión Existente

1. Ve a **"Generar Video"**
2. Elige el tab **"Manual"**
3. Selecciona un guión del dropdown
4. Haz clic en **"Generar Video"**
5. Monitorea el progreso en la ventana emergente

#### Opción 2: Con Gemini IA (Recomendado)

1. Ve a **"Generar Video"**
2. Elige el tab **"Con IA (Gemini)"**
3. Ingresa el tema (ej: "FastAPI para principiantes")
4. Selecciona número de escenas (3-10)
5. Haz clic en **"Generar con Gemini IA"**
6. El sistema generará el guión automáticamente
7. Luego generará el video

### Administrar Guiones

#### Crear Guión

1. Ve a **"Guiones"**
2. Haz clic en **"+ Crear Guión"**
3. Edita escenas en la ventana modal
4. Guarda cambios

#### Editar Guión

1. Ve a **"Guiones"**
2. Haz clic en **"✏️ Editar"** en la tarjeta del guión
3. Modifica escenas (ID, Título, Narración)
4. Haz clic en **"Guardar Guión"**

#### Generar Video desde Guión

1. Ve a **"Guiones"**
2. Haz clic en **"▶️ Generar"** en cualquier guión

### Descargar Videos

1. Ve a **"Mis Videos"**
2. Haz clic en **"⬇️ Descargar"** para el video deseado
3. El archivo `.mp4` se descargará automáticamente

### Ver Estado de Trabajos

1. Ve a **"Trabajos"**
2. Monitorea el estado y progreso de cada trabajo
3. Estados posibles:
   - ⏳ **queued** - En cola
   - 🔄 **generating** - Generando
   - ✅ **completed** - Completado
   - ❌ **failed** - Error

## 🏗️ Arquitectura

```
Frontend (Web Browser)
        ↓
    HTML/CSS/JS
        ↓
    API REST
        ↓
Backend (FastAPI)
    ├── /api/scripts/generate    → Generar con Gemini IA
    ├── /api/scripts/{id}        → Ver/Editar guión
    ├── /api/videos/generate     → Generar video
    ├── /api/jobs/{id}           → Ver estado de trabajo
    ├── /api/files               → Listar/Descargar archivos
    └── /api/health              → Estado del servidor
        ↓
    Background Tasks
    ├── generate_video.py        → Motor de generación
    ├── script_generator_pro.py  → Generador de guiones
    └── Gemini IA API
```

## 📁 Estructura de Archivos

```
canal-tutorial-automation/
├── api_server.py                    # Backend FastAPI
├── generate_video.py                # Motor de generación
├── script_generator_pro.py          # Generador de guiones
├── requirements.txt                 # Dependencias
├── script.json                      # Guión actual
├── web/
│   ├── index.html                  # Interfaz principal
│   ├── styles.css                  # Estilos modernos
│   └── app.js                       # Lógica frontend
├── scripts/                         # Guiones guardados
├── output/                          # Videos generados
└── .jobs/                           # Estados de trabajos
```

## 🔑 API Endpoints

### Scripts

```bash
# Listar guiones
GET /api/scripts

# Ver guión
GET /api/scripts/{script_id}

# Editar guión
PUT /api/scripts/{script_id}

# Generar guión con IA
POST /api/scripts/generate
{
  "topic": "FastAPI",
  "num_scenes": 5
}
```

### Videos

```bash
# Generar video
POST /api/videos/generate?script_id={id}

# Ver estado de trabajo
GET /api/jobs/{job_id}

# Listar trabajos
GET /api/jobs

# Listar archivos
GET /api/files

# Descargar archivo
GET /api/files/{filename}

# Eliminar archivo
DELETE /api/files/{filename}
```

## ⚙️ Configuración

### Variables de Entorno

```bash
# Gemini IA (para generación automática de guiones)
export GEMINI_API_KEY="tu_clave"

# FastAPI (host/puerto)
export HOST="0.0.0.0"
export PORT="8000"
```

### Personalización

Edita `generate_video.py`:

```python
VOICE = "es-MX-DaliaNeural"    # Cambiar voz
W, H = 1280, 720              # Resolución base
BG_COLOR = (20, 22, 28)       # Color fondo
```

## 🎬 Ejemplos de Uso

### Generar Video sobre Docker

1. Ve a **"Generar Video" → "Con IA"**
2. Ingresa: `Docker para principiantes`
3. Escenas: `6`
4. Haz clic: **"Generar con Gemini IA"**
5. Espera a que se complete (~40 min)
6. Descarga en **"Mis Videos"**

### Editar Guión Existente

1. Ve a **"Guiones"**
2. Haz clic en **"✏️ Editar"**
3. Cambia textos, títulos, comandos
4. Haz clic: **"Guardar Guión"**
5. Luego: **"▶️ Generar"**

## 📊 Monitoreo

### En Tiempo Real

- El progreso se actualiza cada segundo
- Barra de progreso animada
- Mensaje de estado actual
- ID del trabajo para referencia

### Dashboard

- Estadísticas automáticas
- Último trabajos listados
- Actualización con botón 🔄

## 🐛 Troubleshooting

### Error: "GEMINI_API_KEY no configurada"

```bash
export GEMINI_API_KEY="tu_clave"
python api_server.py
```

### Error: "Puerto 8000 en uso"

```bash
# Usar otro puerto
uvicorn api_server:app --port 8001
```

### Video lento generándose

- Esto es normal (30-60 min con calidad 1080p @ 5Mbps)
- Cierra la pestaña si deseas, el video continúa en background
- Ve a **"Trabajos"** para monitorear

### API no responde

```bash
# Verificar servidor
curl http://localhost:8000/api/health
```

## 📈 Performance

| Operación | Tiempo |
|-----------|--------|
| Generar guión (Gemini) | 10-15s |
| Generar video | 30-60 min |
| Upscale a 1080p | 5-10 min |
| Descargar archivo | <1s |

## 🔐 Seguridad

- ✅ API validada con Pydantic
- ✅ Archivos en directorio aislado
- ✅ Sin exposición de rutas del sistema
- ✅ CORS deshabilitado (localhost only)

Para producción, añade:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["tu_dominio.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📚 Stack Tecnológico

- **Backend**: FastAPI + Uvicorn
- **Frontend**: HTML5 + CSS3 + JavaScript Vanilla
- **IA**: Google Gemini API
- **Procesamiento**: FFmpeg, moviepy, faster-whisper
- **Audio**: edge-tts, Python

## 🚀 Deploy

### En servidor Linux

```bash
# Instalar
git clone <repo>
cd canal-tutorial-automation
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Ejecutar con Systemd
sudo systemctl start video-generator
```

### Con Docker

```bash
# Crear Dockerfile
FROM python:3.10
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "api_server.py"]

# Build y run
docker build -t video-gen .
docker run -p 8000:8000 video-gen
```

## 📞 Soporte

- 📖 Documentación: Ver MEJORAS.md, README.md
- 🐛 Bugs: Reportar en issues
- 💡 Sugerencias: Abrir discussion

## 📝 Licencia

MIT - Libre para uso personal y comercial

---

**¡Crea videos educativos sin escribir código!** 🎬✨
