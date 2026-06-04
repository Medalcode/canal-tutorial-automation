#!/usr/bin/env python3
"""
Pipeline completo: genera guión + video automáticamente
Uso: python run_tutorial.py --topic "FastAPI para principiantes"
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path


def run_command(cmd: list, description: str):
    """Ejecuta comando y maneja errores"""
    print(f"\n{'='*60}")
    print(f"▶️  {description}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {description}")
        print(f"   Código de error: {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ Excepción: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline completo: guión → video",
        epilog="Ejemplo: python run_tutorial.py --topic 'Docker para principiantes'"
    )
    parser.add_argument("--topic", type=str, required=True, help="Tema del tutorial")
    parser.add_argument("--scenes", type=int, default=5, help="Número de escenas (5-10)")
    parser.add_argument("--output", type=str, default="script.json", help="Archivo script.json")
    parser.add_argument("--skip-script", action="store_true", help="Usar script existente")

    args = parser.parse_args()

    print("\n" + "🎬 "*20)
    print("   PIPELINE AUTOMÁTICO DE TUTORIALES")
    print("🎬 "*20)

    if not args.skip_script:
        cmd = [
            sys.executable, "script_generator_pro.py",
            "--topic", args.topic,
            "--scenes", str(args.scenes),
            "--output", args.output,
        ]

        if not run_command(cmd, f"Generando guión: '{args.topic}'"):
            sys.exit(1)

        # Mostrar contenido del guión
        try:
            import json
            with open(args.output) as f:
                script = json.load(f)
                print("\n📋 Escenas generadas:")
                for i, scene in enumerate(script["scenes"], 1):
                    print(f"   {i}. {scene['title']} ({scene['id']})")
        except:
            pass

    if not os.path.exists(args.output):
        print(f"❌ Script no encontrado: {args.output}")
        sys.exit(1)

    if not run_command(
        [sys.executable, "generate_video.py"],
        "Generando video (esto puede tardar 30-60 min)"
    ):
        sys.exit(1)

    print("\n" + "✅ "*20)
    print("   PIPELINE COMPLETADO")
    print("✅ "*20)

    output_file = "output/video_con_musica.mp4"
    if os.path.exists(output_file):
        size_mb = os.path.getsize(output_file) / (1024 * 1024)
        print(f"\n🎬 Video final: {output_file} ({size_mb:.1f} MB)")
        print(f"📸 Thumbnail: output/thumbnail.png")
        print(f"🎵 Audio: output/narracion.mp3")
    else:
        print(f"\n⚠️  Video no encontrado en {output_file}")


if __name__ == "__main__":
    main()
