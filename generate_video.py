import asyncio
import json
import os
import re
import subprocess
from collections import defaultdict

import edge_tts
from faster_whisper import WhisperModel
import imageio_ffmpeg
from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    VideoClip,
    concatenate_videoclips,
)
from moviepy.video.fx import FadeIn, FadeOut

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
        sid = sections[i].strip()
        stext = sections[i + 1].strip()
        scenes.append({"id": sid, "text": stext, "chars": len(stext)})
    return scenes


def assign_durations(scenes, total_duration):
    total_chars = sum(s["chars"] for s in scenes) or 1
    for s in scenes:
        s["duration"] = max(8.0, (s["chars"] / total_chars) * total_duration)


def scene_image_path(scene_id):
    for ext in (".jpg", ".png"):
        p = os.path.join(ASSETS_DIR, f"scene_{scene_id}{ext}")
        if os.path.exists(p):
            return p
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


def transcribe_audio(audio_path):
    print("Transcribiendo audio con faster-whisper...")
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio_path, language="es", word_timestamps=True)
    print(f"Idioma: {info.language} (prob: {info.language_probability:.2f})")
    words = []
    for seg in segments:
        for w in seg.words:
            words.append({"word": w.word.strip(), "start": w.start, "end": w.end})

    chunks = []
    cur = {"words": [], "text": "", "start": None, "end": None}
    for w in words:
        if not w["word"]:
            continue
        if cur["start"] is None:
            cur["start"] = w["start"]
        cur["words"].append(w["word"])
        cur["text"] += w["word"]
        cur["end"] = w["end"]
        should_break = (
            len(cur["words"]) >= 10
            or (w["end"] - cur["start"]) >= 2.8
            or w["word"].rstrip()[-1:] in (".", "?", "!")
        )
        if should_break:
            chunks.append(dict(cur))
            cur = {"words": [], "text": "", "start": None, "end": None}
    if cur["words"]:
        chunks.append(dict(cur))

    print(f"Subtitulos: {len(chunks)} fragmentos, {len(words)} palabras")
    return chunks


def make_subtitle_clips(subtitle_chunks, width, height):
    clips = []
    panel_top = H - 560
    sub_y = panel_top - 60
    for ch in subtitle_chunks:
        text = ch["text"].strip()
        if not text:
            continue
        start, end = ch["start"], ch["end"]
        dur = end - start
        if dur <= 0:
            continue
        txt = TextClip(
            font=FONT_BOLD,
            text=text,
            font_size=32,
            color="white",
            stroke_color="black",
            stroke_width=2,
            text_align="center",
        ).with_position(("center", sub_y)).with_start(start).with_duration(dur)
        clips.append(txt)
    print(f"Clips de subtitulos: {len(clips)}")
    return clips


def build_scene_clip(scene):
    dur = scene["duration"]
    sid = scene["id"]
    commands = SCENE_COMMANDS.get(sid, ["# ..."])
    title = SCENE_TITLES.get(sid, sid.upper())

    bg = make_background(scene)
    title_clip = TextClip(font=FONT_BOLD, text=title, font_size=44, color="white").with_position((80, 50)).with_duration(dur)
    panel_clips = make_terminal_panel(commands, dur)

    return CompositeVideoClip([bg, title_clip] + panel_clips).with_duration(dur)


def make_intro(duration=6):
    clips = []
    # Background with subtle gradient via layered clips
    bg = ColorClip(size=(W, H), color=BG_COLOR).with_duration(duration)
    clips.append(bg)

    # Accent bar that grows
    bar = (ColorClip(size=(4, 200), color=(0, 200, 0))
           .with_duration(duration)
           .with_position(("center", 160)))
    clips.append(bar)

    # Title typewriter (word by word)
    title_words = ["Android", "como", "Servidor"]
    gap = duration / (len(title_words) + 2)
    for i, word in enumerate(title_words):
        t = (TextClip(font=FONT_BOLD, text=word, font_size=80, color="white")
             .with_position(("center", 220 + i * 90))
             .with_start(0.5 + (i + 1) * gap * 0.3)
             .with_duration(duration))
        clips.append(t)

    # Subtitle fade in
    sub = (TextClip(font=FONT, text="Con Termux + Python + FastAPI", font_size=40, color="#00FF00")
           .with_position(("center", 500))
           .with_start(3.5)
           .with_duration(duration - 3.5)
           .with_effects([FadeIn(0.5)]))
    clips.append(sub)

    # Bottom info line
    info = (TextClip(font=FONT, text="Pipeline automatizado con Python", font_size=22, color=(100, 100, 100))
            .with_position(("center", H - 80))
            .with_start(4.0)
            .with_duration(duration - 4.0)
            .with_effects([FadeIn(0.5)]))
    clips.append(info)

    return CompositeVideoClip(clips).with_duration(duration)


def make_outro(duration=8):
    clips = []
    bg = ColorClip(size=(W, H), color=BG_COLOR).with_duration(duration)
    clips.append(bg)

    thanks = (TextClip(font=FONT_BOLD, text="Gracias por ver", font_size=80, color="white")
              .with_position(("center", 200))
              .with_start(1.0)
              .with_duration(duration - 2)
              .with_effects([FadeIn(0.8)]))
    clips.append(thanks)

    sub = (TextClip(font=FONT, text="Suscribete para mas tutoriales como este", font_size=36, color="#00FF00")
           .with_position(("center", 320))
           .with_start(2.0)
           .with_duration(duration - 2.5)
           .with_effects([FadeIn(0.6)]))
    clips.append(sub)

    btn = (ColorClip(size=(360, 70), color=(200, 0, 0))
           .with_duration(4)
           .with_position(("center", 430))
           .with_start(3.0)
           .with_effects([FadeIn(0.5)]))
    clips.append(btn)

    btn_text = (TextClip(font=FONT_BOLD, text="SUSCRIBIRSE", font_size=36, color="white")
                .with_position(("center", 430))
                .with_start(3.0)
                .with_duration(4)
                .with_effects([FadeIn(0.5)]))
    clips.append(btn_text)

    # Fade out at end
    fade_out = (ColorClip(size=(W, H), color=(0, 0, 0))
                .with_duration(1.5)
                .with_start(duration - 1.5)
                .with_effects([FadeIn(1.5)]))
    clips.append(fade_out)

    return CompositeVideoClip(clips).with_duration(duration)


def compose_video(audio_path, subtitle_chunks, output_video):
    audio = AudioFileClip(audio_path)
    total_duration = audio.duration
    print(f"Duracion audio: {total_duration:.2f}s")

    with open("guion.txt") as f:
        text = f.read()

    scenes = parse_scenes(text)
    assign_durations(scenes, total_duration * 0.9)

    all_clips = []
    for scene in scenes:
        all_clips.append(build_scene_clip(scene))

    intro = make_intro(6)
    outro = make_outro(8)
    all_clips = [intro] + all_clips + [outro]

    print(f"Total clips (intro + {len(all_clips)-2} escenas + outro): {len(all_clips)}")
    final = concatenate_videoclips(all_clips, method="chain")

    final_dur = final.duration
    audio_dur = min(audio.duration, final_dur)
    audio_trunc = audio.subclipped(0, audio_dur)

    scenes_start = 6.0
    scenes_end = scenes_start + audio_dur
    if scenes_end > final_dur:
        scenes_end = final_dur
    audio_shifted = audio_trunc.with_start(scenes_start).with_duration(scenes_end - scenes_start)
    final = final.with_audio(audio_shifted)

    INTRO_DUR = 6.0
    for sc in subtitle_chunks:
        sc["start"] += INTRO_DUR
        sc["end"] += INTRO_DUR
    sub_clips = make_subtitle_clips(subtitle_chunks, W, H)
    final = CompositeVideoClip([final] + sub_clips)

    print(f"Duracion final: {final.duration:.2f}s")
    print("Renderizando video...")
    final.write_videofile(
        output_video,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="fast",
        bitrate="2000k",
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
    temp_music = os.path.join(OUTPUT_DIR, "video_temp_music.mp4")
    output_1080p = os.path.join(OUTPUT_DIR, "video_con_musica.mp4")
    thumb_path = os.path.join(OUTPUT_DIR, "thumbnail.png")

    current = input_video

    if os.path.exists(music_path):
        print("Post-proceso: anadiendo musica de fondo...")
        subprocess.run([
            FFMPEG_BIN, "-y",
            "-i", current,
            "-i", music_path,
            "-filter_complex",
            "[1:a]volume=0.08,afade=t=in:d=3,afade=t=out:st=0:d=5[music];"
            "[0:a][music]amix=inputs=2:duration=first[audio]",
            "-map", "0:v", "-map", "[audio]",
            "-c:v", "copy", "-c:a", "aac", "-shortest",
            temp_music,
        ], check=True, capture_output=True)
        print(f"Musica anadida: {temp_music}")
        current = temp_music

    print("Post-proceso: upscaling a 1080p...")
    subprocess.run([
        FFMPEG_BIN, "-y",
        "-i", current,
        "-vf", "scale=1920:1080:flags=lanczos",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-b:v", "4M",
        "-c:a", "copy",
        "-movflags", "+faststart",
        "-profile:v", "high",
        "-pix_fmt", "yuv420p",
        output_1080p,
    ], check=True, capture_output=True)
    print(f"Video 1080p: {output_1080p}")

    dur_out = subprocess.run([FFMPEG_BIN, "-i", output_1080p], capture_output=True, text=True)
    dur_line = [l for l in dur_out.stderr.split("\n") if "Duration" in l]
    if dur_line:
        parts = [float(x) for x in dur_line[0].split()[1].strip(",").split(":")]
        mid = (parts[0] * 3600 + parts[1] * 60 + parts[2]) / 2
        subprocess.run([FFMPEG_BIN, "-y", "-ss", str(mid), "-i", output_1080p, "-vframes", "1", thumb_path], check=True, capture_output=True)
        print(f"Thumbnail: {thumb_path}")


async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(ASSETS_DIR, exist_ok=True)

    audio_path = os.path.join(OUTPUT_DIR, "narracion.mp3")
    video_path = os.path.join(OUTPUT_DIR, "video_final.mp4")

    print("Generando audio con edge-tts...")
    await generate_audio("guion.txt", audio_path)

    subtitle_chunks = transcribe_audio(audio_path)

    print("Componiendo video con moviepy...")
    compose_video(audio_path, subtitle_chunks, video_path)

    post_process(video_path)
    print("Listo!")


if __name__ == "__main__":
    asyncio.run(main())
