# 🚀 Deploy en Vercel + Railway (Arquitectura Recomendada)

## ⚠️ Advertencia Importante

**Vercel tiene limitaciones para esta aplicación:**

| Aspecto | Vercel | Necesario |
|--------|--------|----------|
| Timeout máximo | 60s (Pro: 900s) | 30-60 min por video |
| Procesamiento | Serverless | Long-running |
| Almacenamiento | Efímero | Persistente |
| FFmpeg/Media | Limitado | Requerido |

**Solución recomendada: Hybrid Deployment**

```
┌─ Frontend ─────┐      ┌─ Backend ──────┐
│  HTML/CSS/JS   │      │  FastAPI       │
│  Vercel        │──────│  Railway/Render│
│  (Gratis)      │      │  (Procesos>60s)│
└────────────────┘      └────────────────┘
```

---

## Plan A: Frontend en Vercel (Recomendado)

### Paso 1: Preparar Frontend

```bash
# El frontend está listo en web/
# Solo necesita variables de entorno
```

Crear `.env.local`:

```env
NEXT_PUBLIC_API_URL=https://tu-backend.railway.app
```

### Paso 2: Deploy Frontend en Vercel

```bash
# Instalar CLI de Vercel
npm install -g vercel

# Entrar en directorio del proyecto
cd canal-tutorial-automation

# Deploy
vercel deploy --prod
```

O usar GitHub:

1. Push a GitHub
2. Conecta repo en vercel.com
3. Vercel auto-deploya cambios

---

## Plan B: Backend en Railway (Para procesos largo-running)

### Paso 1: Instalar Railway CLI

```bash
# macOS
brew install railway

# Linux/WSL
curl -fsSL https://railway.app/install.sh | sh

# Windows
iwr https://railway.app/install.ps1 -useb | iex
```

### Paso 2: Conectar con Railway

```bash
# Login
railway login

# Configurar proyecto
railway init

# Selecciona "Python" como template
```

### Paso 3: Crear archivo railway.json

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "dockerfile"
  },
  "deploy": {
    "startCommand": "python api_server.py",
    "restartPolicyMaxRetries": 5
  }
}
```

### Paso 4: Crear Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos
COPY . .

# Instalar Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Exponer puerto
EXPOSE 8000

# Comando de inicio
CMD ["python", "api_server.py"]
```

### Paso 5: Deploy en Railway

```bash
# Deploy
railway up

# Ver logs
railway logs

# Ver status
railway status
```

---

## Plan C: Backend en Render (Alternativa a Railway)

### Paso 1: Crear Dockerfile (igual que arriba)

### Paso 2: Push a GitHub

```bash
git add .
git commit -m "feat: preparar para deploy en Render"
git push
```

### Paso 3: Crear en Render.com

1. Ir a render.com
2. Click "New +"
3. Seleccionar "Web Service"
4. Conectar repo GitHub
5. Configurar:
   - **Name**: video-generator-api
   - **Runtime**: Python 3.10
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python api_server.py`

6. Agregar Variables de Entorno:
   - `GEMINI_API_KEY`: tu_clave

7. Click "Deploy"

---

## Configuración Recomendada: Vercel + Railway

### Frontend en Vercel

```bash
# Crear app Vercel simple con Next.js o static
# O subir directamente web/ folder

vercel deploy --prod
```

### Backend en Railway

```bash
railway login
railway init
# Seleccionar "Python"
# Agregar GEMINI_API_KEY
railway up
```

### Conectar Frontend ↔ Backend

En `web/app.js`, cambiar:

```javascript
const API = {
    async get(endpoint) {
        const baseURL = process.env.VITE_API_URL || 'http://localhost:8000';
        const res = await fetch(`${baseURL}/api${endpoint}`);
        // ...
    }
}
```

En Vercel environment variables:

```
VITE_API_URL=https://video-generator-api.railway.app
```

---

## Plan D: Solo Vercel (No recomendado, pero posible)

Si INSISTES en Vercel solamente:

### Limitaciones:
- ❌ Videos muy lentos o timeout
- ❌ Máximo 15 min de procesamiento (Pro)
- ❌ Almacenamiento efímero (videos se pierden)

### Si aún así quieres intentar:

```bash
vercel deploy --prod --env GEMINI_API_KEY=tu_clave
```

**Pero espera fallos con videos largos.**

---

## Comparación de Servicios

| Servicio | Gratis | Timeout | Storage | Recomendado |
|----------|--------|---------|---------|------------|
| **Vercel** | ✅ | 60s/900s | ❌ Efímero | Frontend |
| **Railway** | $5/mes | ✅ Ilimitado | ✅ Sí | ✅ Backend |
| **Render** | ✅ (lento) | ✅ Ilimitado | ✅ Sí | ✅ Backend |
| **Heroku** | ❌ Pagado | ✅ Ilimitado | ✅ Sí | Backend |

---

## Deploy Paso a Paso (Recomendado)

### 1️⃣ Deploy Backend en Railway (5 min)

```bash
# Crear cuenta en railway.app
# Crear nuevo proyecto
# Conectar GitHub

railway login
railway init  # Seleccionar Python
railway up

# Copiar URL de Railway
# Ej: https://video-generator-api-production.railway.app
```

### 2️⃣ Deploy Frontend en Vercel (3 min)

```bash
# Opción A: Con GitHub
# 1. Push a GitHub
# 2. Ir a vercel.com
# 3. Conectar repo
# 4. Auto-deploy

# Opción B: Con CLI
npm install -g vercel
vercel --prod
```

### 3️⃣ Conectar

En Vercel environment:

```env
VITE_API_URL=https://video-generator-api-production.railway.app
```

### 4️⃣ Configurar Gemini en Railway

En Railway dashboard:

```
GEMINI_API_KEY = tu_clave_aqui
```

---

## URLs Finales

```
Frontend: https://video-generator.vercel.app
Backend:  https://video-generator-api-production.railway.app

API Health: https://video-generator-api-production.railway.app/api/health
```

---

## Monitoreo

### Vercel
```bash
vercel logs --prod
```

### Railway
```bash
railway logs
railway monitor
```

---

## Costos

| Servicio | Costo |
|----------|-------|
| Vercel Frontend | **$0** (gratis) |
| Railway Backend | **$5-10/mes** |
| Gemini API | **Gratis** (con límites) |
| **Total** | **~$5-10/mes** |

---

## ¿Preguntas Frecuentes?

**¿Y si quiero solo Vercel?**
No funcionará para videos >60s. Render o Railway son mejores.

**¿Puedo usar Heroku?**
Heroku pagado también sirve, pero Railway/Render son más baratos.

**¿Se pierden los videos?**
No si usas Railway/Render (storage persistente).

**¿Funciona con Vercel Pro?**
Mejor, pero aún insuficiente (900s max).

---

**Recomendación final: Railway + Vercel = La mejor combinación.** 🚀
