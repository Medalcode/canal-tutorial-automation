# Canal Tutorial Automation

Pipeline automatizado para generar videos de tutoriales de programación usando Python, edge-tts, faster-whisper y moviepy.

## Características

- 🎙️ **Narración automática** con edge-tts (voces naturales, español)
- 📝 **Subtítulos sincronizados** vía faster-whisper (word-level timestamps)
- 🎬 **Múltiples escenas** por secciones del guion
- 💻 **Overlay estilo terminal** con código monoespaciado verde
- 🎵 **Música de fondo** con fade in/out
- 🖼️ **Thumbnail automático** desde frame intermedio
- 📺 **Upscale a 1080p** en post-procesamiento
- ✨ **Intro animada** y **Outro** con botón de suscripción

## Requisitos

- Python 3.10+
- ffmpeg (incluido automáticamente vía imageio-ffmpeg)

## Instalación

```bash
git clone https://github.com/Medalcode/canal-tutorial-automation.git
cd canal-tutorial-automation
python3 -m venv venv
source venv/bin/activate
pip install edge-tts moviepy faster-whisper imageio-ffmpeg
```

## Uso

### 1. Escribir el guion

Edita `guion.txt` con el contenido del video. Usa `##SECCION: nombre` para dividir en escenas:

```
##SECCION: intro
Texto de la introducción...

##SECCION: paso1
Texto del primer paso...
```

### 2. Configurar comandos por escena (opcional)

Edita `SCENE_COMMANDS` en `generate_video.py` para mostrar comandos en el panel terminal de cada escena.

### 3. Generar el video

```bash
python generate_video.py
```

El pipeline completo:
1. Genera audio con edge-tts
2. Transcribe con faster-whisper para subtítulos
3. Compone escenas con moviepy (intro + tutorial + outro)
4. Añade música de fondo
5. Escala a 1080p
6. Genera thumbnail

### 4. Resultados

Todos los archivos se guardan en `output/`:

| Archivo | Descripción |
|---|---|
| `video_con_musica.mp4` | Video final 1080p con música |
| `narracion.mp3` | Audio de la narración |
| `thumbnail.png` | Thumbnail automático |

## Estructura del proyecto

```
canal/
├── guion.txt              # Guion del video (editable)
├── generate_video.py      # Script principal del pipeline
├── assets/
│   ├── fondo.jpg          # Imagen de fondo por defecto
│   ├── musica_fondo.mp3   # Música de fondo
│   └── scene_*.jpg        # Imágenes por escena (opcional)
└── output/
    ├── video_con_musica.mp4
    ├── narracion.mp3
    └── thumbnail.png
```

## Personalización

- **Voces**: cambiar `VOICE` en `generate_video.py` (ej: `es-ES-AlvaroNeural`, `es-MX-JorgeNeural`)
- **Resolución**: cambiar `W, H` en `generate_video.py`
- **Imágenes por escena**: añadir `assets/scene_NOMBRE.jpg` para cada `##SECCION: NOMBRE`
- **Música**: reemplazar `assets/musica_fondo.mp3`

## Roadmap

- [x] Múltiples escenas
- [x] Overlay estilo terminal
- [x] Música de fondo
- [x] Subtítulos sincronizados
- [x] Intro/Outro animadas
- [x] Upscale 1080p
- [ ] pycoding: tutoriales con ejecución de código real
- [ ] Avatar/cara sobreimpreso
- [ ] Generación de guion con IA
- [ ] Batch processing
- [ ] Subida automática a YouTube

## Licencia

MIT
