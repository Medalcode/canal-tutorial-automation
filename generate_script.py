import argparse
import json
import os

import google.generativeai as genai


def generate_script(topic: str, output_file: str = "script.json"):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: La variable de entorno GEMINI_API_KEY no está configurada.")
        print("Por favor, obtén una en https://aistudio.google.com/ y ejecútalo así:")
        print("GEMINI_API_KEY=\"tu_clave\" python generate_script.py --topic \"...\"")
        return

    genai.configure(api_key=api_key)

    # Using Gemini 1.5 Pro or Flash, which support JSON structured output well.
    # In this case we'll just use gemini-1.5-flash as it is fast and capable.
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    Eres un experto creador de tutoriales técnicos en video para YouTube/TikTok.
    Debes crear un guion estructurado para el tema: "{topic}".

    El tutorial debe tener al menos 4-6 secciones (por ejemplo: intro, instalacion, codigo, ejecucion, cierre, etc.).
    Para cada escena debes generar:
    - id: un identificador corto sin espacios (ej: 'intro', 'instalacion').
    - title: el título que aparecerá en pantalla.
    - narration: el texto que leerá la voz generada (TTS). Debe ser fluido y directo.
    - commands: una lista de strings con los comandos de terminal o código a mostrar.

    Devuelve estrictamente un objeto JSON con la siguiente estructura y sin formato Markdown (sin ```json):
    {{
      "topic": "{topic}",
      "scenes": [
        {{
          "id": "intro",
          "title": "...",
          "narration": "...",
          "commands": ["..."]
        }}
      ]
    }}
    """

    print(f"Generando guion para: '{topic}' usando Gemini...")
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
            )
        )

        script_data = json.loads(response.text)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(script_data, f, ensure_ascii=False, indent=2)

        print(f"Guion generado exitosamente y guardado en {output_file}")
    except Exception as e:
        print(f"Error al generar el guion: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Detalle: {e.response.text}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generar guion automático con Gemini API")
    parser.add_argument("--topic", type=str, required=True, help="El tema del tutorial")
    parser.add_argument("--output", type=str, default="script.json", help="Archivo de salida JSON")

    args = parser.parse_args()
    generate_script(args.topic, args.output)
