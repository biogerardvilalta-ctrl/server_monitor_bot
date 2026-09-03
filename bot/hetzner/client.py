import logging
from hcloud import Client
from hcloud.servers.domain import Server
from bot.config import HETZNER_API_TOKEN, SERVER_NAME

logger = logging.getLogger(__name__)

def get_hcloud_client():
    if not HETZNER_API_TOKEN:
        return None
    try:
        return Client(token=HETZNER_API_TOKEN)
    except Exception as e:
        logger.error(f"Error inicialitzant client Hetzner: {e}")
        return None

def get_server() -> Server:
    client = get_hcloud_client()
    if not client:
        return None
    try:
        servers = client.servers.get_all(name=SERVER_NAME)
        if servers:
            return servers[0]
        return None
    except Exception as e:
        logger.error(f"Error buscant servidor Hetzner: {e}")
        return None

def reboot_server():
    server = get_server()
    if not server:
        return False, "❌ API Token no configurat o Servidor no trobat a Hetzner."
    try:
        server.reboot()
        return True, f"✅ Soft-Reboot enviat a {SERVER_NAME}."
    except Exception as e:
        return False, f"⚠️ Error de Hetzner: {str(e)}"

def reset_server():
    server = get_server()
    if not server:
        return False, "❌ API Token no configurat o Servidor no trobat a Hetzner."
    try:
        server.reset()
        return True, f"✅ Hard-Reset enviat a {SERVER_NAME}."
    except Exception as e:
        return False, f"⚠️ Error de Hetzner: {str(e)}"

def poweroff_server():
    server = get_server()
    if not server:
        return False, "❌ API Token no configurat o Servidor no trobat a Hetzner."
    try:
        server.poweroff()
        return True, f"✅ Ordre d'Apagar enviada a {SERVER_NAME}."
    except Exception as e:
        return False, f"⚠️ Error de Hetzner: {str(e)}"

def poweron_server():
    server = get_server()
    if not server:
        return False, "❌ API Token no configurat o Servidor no trobat a Hetzner."
    try:
        server.poweron()
        return True, f"✅ Ordre d'Encendre enviada a {SERVER_NAME}."
    except Exception as e:
        return False, f"⚠️ Error de Hetzner: {str(e)}"
