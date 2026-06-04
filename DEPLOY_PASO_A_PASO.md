# 🚀 Guía de Deploy Vercel + Railway (Paso a Paso)

## ⚡ TL;DR (Quick Start)

```bash
# 1. Backend en Railway
railway login
railway init  # Elegir Python
railway up

# 2. Frontend en Vercel
vercel --prod

# 3. Conectar en Vercel Dashboard
# Agregar env: VITE_API_URL=<railway_url>
```

---

## 📋 Requisitos

- ✅ Token de Vercel (ya tienes)
- ✅ Cuenta Railway (gratis)
- ✅ Cuenta GitHub (para conectar repos)
- ✅ Gemini API Key (gratis)

---

## Fase 1: Preparar GitHub

### 1. Crear repo en GitHub

```bash
git init
git add .
git commit -m "initial: Video Generator Pro ready to deploy"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/canal-tutorial-automation.git
git push -u origin main
```

O usar CLI de GitHub:

```bash
gh repo create canal-tutorial-automation --public --source=. --remote=origin --push
```

---

## Fase 2: Deploy Backend en Railway (10 minutos)

### Opción A: Con CLI de Railway (Recomendado)

```bash
# 1. Instalar Railway
curl -fsSL https://railway.app/install.sh | sh

# 2. Login con GitHub
railway login

# 3. Crear proyecto
railway init

# 4. Seleccionar "Python" y crear
# 5. Agregar variable de entorno
railway variables set GEMINI_API_KEY="tu_clave_aqui"

# 6. Deploy
railway up

# 7. Ver URL generada
railway open
```

### Opción B: Via Dashboard Railway.app

1. Ir a **railway.app**
2. Click en **"New Project"**
3. Seleccionar **"Deploy from GitHub"**
4. Conectar tu repo
5. Seleccionar branch: **main**
6. Vercel auto-detectará `Dockerfile` y `requirements.txt`
7. Configurar variables:
   - `GEMINI_API_KEY`: tu_clave_aqui
8. Click **"Deploy"**

### 8. Copiar URL de Railway

```
Ej: https://video-generator-api-production.railway.app
```

Guardar esta URL para el siguiente paso.

---

## Fase 3: Deploy Frontend en Vercel (5 minutos)

### Opción A: Con Vercel CLI

```bash
# 1. Instalar Vercel CLI
npm install -g vercel

# 2. Hacer login
vercel login

# 3. Deploy
vercel --prod

# 4. En la pregunta "Link to existing project?": NO
# 5. En "Set up and deploy?": YES
```

### Opción B: Via GitHub + Vercel.com (Recomendado)

1. Ir a **vercel.com**
2. Click **"New Project"**
3. Seleccionar tu repo GitHub
4. Configurar:
   - **Framework Preset**: "Other"
   - **Root Directory**: "./" (default)
   - **Build Command**: (dejar vacío)
   - **Output Directory**: "web"
5. Click **"Environment Variables"**
6. Agregar:
   ```
   VITE_API_URL = https://video-generator-api-production.railway.app
   ```
7. Click **"Deploy"**

### URLs Resultantes

```
Frontend:  https://TU_PROYECTO.vercel.app
Backend:   https://video-generator-api-production.railway.app
```

---

## Fase 4: Conectar Frontend ↔ Backend

### En web/app.js (línea 13-20)

```javascript
const API = {
    async get(endpoint) {
        const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const res = await fetch(`${baseURL}/api${endpoint}`);
        if (!res.ok) throw new Error(`API Error: ${res.status}`);
        return res.json();
    },
    // ... resto del código
}
```

### Crear archivo .env

```env
VITE_API_URL=https://video-generator-api-production.railway.app
```

### Push cambios

```bash
git add web/app.js .env
git commit -m "chore: configure API URL for production"
git push
```

Vercel auto-redeploya.

---

## Fase 5: Configurar Gemini API

### En Railway Dashboard

1. Ir a tu proyecto en railway.app
2. Tab **"Variables"**
3. Click **"+ New"**
4. **Key**: `GEMINI_API_KEY`
5. **Value**: `tu_clave_de_gemini`
6. Click **"Add Variable"**
7. Auto-redeploy

### Verificar que funciona

```bash
curl https://video-generator-api-production.railway.app/api/health
```

Deberías ver:

```json
{
  "status": "ok",
  "version": "1.0",
  "timestamp": "2024-06-04T..."
}
```

---

## Fase 6: Probar en Producción

### 1. Abrir Frontend

```
https://tu-proyecto.vercel.app
```

### 2. Generar un Video

1. Click **"Generar Video"**
2. Click **"Con IA (Gemini)"**
3. Escribe un tema
4. Click **"Generar con Gemini IA"**
5. Monitorea el progreso

### 3. Verificar Logs

```bash
# Railway
railway logs

# Vercel
vercel logs --prod
```

---

## 🔧 Troubleshooting

### Error 404 en API

**Problema**: Frontend no encuentra backend

**Solución**:
```bash
# Verificar URL
curl https://video-generator-api-production.railway.app/api/health

# Si no funciona, revisar Railway logs
railway logs
```

### Error CORS

**Problema**: `Access-Control-Allow-Origin`

**Solución** (en api_server.py):

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tu-proyecto.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Video no genera

**Problema**: Timeout o error en Railway

**Verificar**:
```bash
# Logs
railway logs

# Variables
railway variables

# Health
curl https://video-generator-api-production.railway.app/api/health
```

### Gemini API Key inválida

**Problema**: `GEMINI_API_KEY no configurada`

**Solución**:
1. Ir a railway.app dashboard
2. Click Variables
3. Editar `GEMINI_API_KEY`
4. Pegar clave correcta

---

## 📊 Monitoreo en Producción

### Railway Dashboard

```bash
railway open
# O ir a railway.app → Click proyecto
```

Ver:
- 📊 Métricas (CPU, RAM, Red)
- 📝 Logs en tiempo real
- 🔄 Deploy history
- ⚙️ Variables

### Vercel Dashboard

```bash
vercel dashboard
# O ir a vercel.com
```

Ver:
- 📊 Traffic analytics
- 📝 Function logs
- 🔄 Deploy history
- 📈 Performance

---

## 🚀 Comandos Útiles

### Railway

```bash
# Ver logs en vivo
railway logs --follow

# Redeploy
railway up

# Ver variables
railway variables

# Editar variable
railway variables set GEMINI_API_KEY="nueva_clave"

# Ver URL
railway domains

# Monitorear métricas
railway monitor
```

### Vercel

```bash
# Ver logs
vercel logs --prod

# Listar deployments
vercel list

# Revert a deploy anterior
vercel rollback

# Rebuild
vercel rebuild --prod
```

---

## 💾 Backup de Datos

Los videos se guardan en Railway `/app/output/`

### Descargar videos

```bash
# SSH a Railway
railway ssh

# Listar videos
ls output/

# Descargar
railway volumes ls
```

---

## 🔐 Seguridad

### Cambiar Gemini API Key

Si crees que fue comprometida:

```bash
railway variables set GEMINI_API_KEY="nueva_clave_segura"
```

### Rate Limiting

En `api_server.py`:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/videos/generate")
@limiter.limit("5/minute")
async def generate_video(...):
    # ...
```

---

## 📈 Escalabilidad

Si tienes muchos usuarios:

### Railway Pro

```bash
railway account upgrade
# Más RAM, mejor performance
```

### Vercel Pro

Similar para frontend.

### Load Balancing

Si Railway se sobrecarga:
- Usar Railway Replica
- O migrar a Cloud Run (Google)

---

## 🎯 Checklist Final

- [ ] Repo en GitHub
- [ ] Backend en Railway
- [ ] Frontend en Vercel
- [ ] Conectados correctamente
- [ ] Gemini API Key configurada
- [ ] Health check: `curl api/health`
- [ ] Video generándose correctamente
- [ ] Videos descargables
- [ ] Logs accesibles
- [ ] Monitoreo en vivo

---

## 📞 URLs de Referencia

- **Railway Docs**: https://docs.railway.app
- **Vercel Docs**: https://vercel.com/docs
- **Gemini API**: https://aistudio.google.com
- **FastAPI**: https://fastapi.tiangolo.com

---

## 🎉 ¡Listo!

Tu aplicación está en producción:

```
🌐 Frontend:  https://tu-proyecto.vercel.app
⚙️ Backend:   https://video-generator-api-production.railway.app
🤖 IA:        Gemini API integrada
📹 Videos:    Generando en tiempo real
```

**¡Ahora puedes crear videos desde cualquier lugar!** 🚀✨
