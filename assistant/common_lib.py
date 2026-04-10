from policia.settings import BASE_DIR
from gestion.models import Config
import time


ERRORS_ANSWER = ["Lo siento, no puedo ayudarte con eso en este momento.",
                "No tengo suficiente información para responder a tu pregunta.",
                "Por favor, proporciona más detalles para que pueda asistirte mejor.",
                "Ha ocurrido un error al procesar tu solicitud. ¿Podrías intentarlo de nuevo?"]

def get_config(key):
    cfg = Config.objects.filter(key=key).first()
    return cfg.value if cfg != None else ""

#def log2file(msg: str, path: str = "logs/rag_app.log"):
def log2file(msg: str, path: str = None):
    from pathlib import Path
    """Log simple a file."""
    if path is None:
        path = Path(BASE_DIR) / "logs" / "rag_app.log"
    try:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except Exception as e:
        print(f"Logging error: {e}")


