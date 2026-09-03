import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_CHAT_ID = os.getenv("ALLOWED_CHAT_ID")
HETZNER_API_TOKEN = os.getenv("HETZNER_API_TOKEN")
SERVER_NAME = os.getenv("SERVER_NAME", "Servidor")

ALERT_CPU_THRESHOLD = float(os.getenv("ALERT_CPU_THRESHOLD", "85"))
ALERT_RAM_THRESHOLD = float(os.getenv("ALERT_RAM_THRESHOLD", "90"))
ALERT_DISK_THRESHOLD = float(os.getenv("ALERT_DISK_THRESHOLD", "85"))

if ALLOWED_CHAT_ID:
    try:
        ALLOWED_CHAT_ID = int(ALLOWED_CHAT_ID)
    except ValueError:
        print("ERROR: ALLOWED_CHAT_ID ha de ser un número (integer).")

def check_config():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("Falta TELEGRAM_BOT_TOKEN al fitxer .env")
    if not ALLOWED_CHAT_ID:
        raise ValueError("Falta ALLOWED_CHAT_ID al fitxer .env")
