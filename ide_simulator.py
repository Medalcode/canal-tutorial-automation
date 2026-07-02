"""
ide_simulator.py
Genera clips de video que simulan un editor de código (estilo VS Code Dark+)
con código que se escribe letra por letra, cursor parpadeante y resaltado de sintaxis.
"""

import os
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoClip, ImageClip
import numpy as np

# ── Dimensiones por defecto ───────────────────────────────────────────────────
DEFAULT_WIDTH  = 1920
DEFAULT_HEIGHT = 1080

# ── Paleta VS Code Dark+ ─────────────────────────────────────────────────────
BG         = (30,  30,  30)
TITLE_BG   = (37,  37,  38)
TAB_BG     = (45,  45,  45)
GUTTER_FG  = (81,  81,  81)
CURSOR_COL = (220, 220, 220)

SYNTAX = {
    "keyword": (86,  156, 214),
    "builtin": (220, 220, 170),
    "string":  (206, 145, 120),
    "comment": (106, 153,  85),
    "number":  (181, 206, 168),
    "default": (212, 212, 212),
}

FONT_SIZE   = 22
LINE_HEIGHT = 32
GUTTER_W    = 60
PADDING_L   = 20
TAB_HEIGHT  = 35
FPS         = 30
CHAR_W      = 13


def _load_font(size):
    for path in [
        "assets/fonts/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
        "/usr/share/fonts/dejavu/DejaVuSansMono.ttf",
    ]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _tokenize(line: str, language: str = "python"):
    if language != "python":
        return [(line, SYNTAX["default"])]

    KW = {"def","class","import","from","return","if","else","elif",
          "for","while","try","except","finally","with","as","in",
          "not","and","or","is","None","True","False","pass","break",
          "continue","raise","yield","lambda","global","nonlocal","del",
          "async","await"}
    BT = {"print","len","range","type","list","dict","set","tuple",
          "int","str","float","bool","input","open","enumerate","zip",
          "map","filter","sorted","reversed","isinstance","hasattr",
          "getattr","setattr","super","self"}

    if line.lstrip().startswith("#"):
        return [(line, SYNTAX["comment"])]

    tokens, i = [], 0
    while i < len(line):
        if line[i:i+3] in ('"""', "'''"):
            q = line[i:i+3]
            end = line.find(q, i + 3)
            end = (end + 3) if end != -1 else len(line)
            tokens.append((line[i:end], SYNTAX["string"]))
            i = end
        elif line[i] in ('"', "'"):
            q, j = line[i], i + 1
            while j < len(line) and line[j] != q:
                if line[j] == "\\": j += 1
                j += 1
            tokens.append((line[i:j+1], SYNTAX["string"]))
            i = j + 1
        elif line[i] == "#":
            tokens.append((line[i:], SYNTAX["comment"]))
            break
        elif line[i].isalpha() or line[i] == "_":
            j = i
            while j < len(line) and (line[j].isalnum() or line[j] == "_"):
                j += 1
            w = line[i:j]
            color = SYNTAX["keyword"] if w in KW else \
                    SYNTAX["builtin"] if w in BT else \
                    SYNTAX["default"]
            tokens.append((w, color))
            i = j
        elif line[i].isdigit():
            j = i
            while j < len(line) and (line[j].isdigit() or line[j] == "."):
                j += 1
            tokens.append((line[i:j], SYNTAX["number"]))
            i = j
        else:
            tokens.append((line[i], SYNTAX["default"]))
            i += 1
    return tokens


def _render_frame(lines, cur_line, cur_col, blink, filename, language, font,
                  width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
    img  = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, width, 22], fill=TITLE_BG)
    draw.text((width // 2 - 100, 3), f"\u25cf {filename} \u2014 Video Generator Pro",
              fill=(200, 200, 200), font=font)

    draw.rectangle([0, 22, width, 22 + TAB_HEIGHT], fill=TITLE_BG)
    draw.rectangle([0, 22, 190, 22 + TAB_HEIGHT], fill=TAB_BG)
    draw.text((14, 30), f"  {filename}", fill=(200, 200, 200), font=font)
    draw.rectangle([0, 22 + TAB_HEIGHT - 2, 190, 22 + TAB_HEIGHT], fill=(0, 122, 204))

    y0 = 22 + TAB_HEIGHT + 8
    for idx, line in enumerate(lines):
        y = y0 + idx * LINE_HEIGHT
        if y > height - LINE_HEIGHT:
            break

        if idx == cur_line:
            draw.rectangle([GUTTER_W, y - 2, width, y + LINE_HEIGHT - 2], fill=(40, 40, 40))

        draw.text((10, y), str(idx + 1).rjust(3), fill=GUTTER_FG, font=font)

        x = GUTTER_W + PADDING_L
        for tok, color in _tokenize(line, language):
            draw.text((x, y), tok, fill=color, font=font)
            x += len(tok) * CHAR_W

        if idx == cur_line and blink:
            cx = GUTTER_W + PADDING_L + cur_col * CHAR_W
            draw.rectangle([cx, y, cx + 2, y + FONT_SIZE], fill=CURSOR_COL)

    draw.rectangle([0, height - 24, width, height], fill=(0, 122, 204))
    draw.text((10, height - 20),
              f"  {language.upper()}   Ln {cur_line+1}, Col {cur_col+1}",
              fill="white", font=font)

    return np.array(img)


def generate_ide_clip(
    code: str,
    duration: float = 10.0,
    filename: str = "main.py",
    language: str = "python",
    chars_per_second: float = 18.0,
    width=DEFAULT_WIDTH,
    height=DEFAULT_HEIGHT,
):
    font = _load_font(FONT_SIZE)
    total = len(code)

    def make_frame(t):
        expected = min(int(t * chars_per_second), total)
        typed = code[:expected]

        lines = typed.split("\n")
        cur_line = len(lines) - 1
        cur_col = len(lines[-1])
        blink = int(t * 2) % 2 == 0

        return _render_frame(lines, cur_line, cur_col, blink, filename, language, font,
                             width=width, height=height)

    if total == 0:
        blank = _render_frame([], 0, 0, False, filename, language, font,
                              width=width, height=height)
        return ImageClip(blank, duration=duration)

    clip = VideoClip(make_frame, duration=duration)
    clip.fps = FPS
    return clip


# ── Prueba independiente ──────────────────────────────────────────────────────
if __name__ == "__main__":
    sample = '''import os
from pathlib import Path

def load_documents(folder: str) -> list:
    """Carga todos los archivos .txt de la carpeta."""
    docs = []
    for file in Path(folder).glob("*.txt"):
        with open(file, "r", encoding="utf-8") as f:
            docs.append(f.read())
    return docs

def build_rag_index(documents: list) -> dict:
    """Construye un índice de búsqueda RAG simple."""
    index = {}
    for i, doc in enumerate(documents):
        for word in doc.split():
            index.setdefault(word.lower(), []).append(i)
    return index

if __name__ == "__main__":
    docs  = load_documents("data/")
    index = build_rag_index(docs)
    print(f"\u2705 {len(docs)} documentos indexados")
    print(f"\U0001f4da {len(index)} palabras \u00fanicas en el \u00edndice")
'''
    os.makedirs("output", exist_ok=True)
    print("Generando clip IDE de prueba...")
    clip = generate_ide_clip(sample, duration=25.0, filename="rag_pipeline.py")
    clip.write_videofile("output/test_ide.mp4", fps=FPS, logger=None)
    print("\u2705 Listo: output/test_ide.mp4")
