import asyncio
import os
import edge_tts
from moviepy import (
    AudioFileClip,
    ImageClip,
    TextClip,
    CompositeVideoClip,
)

VOICE = "es-MX-DaliaNeural"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
OUTPUT_DIR = "output"
ASSETS_DIR = "assets"


async def generate_audio(text_file: str, output_audio: str):
    with open(text_file, "r") as f:
        text = f.read()
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_audio)
    print(f"Audio generado: {output_audio}")


def get_audio_duration(audio_path: str) -> float:
    audio = AudioFileClip(audio_path)
    dur = audio.duration
    audio.close()
    return dur


def make_code_overlays(duration: float):
    commands = [
        "pkg update && pkg upgrade",
        "pkg install python openssh",
        "ssh usuario@192.168.1.x",
        'echo "Hola desde Android"',
    ]
    clips = []
    seg_duration = duration / len(commands)
    for i, cmd in enumerate(commands):
        txt = TextClip(
            font=FONT,
            text=f"$ {cmd}",
            font_size=48,
            color="white",
            stroke_color="black",
            stroke_width=3,
        ).with_position(("center", 200)).with_duration(seg_duration).with_start(i * seg_duration)
        clips.append(txt)
    return clips


def compose_video(audio_path: str, background_img: str, output_video: str):
    audio = AudioFileClip(audio_path)
    duration = audio.duration
    print(f"Duracion del audio: {duration:.2f} segundos")

    bg = (
        ImageClip(background_img)
        .resized((1920, 1080))
        .with_duration(duration)
    )

    title = (
        TextClip(
            font=FONT,
            text="Android como Servidor",
            font_size=72,
            color="white",
            stroke_color="black",
            stroke_width=3,
        )
        .with_position(("center", "center"))
        .with_duration(5)
        .with_start(0)
    )

    subtitle = (
        TextClip(
            font=FONT,
            text="Con Termux + Python + FastAPI",
            font_size=36,
            color="#00FF00",
            stroke_color="black",
            stroke_width=2,
        )
        .with_position(("center", 500))
        .with_duration(5)
        .with_start(0)
    )

    overlays = make_code_overlays(duration)

    all_clips = [bg, title, subtitle] + overlays
    video = CompositeVideoClip(all_clips).with_audio(audio)

    print("Renderizando video...")
    video.write_videofile(
        output_video,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        ffmpeg_params=[
            "-movflags", "+faststart",
            "-profile:v", "baseline",
            "-level", "3.0",
            "-pix_fmt", "yuv420p",
        ],
    )
    print(f"Video generado: {output_video}")


async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(ASSETS_DIR, exist_ok=True)

    guion_path = "guion.txt"
    audio_path = os.path.join(OUTPUT_DIR, "narracion.mp3")
    bg_path = os.path.join(ASSETS_DIR, "fondo.jpg")
    video_path = os.path.join(OUTPUT_DIR, "video_final.mp4")

    if not os.path.exists(guion_path):
        print(f"Error: no se encuentra {guion_path}")
        return
    if not os.path.exists(bg_path):
        print(f"Error: no se encuentra {bg_path}. Coloca una imagen de fondo en assets/fondo.jpg")
        return

    print("Generando audio con edge-tts...")
    await generate_audio(guion_path, audio_path)

    print("Componiendo video con moviepy...")
    compose_video(audio_path, bg_path, video_path)

    print("Listo!")


if __name__ == "__main__":
    asyncio.run(main())
