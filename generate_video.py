import asyncio
import os
import re
import subprocess
import edge_tts
from moviepy import (
    AudioFileClip,
    ImageClip,
    TextClip,
    CompositeVideoClip,
    ColorClip,
    concatenate_videoclips,
)

import imageio_ffmpeg
FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()

VOICE = "es-MX-DaliaNeural"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
OUTPUT_DIR = "output"
ASSETS_DIR = "assets"
W, H = 1280, 720
BG_COLOR = (20, 22, 28)


def parse_scenes(text: str):
    sections = re.split(r'^##SECCION:\s*(\S+)', text, flags=re.MULTILINE)[1:]
    scenes = []
    for i in range(0, len(sections), 2):
        scene_id = sections[i].strip()
        scene_text = sections[i + 1].strip()
        scenes.append({"id": scene_id, "text": scene_text, "chars": len(scene_text)})
    return scenes


def assign_durations(scenes, total_duration):
    total_chars = sum(s["chars"] for s in scenes)
    for s in scenes:
        s["duration"] = max(8.0, (s["chars"] / total_chars) * total_duration)


def scene_image_path(scene_id):
    for ext in (".jpg", ".png"):
        path = os.path.join(ASSETS_DIR, f"scene_{scene_id}{ext}")
        if os.path.exists(path):
            return path
    return None


def make_background(scene):
    dur = scene["duration"]
    img_path = scene_image_path(scene["id"])
    if img_path:
        return ImageClip(img_path).resized((W, H)).with_duration(dur)
    return ColorClip(size=(W, H), color=BG_COLOR).with_duration(dur)


def make_terminal_panel(commands, duration):
    n = len(commands) or 1
    seg_dur = duration / n
    px, py = 60, H - 560
    pw = W - 120
    clips = []

    clips.append(ColorClip(size=(pw, 500), color=(18, 20, 24)).with_duration(duration).with_position((px, py)))
    clips.append(ColorClip(size=(pw, 2), color=(0, 200, 0)).with_duration(duration).with_position((px, py)))

    for i, cmd in enumerate(commands):
        clips.append(
            TextClip(font=FONT_MONO, text=f"$ {cmd}", font_size=38, color="#00FF00")
            .with_position((px + 30, py + 40 + i * 65))
            .with_duration(seg_dur)
            .with_start(i * seg_dur)
        )
    return clips


SCENE_COMMANDS = {
    "intro": ["# Android como Servidor", "# Termux + Python + FastAPI"],
    "instalacion": ["pkg update && pkg upgrade", "pkg install python openssh"],
    "configuracion": ["pkg install python openssh", "python --version"],
    "ssh": ["whoami", "passwd", "ifconfig", "ssh usuario@192.168.1.x"],
    "codigo": [
        "from fastapi import FastAPI",
        'app = FastAPI()',
        '@app.get("/")',
        'def home():',
        '    return {"msg": "Hola desde Android!"}',
    ],
    "ejecucion": [
        "uvicorn server:app --host 0.0.0.0 --port 8000",
        "http://192.168.1.x:8000",
    ],
    "cierre": ["# Gracias por ver!", "# Dale like y suscríbete"],
}

SCENE_TITLES = {
    "intro": "Android como Servidor",
    "instalacion": "Paso 1: Instalar Termux",
    "configuracion": "Paso 2: Python + OpenSSH",
    "ssh": "Paso 3: Configurar SSH",
    "codigo": "Paso 4: Escribir el Backend",
    "ejecucion": "Paso 5: Ejecutar y Probar",
    "cierre": "Proximos Pasos",
}


async def generate_audio(text_file, output_audio):
    with open(text_file) as f:
        raw = f.read()
    clean = re.sub(r'^##SECCION:.*\n?', '', raw, flags=re.MULTILINE)
    communicate = edge_tts.Communicate(clean.strip(), VOICE)
    await communicate.save(output_audio)
    print(f"Audio generado: {output_audio}")


def build_scene_clip(scene):
    dur = scene["duration"]
    sid = scene["id"]
    commands = SCENE_COMMANDS.get(sid, ["# ..."])
    title = SCENE_TITLES.get(sid, sid.upper())

    bg = make_background(scene)

    title_clip = TextClip(font=FONT_BOLD, text=title, font_size=44, color="white").with_position((80, 50)).with_duration(dur)

    panel_clips = make_terminal_panel(commands, dur)

    return CompositeVideoClip([bg, title_clip] + panel_clips).with_duration(dur)


def compose_video(audio_path, output_video):
    audio = AudioFileClip(audio_path)
    total_duration = audio.duration
    print(f"Duracion total: {total_duration:.2f}s")

    with open("guion.txt") as f:
        text = f.read()

    scenes = parse_scenes(text)
    assign_durations(scenes, total_duration * 0.9)

    all_clips = []

    for scene in scenes:
        seg = build_scene_clip(scene)
        all_clips.append(seg)

    print(f"Total escenas: {len(all_clips)}")

    final = concatenate_videoclips(all_clips, method="chain")

    final_dur = final.duration
    audio_dur = min(audio.duration, final_dur)
    audio_truncated = audio.subclipped(0, audio_dur)
    final = final.with_audio(audio_truncated)
    print(f"Duracion final: {final_dur:.2f}s")

    print("Renderizando video...")
    final.write_videofile(
        output_video,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        ffmpeg_params=[
            "-movflags", "+faststart",
            "-profile:v", "baseline",
            "-level", "3.0",
            "-pix_fmt", "yuv420p",
        ],
    )
    print(f"Video generado: {output_video}")


def post_process(input_video):
    music_path = os.path.join(ASSETS_DIR, "musica_fondo.mp3")
    output_with_music = os.path.join(OUTPUT_DIR, "video_con_musica.mp4")
    thumbnail_path = os.path.join(OUTPUT_DIR, "thumbnail.png")

    if os.path.exists(music_path):
        print("Post-proceso: añadiendo música de fondo...")
        cmd = [
            FFMPEG_BIN, "-y",
            "-i", input_video,
            "-i", music_path,
            "-filter_complex",
            "[1:a]volume=0.08,afade=t=in:d=3,afade=t=out:st=0:d=5[music];"
            "[0:a][music]amix=inputs=2:duration=first[audio]",
            "-map", "0:v",
            "-map", "[audio]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_with_music,
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"Musica añadida: {output_with_music}")
    else:
        output_with_music = input_video

    dur_cmd = [FFMPEG_BIN, "-i", output_with_music]
    dur_out = subprocess.run(dur_cmd, capture_output=True, text=True)
    dur_line = [l for l in dur_out.stderr.split("\n") if "Duration" in l]
    if dur_line:
        dur_str = dur_line[0].split()[1].strip(",")
        parts = [float(x) for x in dur_str.split(":")]
        mid = (parts[0] * 3600 + parts[1] * 60 + parts[2]) / 2
        thumb_cmd = [FFMPEG_BIN, "-y", "-ss", str(mid), "-i", output_with_music, "-vframes", "1", thumbnail_path]
        subprocess.run(thumb_cmd, check=True, capture_output=True)
        print(f"Thumbnail: {thumbnail_path}")


async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(ASSETS_DIR, exist_ok=True)

    audio_path = os.path.join(OUTPUT_DIR, "narracion.mp3")
    video_path = os.path.join(OUTPUT_DIR, "video_final.mp4")

    print("Generando audio con edge-tts...")
    await generate_audio("guion.txt", audio_path)

    print("Componiendo video con moviepy...")
    compose_video(audio_path, video_path)

    post_process(video_path)
    print("Listo!")


if __name__ == "__main__":
    asyncio.run(main())
