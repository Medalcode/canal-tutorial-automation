import argparse
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(description="Concatenate video clips with crossfade")
    parser.add_argument("--clips", nargs='+', required=True, help="List of input video clips")
    parser.add_argument("--output", required=True, help="Output video file path")
    args = parser.parse_args()

    if len(args.clips) < 2:
        sys.stderr.write("At least two clips are required for concatenation.\n")
        sys.exit(1)

    sys.stderr.write("Getting durations...\n")
    durations = []
    for clip in args.clips:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", clip]
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            durations.append(float(result.stdout.strip()))
        except Exception as e:
            sys.stderr.write(f"Error getting duration for {clip}: {e}\n")
            sys.exit(1)

    crossfade = 0.5
    filter_str = ""
    inputs = []
    for i in range(len(args.clips)):
        inputs.extend(["-i", args.clips[i]])
        
    offset = 0
    v_labels = []
    
    for i in range(1, len(args.clips)):
        offset += durations[i-1] - crossfade
        in1 = "[0:v]" if i == 1 else f"[v{i-1}]"
        in2 = f"[{i}:v]"
        out = f"[v{i}]"
        filter_str += f"{in1}{in2}xfade=transition=fade:duration={crossfade}:offset={offset}{out};"
        v_labels.append(out)

    final_v = v_labels[-1] if v_labels else "[0:v]"
    
    sys.stderr.write("Concatenating clips with xfade...\n")
    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_str,
        "-map", final_v,
        "-an",
        args.output
    ]

    try:
        subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
        sys.stderr.write("Clips concatenated successfully.\n")
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error concatenating clips: {e.stderr.decode()}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
