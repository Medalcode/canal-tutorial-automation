import argparse
import subprocess
import sys
import os
from faster_whisper import WhisperModel

def main():
    parser = argparse.ArgumentParser(description="Transcribe audio and burn subtitles into video")
    parser.add_argument("--video", required=True, help="Input video file path")
    parser.add_argument("--audio", required=True, help="Input audio file path")
    parser.add_argument("--output", required=True, help="Output video file path")
    args = parser.parse_args()

    sys.stderr.write("Transcribing audio with faster-whisper (base model)...\n")
    model_size = "base"
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    segments, info = model.transcribe(args.audio, beam_size=5)

    srt_path = "temp_subtitles.srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, segment in enumerate(segments, start=1):
            start = format_timestamp(segment.start)
            end = format_timestamp(segment.end)
            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{segment.text.strip()}\n\n")

    sys.stderr.write("Burning subtitles into video...\n")
    escaped_srt = srt_path.replace("\\", "/").replace(":", "\\:")
    cmd = [
        "ffmpeg", "-y",
        "-i", args.video,
        "-i", args.audio,
        "-vf", f"subtitles={escaped_srt}",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        args.output
    ]

    try:
        subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
        sys.stderr.write("Subtitles burned successfully.\n")
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error burning subtitles: {e.stderr.decode()}\n")
        sys.exit(1)
    finally:
        if os.path.exists(srt_path):
            os.remove(srt_path)

def format_timestamp(seconds: float):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

if __name__ == "__main__":
    main()
