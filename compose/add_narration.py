import argparse
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(description="Add narration using edge-tts")
    parser.add_argument("--text", required=True, help="Narration text")
    parser.add_argument("--output", required=True, help="Output MP3 file path")
    args = parser.parse_args()

    voice = "es-MX-DaliaNeural"
    cmd = ["edge-tts", "--voice", voice, "--text", args.text, "--write-media", args.output]
    
    try:
        sys.stderr.write(f"Generating narration to {args.output}...\n")
        subprocess.run(cmd, check=True)
        sys.stderr.write("Narration generated successfully.\n")
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error generating narration: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
