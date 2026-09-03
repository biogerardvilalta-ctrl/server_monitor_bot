import logging
from bot.config import ALERT_CPU_THRESHOLD, ALERT_RAM_THRESHOLD, ALERT_DISK_THRESHOLD, SERVER_NAME, ALLOWED_CHAT_ID
from bot.monitors.system import get_system_stats
from bot.monitors.docker_monitor import get_client, restart_container

logger = logging.getLogger(__name__)

# Estat previ per no enviar alertes repetides cada minut
previous_state = {
    "cpu_alert": False,
    "ram_alert": False,
    "disk_alert": False,
    "failed_containers": set()
}

async def check_alerts_job(context):
    global previous_state
    try:
        stats = get_system_stats()
        
        # 1. Alerta de CPU
        cpu_p = stats['cpu']['percent']
        if cpu_p >= ALERT_CPU_THRESHOLD:
            if not previous_state["cpu_alert"]:
                previous_state["cpu_alert"] = True
                await context.bot.send_message(
                    chat_id=ALLOWED_CHAT_ID,
                    text=f"⚠️ *ALERTA CPU ALTA*\n\nEl servidor *{SERVER_NAME}* està utilitzant un `{cpu_p}%` de CPU (Llindar: {ALERT_CPU_THRESHOLD}%).",
                    parse_mode='Markdown'
                )
        else:
            if previous_state["cpu_alert"]:
                previous_state["cpu_alert"] = False
                await context.bot.send_message(
                    chat_id=ALLOWED_CHAT_ID,
                    text=f"✅ *RECUPERACIÓ CPU*\n\nLa CPU del servidor *{SERVER_NAME}* ha tornat a nivells normals (`{cpu_p}%`).",
                    parse_mode='Markdown'
                )

        # 2. Alerta de RAM
        ram_p = stats['ram']['percent']
        if ram_p >= ALERT_RAM_THRESHOLD:
            if not previous_state["ram_alert"]:
                previous_state["ram_alert"] = True
                await context.bot.send_message(
                    chat_id=ALLOWED_CHAT_ID,
                    text=f"⚠️ *ALERTA MEMÒRIA RAM ALTA*\n\nEl servidor *{SERVER_NAME}* té la RAM al `{ram_p}%` (`{stats['ram']['used_gb']}GB / {stats['ram']['total_gb']}GB`).",
                    parse_mode='Markdown'
                )
        else:
            if previous_state["ram_alert"]:
                previous_state["ram_alert"] = False
                await context.bot.send_message(
                    chat_id=ALLOWED_CHAT_ID,
                    text=f"✅ *RECUPERACIÓ RAM*\n\nLa RAM del servidor *{SERVER_NAME}* s'ha normalitzat (`{ram_p}%`).",
                    parse_mode='Markdown'
                )

        # 3. Alerta de Disc
        disk_p = stats['disk']['percent']
        if disk_p >= ALERT_DISK_THRESHOLD:
            if not previous_state["disk_alert"]:
                previous_state["disk_alert"] = True
                await context.bot.send_message(
                    chat_id=ALLOWED_CHAT_ID,
                    text=f"🚨 *ALERTA ESPAI EN DISC*\n\nEl servidor *{SERVER_NAME}* té el disc al `{disk_p}%` (`{stats['disk']['used_gb']}GB / {stats['disk']['total_gb']}GB`).",
                    parse_mode='Markdown'
                )
        else:
            if previous_state["disk_alert"]:
                previous_state["disk_alert"] = False
                await context.bot.send_message(
                    chat_id=ALLOWED_CHAT_ID,
                    text=f"✅ *RECUPERACIÓ DISC*\n\nL'espai en disc de *{SERVER_NAME}* s'ha normalitzat (`{disk_p}%`).",
                    parse_mode='Markdown'
                )

        # 4. Auto-Reparació i Alertas de Contenidors Caiguts
        try:
            client = get_client()
            containers = client.containers.list(all=True)
            current_failed = set()
            
            for c in containers:
                # No monitoritzar el propi bot de monitoratge si està aturat manualment
                if c.name == "server-monitor-bot":
                    continue
                    
                if c.status not in ['running', 'restarting']:
                    current_failed.add(c.name)

            # Contenidors que han caigut nous -> Intentar AUTO-REPARACIÓ
            new_failed = current_failed - previous_state["failed_containers"]
            for name in new_failed:
                logger.warning(f"Contenidor {name} caigut. Intentant auto-reinici...")
                
                # Intentar reiniciar el contenidor automàticament
                success, restart_msg = restart_container(name)
                
                if success:
                    await context.bot.send_message(
                        chat_id=ALLOWED_CHAT_ID,
                        text=f"⚡ *AUTO-REPARACIÓ EXECUTADA*\n\nEl servei `{name}` havia caigut al servidor *{SERVER_NAME}*.\n\n🔄 *Acció*: El bot l'ha reiniciat automàticament i torna a estar actiu (🟢 running).",
                        parse_mode='Markdown'
                    )
                else:
                    await context.bot.send_message(
                        chat_id=ALLOWED_CHAT_ID,
                        text=f"🚨 *CONTENIDOR CAIGUT (AUTO-REPARACIÓ FALLIDA)*\n\nEl servei `{name}` ha caigut al servidor *{SERVER_NAME}*.\n\n❌ L'intent de reiniciar-lo automàticament ha fallat:\n`{restart_msg}`\n\nComprova els logs amb `/logs {name}`.",
                        parse_mode='Markdown'
                    )

            previous_state["failed_containers"] = current_failed

        except Exception as e:
            logger.error(f"Error comprovant contenidors a les alertes: {e}")

    except Exception as e:
        logger.error(f"Error executant job d'alertes: {e}")


async def send_daily_report_job(context):
    try:
        stats = get_system_stats()
        
        msg = f"📊 *REPORT DIARI — {SERVER_NAME}*\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"⏱ Uptime: `{stats['uptime']}`\n\n"
        msg += f"🧠 *CPU*: `{stats['cpu']['percent']}%` ({stats['cpu']['cores']} cores)\n"
        msg += f"💾 *RAM*: `{stats['ram']['used_gb']}GB / {stats['ram']['total_gb']}GB` ({stats['ram']['percent']}%)\n"
        msg += f"💿 *Disc*: `{stats['disk']['used_gb']}GB / {stats['disk']['total_gb']}GB` ({stats['disk']['percent']}%)\n\n"
        
        try:
            client = get_client()
            containers = client.containers.list(all=True)
            msg += f"📦 *Contenidors ({len(containers)} total):*\n"
            for c in containers:
                status_icon = "🟢" if c.status == "running" else "🔴"
                msg += f"  {status_icon} `{c.name}` ({c.status})\n"
        except Exception:
            msg += "📦 Error llegint l'estat dels contenidors.\n"

        msg += "\n✅ Tot funcionant correctament!"
        
        await context.bot.send_message(
            chat_id=ALLOWED_CHAT_ID,
            text=msg,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error enviant report diari: {e}")
