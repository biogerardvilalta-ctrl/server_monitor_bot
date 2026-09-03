import os
import glob
import datetime
import logging

logger = logging.getLogger(__name__)

# Com que Docker té muntat el directori arrel del servidor a /host,
# la ruta /home/admin/backups de Hetzner està a /host/home/admin/backups
BACKUP_DIR = "/host/home/admin/backups"

def check_backups():
    if not os.path.exists(BACKUP_DIR):
        return False, f"❌ El directori de backups no existeix: `{BACKUP_DIR}`\nSi s'han mogut, cal actualitzar la ruta al bot."

    # Llista dels projectes que esperem trobar
    projectes = ["mailcow", "psicoaissist", "trading"]
    resultats = []
    tot_correcte = True

    try:
        rutes_absolutes = []
        # Cerca recursiva (entrarà a carpetes com /trading_bot/)
        for root, dirs, files in os.walk(BACKUP_DIR):
            for file in files:
                if file.endswith(".gz") or file.endswith(".db"):
                    rutes_absolutes.append(os.path.join(root, file))
        
        for projecte in projectes:
            # Buscar fitxers que tinguin el nom del projecte a l'arxiu
            fitxers_projecte = [f for f in rutes_absolutes if projecte in os.path.basename(f).lower()]
            
            if not fitxers_projecte:
                resultats.append(f"🔴 `{projecte}`: No s'ha trobat cap backup!")
                tot_correcte = False
                continue
            
            # Agafar el fitxer modificat més recentment
            arxiu_mes_recent = max(fitxers_projecte, key=os.path.getmtime)
            nom_arxiu = os.path.basename(arxiu_mes_recent)
            
            # Temps des de la modificació
            mtime = os.path.getmtime(arxiu_mes_recent)
            data_mod = datetime.datetime.fromtimestamp(mtime)
            hores_passades = (datetime.datetime.now() - data_mod).total_seconds() / 3600
            
            if hores_passades > 30:
                resultats.append(f"🔴 `{projecte}`: Desfasat! ({hores_passades:.1f}h) - `{nom_arxiu}`")
                tot_correcte = False
            else:
                resultats.append(f"🟢 `{projecte}`: OK (Fa {hores_passades:.1f}h) - `{nom_arxiu}`")
                
        # Format del missatge
        msg = "💾 *Estat de les Còpies de Seguretat:*\n\n"
        msg += "\n".join(resultats)
        
        return tot_correcte, msg

    except Exception as e:
        logger.error(f"Error llegint backups: {e}")
        return False, f"⚠️ Error intentant llegir els backups: {str(e)}"
