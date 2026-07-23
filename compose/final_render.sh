#!/bin/bash
# final_render.sh - 40/60 Split-Screen Ghibli AI Avatar + Code Editor Tutorial Generator

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
PROJECT_ROOT="$(cd "$COMPOSE_DIR/.." && pwd)"

TEXT_FILE="$INPUT_DIR/narration.txt"
CODE_FILE="$INPUT_DIR/code.py"
MUSIC_FILE="$INPUT_DIR/bg_music.mp3"
if [ ! -f "$MUSIC_FILE" ] && [ -f "$PROJECT_ROOT/assets/musica_fondo.mp3" ]; then
    MUSIC_FILE="$PROJECT_ROOT/assets/musica_fondo.mp3"
fi

TEMP_NARRATION="$INPUT_DIR/temp_narration.mp3"
TEMP_CODE_PNG="$INPUT_DIR/temp_code_ide.png"
TEMP_CONCAT="$INPUT_DIR/temp_concat.mp4"
TEMP_SPLIT="$INPUT_DIR/temp_split.mp4"
TEMP_SUBS="$INPUT_DIR/temp_subs.mp4"
TEMP_MUX="$INPUT_DIR/temp_mux.mp4"

# 1. Prepare Code IDE Image (60% right: 1152x1080)
echo "1. Rendering Code IDE panel (1152x1080)..."
if [ -f "$CODE_FILE" ]; then
    python3 "$COMPOSE_DIR/code_renderer.py" --code-file "$CODE_FILE" --output "$TEMP_CODE_PNG" --width 1152 --height 1080
elif [ -f "$INPUT_DIR/code.txt" ]; then
    python3 "$COMPOSE_DIR/code_renderer.py" --code-file "$INPUT_DIR/code.txt" --output "$TEMP_CODE_PNG" --width 1152 --height 1080
else
    python3 "$COMPOSE_DIR/code_renderer.py" --code "# Tutorial Automation\nimport os\n\ndef run_pipeline():\n    print('Executing 40/60 AI tutorial...')" --output "$TEMP_CODE_PNG" --width 1152 --height 1080
fi

# 2. Prepare Avatar Input (40% left: 768x1080)
AVATAR_INPUT=""
CLIPS=($(ls "$INPUT_DIR"/*.mp4 2>/dev/null | grep -v temp_ | grep -v "$(basename "$OUTPUT")"))

if [ ${#CLIPS[@]} -gt 0 ]; then
    echo "Using generated AI video clips for avatar..."
    python3 "$COMPOSE_DIR/concat_clips.py" --clips "${CLIPS[@]}" --output "$TEMP_CONCAT"
    AVATAR_INPUT="$TEMP_CONCAT"
elif [ -f "$INPUT_DIR/avatar.jpg" ] || [ -f "$INPUT_DIR/avatar.png" ]; then
    AVATAR_INPUT="$(ls "$INPUT_DIR"/avatar.* 2>/dev/null | head -n 1)"
elif [ -f "$PROJECT_ROOT/assets/ghibli_programmer.png" ]; then
    AVATAR_INPUT="$PROJECT_ROOT/assets/ghibli_programmer.png"
fi

echo "Avatar source: $AVATAR_INPUT"

# 3. Generate Narration Audio
if [ -f "$TEXT_FILE" ]; then
    echo "3. Generating TTS Narration..."
    NARRATION_TEXT=$(cat "$TEXT_FILE")
    python3 "$COMPOSE_DIR/add_narration.py" --text "$NARRATION_TEXT" --output "$TEMP_NARRATION"
fi

# 4. Perform 40/60 Split-Screen Composite with FFmpeg
echo "4. Compositing 40/60 Split-Screen (Left: 768x1080 Avatar, Right: 1152x1080 Code IDE)..."

if [ -f "$TEMP_NARRATION" ]; then
    # Use narration audio duration
    ffmpeg -y -loop 1 -i "$AVATAR_INPUT" -loop 1 -i "$TEMP_CODE_PNG" -i "$TEMP_NARRATION" \
        -filter_complex "[0:v]scale=768:1080:force_original_aspect_ratio=increase,crop=768:1080[left]; [1:v]scale=1152:1080[right]; [left][right]hstack=inputs=2[v]" \
        -map "[v]" -map 2:a -c:v libx264 -preset medium -b:v 5M -c:a aac -shortest "$TEMP_SPLIT"
else
    # Default 10 sec video if no audio
    ffmpeg -y -loop 1 -i "$AVATAR_INPUT" -loop 1 -i "$TEMP_CODE_PNG" -t 10 \
        -filter_complex "[0:v]scale=768:1080:force_original_aspect_ratio=increase,crop=768:1080[left]; [1:v]scale=1152:1080[right]; [left][right]hstack=inputs=2[v]" \
        -map "[v]" -c:v libx264 -preset medium -b:v 5M "$TEMP_SPLIT"
fi

# 5. Subtitles & Music
if [ -f "$TEMP_NARRATION" ]; then
    echo "5. Adding subtitles..."
    python3 "$COMPOSE_DIR/add_subtitles.py" --video "$TEMP_SPLIT" --audio "$TEMP_NARRATION" --output "$TEMP_SUBS"
else
    cp "$TEMP_SPLIT" "$TEMP_SUBS"
fi

if [ -f "$MUSIC_FILE" ]; then
    echo "6. Adding background music..."
    python3 "$COMPOSE_DIR/add_music.py" --video "$TEMP_SUBS" --music "$MUSIC_FILE" --output "$TEMP_MUX"
else
    cp "$TEMP_SUBS" "$TEMP_MUX"
fi

cp "$TEMP_MUX" "$OUTPUT"
echo "Done! 40/60 Split-Screen video saved to $OUTPUT"
