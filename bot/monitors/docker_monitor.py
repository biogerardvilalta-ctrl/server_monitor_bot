import docker
import logging

logger = logging.getLogger(__name__)

def get_docker_client():
    try:
        return docker.from_env()
    except Exception as e:
        logger.error(f"Error connectant a Docker: {e}")
        return None

def list_containers():
    client = get_docker_client()
    if not client:
        return "❌ Error: No s'ha pogut connectar a Docker (està socket muntat?)"
    
    try:
        containers = client.containers.list(all=True)
        if not containers:
            return "No hi ha cap contenidor Docker."
        
        msg = "📦 *Contenidors Docker:*\n\n"
        for c in containers:
            status_icon = "🟢" if c.status == "running" else "🔴"
            msg += f"{status_icon} `{c.name}` ({c.status})\n"
            
        return msg
    except Exception as e:
        logger.error(f"Error llistant contenidors: {e}")
        return "⚠️ Error llegint l'estat dels contenidors."

def restart_container(container_name):
    client = get_docker_client()
    if not client:
        return False, "Error de connexió a Docker"
        
    try:
        container = client.containers.get(container_name)
        container.restart()
        return True, f"✅ Contenidor `{container_name}` reiniciat correctament."
    except docker.errors.NotFound:
        return False, f"❌ No s'ha trobat el contenidor `{container_name}`."
    except Exception as e:
        return False, f"⚠️ Error reiniciant: {str(e)}"

def get_container_logs(container_name, tail=30):
    client = get_docker_client()
    if not client:
        return False, "Error de connexió a Docker"
        
    try:
        container = client.containers.get(container_name)
        logs = container.logs(tail=tail).decode('utf-8')
        if not logs:
            logs = "(No hi ha logs recents)"
        return True, logs
    except docker.errors.NotFound:
        return False, f"❌ No s'ha trobat el contenidor `{container_name}`."
    except Exception as e:
        return False, f"⚠️ Error llegint logs: {str(e)}"
