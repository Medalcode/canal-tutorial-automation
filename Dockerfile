FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para FFmpeg y procesamiento de video
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar resto de la aplicación
COPY . .

# Crear directorio de output
RUN mkdir -p output scripts .jobs web

# Exponer puerto
EXPOSE 8000

# Variable de entorno para desarrollo
ENV PYTHONUNBUFFERED=1

# Comando de inicio
CMD ["python", "api_server.py"]
