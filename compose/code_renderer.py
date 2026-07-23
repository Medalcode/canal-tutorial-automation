import argparse
import os
import sys
from PIL import Image, ImageDraw, ImageFont
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer

# Default VS Code Dark Theme Palette
COLOR_BG = (30, 30, 30)            # #1e1e1e (IDE background)
COLOR_SIDEBAR = (37, 37, 38)       # #252526
COLOR_TITLEBAR = (50, 50, 50)      # #323232
COLOR_TAB_ACTIVE = (30, 30, 30)     # #1e1e1e
COLOR_TAB_INACTIVE = (45, 45, 45)  # #2d2d2d
COLOR_TEXT_WHITE = (220, 220, 220)
COLOR_TEXT_DIM = (140, 140, 140)
COLOR_LINE_NUM = (100, 100, 100)
COLOR_BORDER = (60, 60, 60)
COLOR_CLOSE = (255, 95, 86)
COLOR_MINIMIZE = (255, 189, 46)
COLOR_MAXIMIZE = (39, 201, 63)

# Pygments token to RGB mapping for dark theme
PYGMENTS_COLORS = {
    'Comment': (106, 153, 85),       # Green #6A9955
    'Keyword': (86, 156, 214),       # Blue #569CD6
    'String': (206, 145, 120),       # Orange/Brown #CE9178
    'Number': (181, 206, 168),       # Light Green #B5CEA8
    'Name.Function': (220, 220, 170),# Yellow #DCDCAA
    'Name.Class': (78, 201, 176),    # Teal #4EC9B0
    'Operator': (214, 214, 214),     # White #D4D4D4
    'Name.Builtin': (86, 156, 214),  # Blue
    'Text': (220, 220, 220),         # Off-white
}

def load_font(size):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"
    ]
    for p in font_paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def render_vscode_ide(code: str, language: str = "python", filename: str = "main.py", width: int = 1152, height: int = 1080) -> Image.Image:
    image = Image.new("RGB", (width, height), COLOR_BG)
    draw = ImageDraw.Draw(image)
    
    font_code = load_font(22)
    font_ui = load_font(18)
    
    # 1. Draw Title Bar (Height: 45px)
    title_height = 45
    draw.rectangle([(0, 0), (width, title_height)], fill=COLOR_TITLEBAR)
    
    # Mac-style Window Controls (Red, Yellow, Green circles)
    draw.ellipse([(15, 15), (27, 27)], fill=COLOR_CLOSE)
    draw.ellipse([(35, 15), (47, 27)], fill=COLOR_MINIMIZE)
    draw.ellipse([(55, 15), (67, 27)], fill=COLOR_MAXIMIZE)
    
    # Title Text
    title_text = f"● {filename} - Visual Studio Code"
    draw.text((width // 2 - 140, 12), title_text, fill=COLOR_TEXT_DIM, font=font_ui)
    
    # 2. Draw Tab Bar (Height: 40px)
    tab_height = 40
    tab_y = title_height
    draw.rectangle([(0, tab_y), (width, tab_y + tab_height)], fill=COLOR_TAB_INACTIVE)
    
    # Active Tab
    tab_width = 180
    draw.rectangle([(0, tab_y), (tab_width, tab_y + tab_height)], fill=COLOR_TAB_ACTIVE)
    draw.rectangle([(0, tab_y), (tab_width, tab_y + 2)], fill=(0, 122, 204)) # Blue indicator bar
    draw.text((20, tab_y + 10), filename, fill=COLOR_TEXT_WHITE, font=font_ui)
    
    # 3. Draw Left Activity / File Tree Sidebar (Width: 60px)
    sidebar_width = 60
    content_y = tab_y + tab_height
    draw.rectangle([(0, content_y), (sidebar_width, height)], fill=COLOR_SIDEBAR)
    draw.line([(sidebar_width, content_y), (sidebar_width, height)], fill=COLOR_BORDER, width=1)
    
    # 4. Draw Line Numbers Column
    gutter_x = sidebar_width + 10
    code_start_x = sidebar_width + 70
    line_y = content_y + 25
    line_height = 34
    
    lines = code.strip().split('\n')
    
    try:
        lexer = get_lexer_by_name(language)
    except Exception:
        lexer = guess_lexer(code)
        
    tokens = list(lexer.get_tokens(code))
    
    # Render line numbers
    for idx in range(len(lines)):
        curr_y = line_y + (idx * line_height)
        if curr_y + line_height > height - 30:
            break
        num_str = f"{idx + 1:>3}"
        draw.text((gutter_x, curr_y), num_str, fill=COLOR_LINE_NUM, font=font_code)
        
    # Render Tokens
    current_line = 0
    cursor_x = code_start_x
    cursor_y = line_y
    
    for token_type, value in tokens:
        # Determine token color
        t_type_str = str(token_type)
        token_color = COLOR_TEXT_WHITE
        for k, col in PYGMENTS_COLORS.items():
            if k in t_type_str:
                token_color = col
                break
                
        lines_in_val = value.split('\n')
        for i, val_part in enumerate(lines_in_val):
            if i > 0:
                current_line += 1
                cursor_x = code_start_x
                cursor_y = line_y + (current_line * line_height)
                
            if cursor_y + line_height > height - 30:
                break
                
            if val_part:
                draw.text((cursor_x, cursor_y), val_part, fill=token_color, font=font_code)
                # Calculate offset for next token
                bbox = font_code.getbbox(val_part)
                token_w = bbox[2] - bbox[0]
                cursor_x += token_w

    # 5. Draw Bottom Status Bar (Height: 25px)
    status_y = height - 25
    draw.rectangle([(0, status_y), (width, height)], fill=(0, 122, 204)) # VS Code Blue Status Bar
    draw.text((15, status_y + 4), "  UTF-8   Python 3.11   n8n-Automation  ", fill=(255, 255, 255), font=font_ui)
    
    return image

def main():
    parser = argparse.ArgumentParser(description="Render code to VS Code IDE image")
    parser.add_argument("--code", type=str, help="Code string to render")
    parser.add_argument("--code-file", type=str, help="File containing code to render")
    parser.add_argument("--output", required=True, help="Output PNG image path")
    parser.add_argument("--language", default="python", help="Programming language")
    parser.add_argument("--filename", default="script.py", help="Tab filename")
    parser.add_argument("--width", type=int, default=1152, help="Image width")
    parser.add_argument("--height", type=int, default=1080, help="Image height")
    args = parser.parse_args()

    code_text = args.code
    if args.code_file and os.path.exists(args.code_file):
        with open(args.code_file, "r", encoding="utf-8") as f:
            code_text = f.read()

    if not code_text:
        code_text = "# Sample Code Tutorial\ndef hello_world():\n    print('Hello from n8n & LTX Video!')\n\nhello_world()"

    img = render_vscode_ide(code_text, language=args.language, filename=args.filename, width=args.width, height=args.height)
    img.save(args.output)
    print(f"Rendered IDE code image to {args.output}")

if __name__ == "__main__":
    main()
