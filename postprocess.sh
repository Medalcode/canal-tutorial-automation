#!/bin/bash
# Post-procesamiento: añade música de fondo y genera thumbnail
# Uso: bash postprocess.sh

set -e

INPUT="output/video_final.mp4"
MUSIC="assets/musica_fondo.mp3"
OUTPUT_NO_MUSIC="output/video_sin_musica.mp4"
OUTPUT_FINAL="output/video_con_musica.mp4"
THUMBNAIL="output/thumbnail.png"
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# 1. Copia el video generado por moviepy
cp "$INPUT" "$OUTPUT_NO_MUSIC"

# 2. Mezcla música de fondo con ffmpeg (más rápido que moviepy)
if [ -f "$MUSIC" ]; then
    echo "Añadiendo música de fondo..."
    ffmpeg -y -i "$OUTPUT_NO_MUSIC" -i "$MUSIC" \
        -filter_complex \
        "[1:a]volume=0.08,afade=t=in:d=3,afade=t=out:st=0:d=5[music]; \
         [0:a][music]amix=inputs=2:duration=first[audio]" \
        -map 0:v -map "[audio]" -c:v copy -c:a aac -shortest \
        "$OUTPUT_FINAL"
    echo "Video con música: $OUTPUT_FINAL"
else
    echo "No se encuentra $MUSIC, saltando música"
    cp "$OUTPUT_NO_MUSIC" "$OUTPUT_FINAL"
fi

# 3. Genera thumbnail automático (frame del medio + overlay de texto)
if command -v ffmpeg &> /dev/null; then
    DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUTPUT_FINAL")
    MID_TIME=$(echo "$DUR / 2" | bc -l)
    ffmpeg -y -ss "$MID_TIME" -i "$OUTPUT_FINAL" -vframes 1 "$THUMBNAIL" 2>/dev/null
    echo "Thumbnail: $THUMBNAIL"
fi

echo "Post-procesamiento completado."
