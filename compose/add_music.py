import argparse
import subprocess
import sys
import os

def main():
    parser = argparse.ArgumentParser(description="Add background music to video")
    parser.add_argument("--video", required=True, help="Input video file path")
    parser.add_argument("--music", required=True, help="Input background music file path")
    parser.add_argument("--output", required=True, help="Output video file path")
    args = parser.parse_args()

    if not os.path.exists(args.music):
        sys.stderr.write(f"Music file not found: {args.music}. Exiting.\n")
        sys.exit(1)

    # Check if input video has audio stream using ffprobe
    has_audio = False
    try:
        probe_cmd = ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "csv=p=0", args.video]
        res = subprocess.run(probe_cmd, capture_output=True, text=True)
        if "audio" in res.stdout:
            has_audio = True
    except Exception:
        pass

    sys.stderr.write("Mixing background music...\n")
    if has_audio:
        filter_str = "[1:a]volume=-18dB[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[a]"
    else:
        filter_str = "[1:a]volume=-18dB[a]"

    cmd = [
        "ffmpeg", "-y",
        "-i", args.video,
        "-i", args.music,
        "-filter_complex", filter_str,
        "-map", "0:v:0",
        "-map", "[a]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        args.output
    ]

    try:
        subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
        sys.stderr.write("Background music added successfully.\n")
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error adding background music: {e.stderr.decode()}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
