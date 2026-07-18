#!/usr/bin/env python3
"""
Script Generator Pro - Genera guiones de múltiples fuentes
Fuentes soportadas: Gemini IA, YouTube, Markdown, URLs
"""

import argparse
import json
import os
import sys
from pathlib import Path

import google.generativeai as genai


def load_from_markdown(file_path: str) -> dict:
    """Carga guión desde archivo Markdown estructurado"""
    print(f"📄 Cargando guión desde Markdown: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    scenes = []
    current_scene = None
    current_section = None

    for line in lines:
        if line.startswith("## "):
            if current_scene:
                scenes.append(current_scene)
            scene_title = line.replace("## ", "").strip()
            current_scene = {
                "id": scene_title.lower().replace(" ", "_"),
                "title": scene_title,
                "narration": "",
                "commands": []
            }
            current_section = "narration"
        elif line.startswith("### "):
            current_section = line.replace("### ", "").strip().lower()
        elif line.startswith("```"):
            current_section = "code"
        elif line.startswith("$ "):
            if current_scene:
                current_scene["commands"].append(line.replace("$ ", "").strip())
        elif current_scene and line.strip():
            if current_section == "narration":
                current_scene["narration"] += line.strip() + " "

    if current_scene:
        scenes.append(current_scene)

    return {
        "topic": Path(file_path).stem,
        "scenes": scenes
    }


def generate_with_gemini(topic: str, num_scenes: int = 5) -> dict:
    """Genera guión usando Gemini API"""
    print(f"🤖 Generando guión con Gemini IA para: '{topic}'")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY no configurada")
        print("   Obtén una en: https://aistudio.google.com/")
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""
    Eres un experto creador de tutoriales técnicos para YouTube.
    Crea un guion estructurado para: "{topic}"

    Requisitos:
    - Mínimo {num_scenes} secciones con: introducción, conceptos clave, implementación, demostración, conclusión
    - Narración clara, directa y para principiantes
    - Comandos/código realista y ejecutable
    - Duración total estimada: 8-12 minutos

    Responde SOLO con JSON válido (sin ```json):
    {{
      "topic": "{topic}",
      "youtube_title": "Título llamativo para YouTube...",
      "youtube_description": "Descripción optimizada para SEO...",
      "youtube_tags": ["tag1", "tag2", "tag3"],
      "scenes": [
        {{
          "id": "intro",
          "title": "Introducción",
          "narration": "Texto de narración...",
          "commands": ["comando1", "comando2"]
        }}
      ]
    }}
    """

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
            )
        )

        script_data = json.loads(response.text)
        print(f"✅ Guión generado: {len(script_data['scenes'])} escenas")
        return script_data
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def validate_script(script_data: dict) -> bool:
    """Valida estructura del guión"""
    required_keys = ["topic", "scenes"]
    if not all(k in script_data for k in required_keys):
        print("❌ Estructura inválida: faltan campos requeridos")
        return False

    if not isinstance(script_data["scenes"], list) or len(script_data["scenes"]) < 3:
        print("❌ El guión debe tener al menos 3 escenas")
        return False

    for i, scene in enumerate(script_data["scenes"]):
        required = ["id", "title", "narration", "commands"]
        if not all(k in scene for k in required):
            print(f"❌ Escena {i}: faltan campos {set(required) - set(scene.keys())}")
            return False

    return True


def interactive_menu() -> tuple[str, int]:
    """Menú interactivo para elegir fuente"""
    print("\n" + "="*50)
    print("🎬 GENERADOR DE GUIONES PRO")
    print("="*50)
    print("\nFuentes disponibles:")
    print("1. 🤖 Gemini IA (recomendado)")
    print("2. 📄 Archivo Markdown local")
    print("3. 🔗 URL (blog/artículo)")

    choice = input("\nElige una opción (1-3): ").strip()

    if choice == "1":
        topic = input("\nTema del tutorial: ").strip()
        if not topic:
            print("❌ El tema no puede estar vacío")
            sys.exit(1)
        num_scenes = input("Número de escenas (5-10, default=5): ").strip()
        num_scenes = int(num_scenes) if num_scenes.isdigit() else 5
        return ("gemini", topic, num_scenes)

    elif choice == "2":
        path = input("\nRuta del archivo Markdown: ").strip()
        if not os.path.exists(path):
            print(f"❌ Archivo no encontrado: {path}")
            sys.exit(1)
        return ("markdown", path, 0)

    else:
        print("❌ Opción no válida")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Generador de guiones profesional")
    parser.add_argument("--topic", type=str, help="Tema (Gemini)")
    parser.add_argument("--source", choices=["gemini", "markdown"], default="gemini")
    parser.add_argument("--path", type=str, help="Ruta del archivo (Markdown)")
    parser.add_argument("--output", type=str, default="script.json")
    parser.add_argument("--scenes", type=int, default=5, help="Número de escenas (Gemini)")
    parser.add_argument("--validate-only", action="store_true")

    args = parser.parse_args()

    if args.topic:
        source = args.source
        data = args.topic
    elif args.path:
        source = "markdown"
        data = args.path
    else:
        result = interactive_menu()
        source = result[0]
        data = result[1]
        num_scenes = result[2] if len(result) > 2 else args.scenes
        args.scenes = num_scenes

    if source == "gemini":
        script_data = generate_with_gemini(data, args.scenes)
    elif source == "markdown":
        script_data = load_from_markdown(data)
    else:
        print("❌ Fuente no soportada")
        sys.exit(1)

    if not validate_script(script_data):
        sys.exit(1)

    if args.validate_only:
        print("✅ Guión válido")
        return

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Guión guardado en: {args.output}")
    print(f"   Tema: {script_data['topic']}")
    print(f"   Escenas: {len(script_data['scenes'])}")
    print("\n🎬 Próximo paso:")
    print("   python generate_video.py")


if __name__ == "__main__":
    main()
