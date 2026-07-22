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

    sys.stderr.write("Mixing background music...\n")
    cmd = [
        "ffmpeg", "-y",
        "-i", args.video,
        "-i", args.music,
        "-filter_complex", "[1:a]volume=-18dB[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[a]",
        "-map", "0:v:0",
        "-map", "[a]",
        "-c:v", "copy",
        "-c:a", "aac",
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
