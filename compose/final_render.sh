#!/bin/bash
# final_render.sh

INPUT_DIR=""
OUTPUT=""

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --input-dir) INPUT_DIR="$2"; shift ;;
        --output) OUTPUT="$2"; shift ;;
        *) echo "Usage: $0 --input-dir <dir> --output <file>"; exit 1 ;;
    esac
    shift
done

if [ -z "$INPUT_DIR" ] || [ -z "$OUTPUT" ]; then
    echo "Usage: $0 --input-dir <dir> --output <file>"
    exit 1
fi

COMPOSE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEXT_FILE="$INPUT_DIR/narration.txt"
MUSIC_FILE="$INPUT_DIR/bg_music.mp3"
TEMP_NARRATION="$INPUT_DIR/temp_narration.mp3"
TEMP_CONCAT="$INPUT_DIR/temp_concat.mp4"
TEMP_SUBS="$INPUT_DIR/temp_subs.mp4"
TEMP_MUX="$INPUT_DIR/temp_mux.mp4"

CLIPS=($(ls "$INPUT_DIR"/*.mp4 2>/dev/null | grep -v temp_ | grep -v "$(basename "$OUTPUT")"))

if [ ${#CLIPS[@]} -eq 0 ]; then
    echo "No clips found in $INPUT_DIR"
    exit 1
fi

echo "1. Concatenating clips..."
python3 "$COMPOSE_DIR/concat_clips.py" --clips "${CLIPS[@]}" --output "$TEMP_CONCAT"

if [ -f "$TEXT_FILE" ]; then
    echo "2. Adding narration..."
    NARRATION_TEXT=$(cat "$TEXT_FILE")
    python3 "$COMPOSE_DIR/add_narration.py" --text "$NARRATION_TEXT" --output "$TEMP_NARRATION"
    
    echo "3. Adding subtitles..."
    python3 "$COMPOSE_DIR/add_subtitles.py" --video "$TEMP_CONCAT" --audio "$TEMP_NARRATION" --output "$TEMP_SUBS"
else
    echo "No narration.txt found, skipping narration and subtitles."
    cp "$TEMP_CONCAT" "$TEMP_SUBS"
fi

if [ -f "$MUSIC_FILE" ]; then
    echo "4. Adding music..."
    python3 "$COMPOSE_DIR/add_music.py" --video "$TEMP_SUBS" --music "$MUSIC_FILE" --output "$TEMP_MUX"
else
    echo "No background music found."
    cp "$TEMP_SUBS" "$TEMP_MUX"
fi

echo "5. Final render (1080p 5Mbps)..."
ffmpeg -y -i "$TEMP_MUX" -c:v libx264 -preset medium -b:v 5M -vf scale=1920:1080 -c:a aac "$OUTPUT"

echo "Done! Saved to $OUTPUT"
