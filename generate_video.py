import argparse
import asyncio
import json
import os
import re
import subprocess
import shutil
from collections import defaultdict
from pathlib import Path

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
    VideoFileClip,
    concatenate_videoclips,
)
from moviepy.video.fx import FadeIn, FadeOut
import ide_simulator

FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()

VOICE = "es-MX-DaliaNeural"
OUTPUT_DIR = "output"
ASSETS_DIR = "assets"
W, H = 1920, 1080
BG_COLOR = (20, 22, 28)

def get_font_path(font_name):
    # Intentar cargar desde assets locales primero
    local_path = os.path.join(ASSETS_DIR, "fonts", font_name)
    if os.path.exists(local_path):
        return local_path
    
    # Fallback a las fuentes del sistema
    linux_paths = [
        f"/usr/share/fonts/truetype/dejavu/{font_name}",
        f"/usr/share/fonts/dejavu/{font_name}",
        f"/usr/share/fonts/TTF/{font_name}"
    ]
    for p in linux_paths:
        if os.path.exists(p):
            return p
    return "Arial" # Fallback generico de MoviePy

FONT_MONO = get_font_path("DejaVuSansMono.ttf")
FONT = get_font_path("DejaVuSans.ttf")
FONT_BOLD = get_font_path("DejaVuSans-Bold.ttf")

def load_script(json_path: str):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    scenes = data.get("scenes", [])
    for s in scenes:
        s["text"] = s.get("narration", "")
        s["chars"] = len(s["text"])
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


async def generate_audio(scenes, output_audio):
    full_text = " ".join([s.get("narration", "") for s in scenes])
    communicate = edge_tts.Communicate(full_text.strip(), VOICE)
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
    commands = scene.get("commands", [])
    manim_code = scene.get("manim_code", "")
    title = scene.get("title", sid.upper())
    language = scene.get("language", "python")

    # 1. Intentar renderizar con Manim si está disponible
    manim_mp4 = None
    if manim_code and "class SceneAnim" in manim_code:
        # Ajustamos el path de salida esperado
        py_file = os.path.join(OUTPUT_DIR, f"manim_{sid}.py")
        with open(py_file, "w", encoding="utf-8") as f:
            f.write(manim_code)
        
        # Manim por defecto guardará en media/videos/manim_{sid}/1080p60/SceneAnim.mp4
        # Forzamos media_dir a OUTPUT_DIR
        cmd = [
            os.path.join(os.environ.get("HOME", ""), ".canal-tutorial-venv", "bin", "manim"),
            py_file, "SceneAnim", "-qh", "--media_dir", os.path.abspath(OUTPUT_DIR)
        ]
        try:
            print(f"[{sid}] Compilando animacion Manim...")
            subprocess.run(cmd, check=True, capture_output=True)
            expected_mp4 = os.path.join(os.path.abspath(OUTPUT_DIR), "videos", f"manim_{sid}", "1080p60", "SceneAnim.mp4")
            if os.path.exists(expected_mp4):
                manim_mp4 = expected_mp4
        except Exception as e:
            print(f"[{sid}] Error en Manim. Usando fallback.")
            if hasattr(e, 'stderr') and e.stderr:
                print(e.stderr.decode(errors="ignore"))

    if manim_mp4:
        print(f"[{sid}] Usando clip Manim: {manim_mp4}")
        clip = VideoFileClip(manim_mp4).resized((W, H))
        if clip.duration < dur:
            # Congelar el último frame
            last_frame = clip.get_frame(clip.duration - 0.1)
            frozen = ImageClip(last_frame).with_duration(dur - clip.duration)
            clip = concatenate_videoclips([clip, frozen])
        return clip.with_duration(dur)

    # 2. Fallback: Determinar si hay código real para mostrar en el IDE
    code_keywords = {"def ", "class ", "import ", "for ", "while ", "if ", "==", "->", ":"}
    code_lines = []
    for cmd in commands:
        if any(kw in cmd for kw in code_keywords) or "\n" in cmd or len(cmd) > 40:
            code_lines.append(cmd)

    if code_lines:
        code_text = "\n".join(code_lines)
        total_chars = len(code_text)
        typing_duration = max(dur * 0.85, 3.0)
        cps = total_chars / max(typing_duration, 1)
        cps = max(8.0, min(cps, 35.0))

        ext_map = {"python": ".py", "bash": ".sh", "javascript": ".js",
                   "typescript": ".ts", "rust": ".rs", "go": ".go"}
        ext = ext_map.get(language, ".py")
        filename = f"{sid.replace('-', '_')}{ext}"

        ide_clip = ide_simulator.generate_ide_clip(
            code=code_text,
            duration=dur,
            filename=filename,
            language=language,
            chars_per_second=cps,
        ).resized((W, H))

        title_clip = (
            TextClip(font=FONT_BOLD, text=title, font_size=36, color="white",
                     stroke_color="black", stroke_width=2)
            .with_position((80, 60))
            .with_duration(dur)
        )
        return CompositeVideoClip([ide_clip, title_clip]).with_duration(dur)

    else:
        bg = make_background(scene)
        title_clip = (
            TextClip(font=FONT_BOLD, text=title, font_size=44, color="white")
            .with_position((80, 50))
            .with_duration(dur)
        )
        panel_clips = make_terminal_panel(commands, dur)
        return CompositeVideoClip([bg, title_clip] + panel_clips).with_duration(dur)


def make_intro(duration=6):
    clips = []
    bg = ColorClip(size=(W, H), color=BG_COLOR).with_duration(duration)
    clips.append(bg)

    bar = (ColorClip(size=(4, 200), color=(0, 200, 0))
           .with_duration(duration)
           .with_position(("center", 160)))
    clips.append(bar)

    title_words = ["Tutorial", "Generado", "por IA"]
    gap = duration / (len(title_words) + 2)
    for i, word in enumerate(title_words):
        t = (TextClip(font=FONT_BOLD, text=word, font_size=80, color="white")
             .with_position(("center", 220 + i * 90))
             .with_start(0.5 + (i + 1) * gap * 0.3)
             .with_duration(duration))
        clips.append(t)

    sub = (TextClip(font=FONT, text="Automatizado con Python", font_size=40, color="#00FF00")
           .with_position(("center", 500))
           .with_start(3.5)
           .with_duration(duration - 3.5)
           .with_effects([FadeIn(0.5)]))
    clips.append(sub)

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

    sub = (TextClip(font=FONT, text="Suscribete para mas tutoriales", font_size=36, color="#00FF00")
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

    fade_out = (ColorClip(size=(W, H), color=(0, 0, 0))
                .with_duration(1.5)
                .with_start(duration - 1.5)
                .with_effects([FadeIn(1.5)]))
    clips.append(fade_out)

    return CompositeVideoClip(clips).with_duration(duration)


def compose_video(audio_path, subtitle_chunks, scenes, output_video):
    audio = AudioFileClip(audio_path)
    total_duration = audio.duration
    print(f"Duracion audio: {total_duration:.2f}s")

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

    print(f"Duracion final de render raw: {final.duration:.2f}s")
    print("Renderizando video temporal...")
    # Generamos el video crudo que luego pasará por post-proceso
    final.write_videofile(
        output_video,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",  # rápido aquí, lo optimizaremos en post-proceso
        bitrate="5000k"
    )
    print(f"Video temporal renderizado: {output_video}")


def download_fallback_music(music_path):
    import urllib.request
    url = "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Sunshine.mp3"
    try:
        print("Descargando musica de fondo libre de derechos...")
        os.makedirs(os.path.dirname(music_path), exist_ok=True)
        urllib.request.urlretrieve(url, music_path)
        print(f"Musica descargada: {music_path}")
        return True
    except Exception as e:
        print(f"No se pudo descargar musica: {e}. Se continuara sin musica.")
        return False


def post_process(input_video, final_output, thumb_path):
    music_path = os.path.join(ASSETS_DIR, "musica_fondo.mp3")

    if not os.path.exists(music_path):
        download_fallback_music(music_path)

    has_music = os.path.exists(music_path)
    print("Post-proceso: upscaling a 1080p, calidad lenta y añadiendo música si aplica...")
    
    cmd = [
        FFMPEG_BIN, "-y",
        "-i", input_video
    ]
    
    if has_music:
        cmd.extend(["-i", music_path])
        cmd.extend([
            "-filter_complex",
            # Escalado de video
            "[0:v]scale=1920:1080:flags=lanczos:force_original_aspect_ratio=decrease[vout];"
            # Mezcla de audio
            "[1:a]volume=0.06,afade=t=in:d=3,afade=t=out:st=0:d=5[music];"
            "[0:a][music]amix=inputs=2:duration=first[aout]",
            "-map", "[vout]", "-map", "[aout]"
        ])
    else:
        cmd.extend([
            "-vf", "scale=1920:1080:flags=lanczos:force_original_aspect_ratio=decrease",
            "-map", "0:v", "-map", "0:a"
        ])
        
    cmd.extend([
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "16",
        "-b:v", "5M",
        "-maxrate", "6M",
        "-bufsize", "10M",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        "-profile:v", "high",
        "-level", "4.2",
        "-pix_fmt", "yuv420p",
        final_output
    ])

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"Video final procesado: {final_output}")
    except subprocess.CalledProcessError as e:
        print(f"Error en post_process ffmpeg: {e.stderr.decode()}")
        raise e

    # Extraer miniatura
    dur_out = subprocess.run([FFMPEG_BIN, "-i", final_output], capture_output=True, text=True)
    dur_line = [l for l in dur_out.stderr.split("\n") if "Duration" in l]
    if dur_line:
        try:
            time_str = dur_line[0].split()[1].strip(",")
            h, m, s = map(float, time_str.split(":"))
            mid = (h * 3600 + m * 60 + s) / 2
            subprocess.run([FFMPEG_BIN, "-y", "-ss", str(mid), "-i", final_output, "-vframes", "1", thumb_path], check=True, capture_output=True)
            print(f"Thumbnail: {thumb_path}")
        except Exception as e:
            print(f"No se pudo generar thumbnail: {e}")

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", required=True, help="Ruta al archivo script.json")
    parser.add_argument("--job-id", required=True, help="ID único para este trabajo")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(ASSETS_DIR, exist_ok=True)

    if not os.path.exists(args.script):
        print(f"ERROR: No se encontró el script {args.script}")
        return

    scenes = load_script(args.script)

    audio_path = os.path.join(OUTPUT_DIR, f"narracion_{args.job_id}.mp3")
    temp_video_path = os.path.join(OUTPUT_DIR, f"temp_video_{args.job_id}.mp4")
    final_video_path = os.path.join(OUTPUT_DIR, f"video_con_musica_{args.job_id}.mp4")
    thumb_path = os.path.join(OUTPUT_DIR, f"thumbnail_{args.job_id}.png")

    print("Generando audio con edge-tts...")
    await generate_audio(scenes, audio_path)

    subtitle_chunks = transcribe_audio(audio_path)

    print("Componiendo video con MoviePy...")
    compose_video(audio_path, subtitle_chunks, scenes, temp_video_path)

    post_process(temp_video_path, final_video_path, thumb_path)
    
    # Limpiar archivos temporales
    try:
        os.remove(audio_path)
        os.remove(temp_video_path)
    except Exception as e:
        print(f"Aviso al limpiar temporales: {e}")
        
    print("Listo!")

if __name__ == "__main__":
    asyncio.run(main())
