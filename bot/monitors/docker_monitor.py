import docker
import logging

logger = logging.getLogger(__name__)

def get_client():
    # Usar unix socket directament per evitar incompatibilitats http+docker d'urllib3
    return docker.DockerClient(base_url='unix://var/run/docker.sock')

def list_containers():
    try:
        client = get_client()
        containers = client.containers.list(all=True)
        if not containers:
            return "No hi ha cap contenidor Docker actiu o registrat."
        
        msg = "📦 *Contenidors Docker:*\n\n"
        for c in containers:
            status_icon = "🟢" if c.status == "running" else "🔴"
            msg += f"{status_icon} `{c.name}` ({c.status})\n"
            
        return msg
    except Exception as e:
        logger.error(f"Error connectant o llistant Docker: {e}")
        return f"❌ Error connectant a Docker:\n`{str(e)}`"

def restart_container(container_name):
    try:
        client = get_client()
        container = client.containers.get(container_name)
        container.restart()
        return True, f"✅ Contenidor `{container_name}` reiniciat correctament."
    except docker.errors.NotFound:
        return False, f"❌ No s'ha trobat el contenidor `{container_name}`."
    except Exception as e:
        return False, f"⚠️ Error reiniciant `{container_name}`:\n`{str(e)}`"

def get_container_logs(container_name, tail=30):
    try:
        client = get_client()
        container = client.containers.get(container_name)
        logs = container.logs(tail=tail).decode('utf-8', errors='replace')
        if not logs:
            logs = "(No hi ha logs recents)"
        return True, logs
    except docker.errors.NotFound:
        return False, f"❌ No s'ha trobat el contenidor `{container_name}`."
    except Exception as e:
        return False, f"⚠️ Error llegint logs de `{container_name}`:\n`{str(e)}`"
