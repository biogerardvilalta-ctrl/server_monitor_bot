import os
import psutil
import datetime
import time

def get_system_stats():
    # Temps d'uptime
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.datetime.now() - boot_time
    uptime_str = str(uptime).split('.')[0] # Treure els microsegons

    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count(logical=True)
    load_avg = [round(x, 2) for x in psutil.getloadavg()] if hasattr(psutil, 'getloadavg') else []

    # Memòria
    ram = psutil.virtual_memory()
    ram_total = round(ram.total / (1024 ** 3), 2)
    ram_used = round(ram.used / (1024 ** 3), 2)
    ram_percent = ram.percent

    # Disc (arrel / o /host si estem en Docker)
    disk_path = '/host' if os.path.exists('/host') else '/'
    disk = psutil.disk_usage(disk_path)
    disk_total = round(disk.total / (1024 ** 3), 2)
    disk_used = round(disk.used / (1024 ** 3), 2)
    disk_percent = disk.percent

    return {
        "uptime": uptime_str,
        "cpu": {
            "percent": cpu_percent,
            "cores": cpu_count,
            "load_avg": load_avg
        },
        "ram": {
            "total_gb": ram_total,
            "used_gb": ram_used,
            "percent": ram_percent
        },
        "disk": {
            "total_gb": disk_total,
            "used_gb": disk_used,
            "percent": disk_percent
        }
    }

def format_status_message(stats, server_name):
    msg = f"📊 *Estat de {server_name}*\n"
    msg += f"⏱ Uptime: `{stats['uptime']}`\n\n"
    
    msg += f"🧠 *CPU*: `{stats['cpu']['percent']}%` ({stats['cpu']['cores']} cores)\n"
    if stats['cpu']['load_avg']:
        msg += f"   Load Avg: `{stats['cpu']['load_avg']}`\n"
        
    msg += f"💾 *RAM*: `{stats['ram']['used_gb']}GB / {stats['ram']['total_gb']}GB` ({stats['ram']['percent']}%)\n"
    
    msg += f"💿 *Disc*: `{stats['disk']['used_gb']}GB / {stats['disk']['total_gb']}GB` ({stats['disk']['percent']}%)\n"
    
    return msg
