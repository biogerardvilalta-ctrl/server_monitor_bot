import logging
import datetime
import pytz
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, filters, MessageHandler
from bot.config import TELEGRAM_BOT_TOKEN, ALLOWED_CHAT_ID, SERVER_NAME, check_config
from bot.monitors.system import get_system_stats, format_status_message
from bot.monitors.docker_monitor import list_containers, restart_container, get_container_logs
from bot.monitors.backup_monitor import check_backups
from bot.hetzner.client import reboot_server, reset_server, poweroff_server, poweron_server
from bot.monitors.alert_engine import check_alerts_job, send_daily_report_job

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def is_authorized(update: Update) -> bool:
    if not update.effective_chat: return False
    return update.effective_chat.id == ALLOWED_CHAT_ID

async def auth_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not is_authorized(update):
        if update.message:
            await update.message.reply_text("⛔ No tens permisos per utilitzar aquest bot.")
        return False
    return True

# --- Handlers de Sistema ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    keyboard = [
        ['/status', '/containers', '/help'],
        ['/cpu', '/ram', '/disk']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"👋 Hola! Soc el bot de monitoratge de *{SERVER_NAME}*.\nFes servir /help per veure totes les comandes.",
        parse_mode='Markdown', reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    help_text = (
        "🛠 *Comandes Disponibles:*\n\n"
        "📊 *Sistema*\n"
        "/status - Estat general\n"
        "/cpu, /ram, /disk - Mètriques específiques\n\n"
        "📦 *Docker*\n"
        "/containers - Llista de contenidors\n"
        "/restart <nom> - Reinicia un contenidor\n"
        "/logs <nom> - Mostra els últims logs\n\n"
        "⚡ *Energia (Hetzner)*\n"
        "/reboot - Soft reboot (reinici normal)\n"
        "/hardreset - Hard reset (botó d'emergència)\n"
        "/poweroff - Apagar servidor\n"
        "/poweron - Encendre servidor\n\n"
        "💾 *Seguretat*\n"
        "/backups - Estat de les últimes còpies de seguretat\n\n"
        "🔔 *Alertes automàtiques activades*\n"
        "• Avís si CPU > 85%, RAM > 90% o Disc > 85%\n"
        "• Avís si un contenidor cau o s'atura\n"
        "• Report diari automàtic a les 09:00h"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    stats = get_system_stats()
    await update.message.reply_text(format_status_message(stats, SERVER_NAME), parse_mode='Markdown')

async def cpu_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    stats = get_system_stats()
    await update.message.reply_text(f"🧠 *CPU*: `{stats['cpu']['percent']}%` ({stats['cpu']['cores']} cores)", parse_mode='Markdown')

async def ram_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    stats = get_system_stats()
    await update.message.reply_text(f"💾 *RAM*: `{stats['ram']['used_gb']}GB / {stats['ram']['total_gb']}GB` ({stats['ram']['percent']}%)", parse_mode='Markdown')

async def disk_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    stats = get_system_stats()
    await update.message.reply_text(f"💿 *Disc*: `{stats['disk']['used_gb']}GB / {stats['disk']['total_gb']}GB` ({stats['disk']['percent']}%)", parse_mode='Markdown')

# --- Handlers de Docker ---
async def cmd_containers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    await update.message.reply_text(list_containers(), parse_mode='Markdown')

async def cmd_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    if not context.args:
        await update.message.reply_text("⚠️ Has de dir quin contenidor. Exemple: `/restart trading_bot`", parse_mode='Markdown')
        return
    success, msg = restart_container(context.args[0])
    await update.message.reply_text(msg, parse_mode='Markdown')

async def cmd_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    if not context.args:
        await update.message.reply_text("⚠️ Has de dir quin contenidor. Exemple: `/logs trading_bot`", parse_mode='Markdown')
        return
    success, msg = get_container_logs(context.args[0])
    if success:
        await update.message.reply_text(f"📜 *Logs de {context.args[0]}:*\n```text\n{msg[-3800:]}\n```", parse_mode='Markdown')
    else:
        await update.message.reply_text(msg, parse_mode='Markdown')

async def cmd_backups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    success, msg = check_backups()
    await update.message.reply_text(msg, parse_mode='Markdown')

# --- Handlers de Hetzner ---
async def cmd_reboot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    success, msg = reboot_server()
    await update.message.reply_text(msg)

async def cmd_hardreset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    success, msg = reset_server()
    await update.message.reply_text(msg)

async def cmd_poweroff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    success, msg = poweroff_server()
    await update.message.reply_text(msg)

async def cmd_poweron(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    success, msg = poweron_server()
    await update.message.reply_text(msg)

def main():
    check_config()
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("cpu", cpu_info))
    app.add_handler(CommandHandler("ram", ram_info))
    app.add_handler(CommandHandler("disk", disk_info))
    
    app.add_handler(CommandHandler("containers", cmd_containers))
    app.add_handler(CommandHandler("restart", cmd_restart))
    app.add_handler(CommandHandler("logs", cmd_logs))
    app.add_handler(CommandHandler("backups", cmd_backups))
    
    app.add_handler(CommandHandler("reboot", cmd_reboot))
    app.add_handler(CommandHandler("hardreset", cmd_hardreset))
    app.add_handler(CommandHandler("poweroff", cmd_poweroff))
    app.add_handler(CommandHandler("poweron", cmd_poweron))
    
    async def ignore_unauthorized(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await auth_check(update, context)
        
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, ignore_unauthorized))
    
    # --- Programació d'alertes automàtiques i report diari ---
    job_queue = app.job_queue
    if job_queue:
        # Comprovar alertes cada 60 segons
        job_queue.run_repeating(check_alerts_job, interval=60, first=10)
        
        # Enviar report diari cada dia a les 09:00h del matí (Hora Madrid/Barcelona)
        madrid_tz = pytz.timezone('Europe/Madrid')
        report_time = datetime.time(hour=9, minute=0, tzinfo=madrid_tz)
        job_queue.run_daily(send_daily_report_job, time=report_time)
        logger.info("Scheduler d'alertes i report diari inicialitzat correctament.")

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
