import os
import pickle
from logger import get_logger

log = get_logger("youtube_uploader")

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = "youtube_token.pkl"
CLIENT_SECRETS_FILE = "client_secret.json"

def get_credentials():
    """Obtiene o refresca las credenciales OAuth. Devuelve las credenciales."""
    credentials = None

    # Si ya tenemos un token guardado, lo cargamos
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            credentials = pickle.load(f)

    # Si el token expiró, lo refrescamos automáticamente
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(credentials, f)
        return credentials

    # Si no hay token, lanzar un flujo de autorización
    if not credentials or not credentials.valid:
        if not os.path.exists(CLIENT_SECRETS_FILE):
            raise FileNotFoundError(
                f"No se encontró '{CLIENT_SECRETS_FILE}'. "
                "Sigue las instrucciones para configurar las credenciales de Google Cloud."
            )

        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, SCOPES
        )
        # Usa run_local_server para abrir el navegador del usuario
        credentials = flow.run_local_server(
            port=8765,
            success_message="✅ Autorización completada. Puedes cerrar esta pestaña.",
            open_browser=True
        )

        # Guardamos el token para la próxima vez (no hay que volver a loguear)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(credentials, f)

    return credentials


def upload_to_youtube(video_file, title, description, tags, category_id="27"):
    """
    Sube un video a YouTube usando OAuth 2.0 y la YouTube Data API v3.
    Devuelve la URL del video subido.
    """
    log.info("Autenticando con YouTube...")
    credentials = get_credentials()

    youtube = googleapiclient.discovery.build(
        "youtube", "v3", credentials=credentials
    )

    request_body = {
        "snippet": {
            "categoryId": category_id,
            "description": description,
            "title": title,
            "tags": tags if tags else []
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": True
        }
    }

    log.info(f"Subiendo a YouTube: {title}")

    media_file = MediaFileUpload(video_file, chunksize=-1, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media_file
    )

    response = request.execute()
    video_id = response.get("id")
    url = f"https://youtu.be/{video_id}"
    log.info(f"✅ Subida completada: {url}")
    return url


def authorize_youtube():
    """
    Función auxiliar para pre-autorizar YouTube antes de generar el primer video.
    Llama a esta función desde la línea de comandos para generar el token.
    """
    log.info("Iniciando proceso de autorización con YouTube...")
    credentials = get_credentials()
    if credentials and credentials.valid:
        log.info("✅ Autorización exitosa. Ya puedes subir videos a YouTube desde la app.")
    else:
        log.error("❌ No se pudo completar la autorización.")


if __name__ == "__main__":
    authorize_youtube()
