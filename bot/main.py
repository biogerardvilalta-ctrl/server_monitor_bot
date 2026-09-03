import logging
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, filters, MessageHandler
from bot.config import TELEGRAM_BOT_TOKEN, ALLOWED_CHAT_ID, SERVER_NAME, check_config
from bot.monitors.system import get_system_stats, format_status_message

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Funcions auxiliars ---

def is_authorized(update: Update) -> bool:
    """Verifica si l'usuari que envia el missatge està autoritzat"""
    if not update.effective_chat:
        return False
    return update.effective_chat.id == ALLOWED_CHAT_ID

async def auth_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Filtre per aturar l'execució si no està autoritzat"""
    if not is_authorized(update):
        logger.warning(f"Accés denegat: Intent d'accés des del chat ID {update.effective_chat.id if update.effective_chat else 'Desconegut'}")
        if update.message:
             await update.message.reply_text("⛔ No tens permisos per utilitzar aquest bot.")
        return False
    return True

# --- Handlers de comandes ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler per a la comanda /start"""
    if not await auth_check(update, context): return
    
    keyboard = [
        ['/status', '/cpu', '/ram'],
        ['/help']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"👋 Hola! Soc el bot de monitoratge del servidor *{SERVER_NAME}*.\n\n"
        f"Estic connectat i llest per rebre comandes. Fes servir /help per veure tot el que puc fer o utilitza els botons a sota.",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler per a la comanda /help"""
    if not await auth_check(update, context): return
    
    help_text = (
        "🛠 *Comandes Disponibles:*\n\n"
        "📊 *Monitoratge de Sistema*\n"
        "/status - Resum complet de l'estat del servidor\n"
        "/cpu - Només informació de la CPU\n"
        "/ram - Només informació de la memòria\n"
        "/disk - Només informació de l'espai en disc\n"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler per a la comanda /status"""
    if not await auth_check(update, context): return
    
    try:
        stats = get_system_stats()
        msg = format_status_message(stats, SERVER_NAME)
        await update.message.reply_text(msg, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error obtenint l'estat: {e}")
        await update.message.reply_text("⚠️ Hi ha hagut un error intentant obtenir l'estat del servidor.")

async def cpu_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    stats = get_system_stats()
    msg = f"🧠 *CPU*: `{stats['cpu']['percent']}%` ({stats['cpu']['cores']} cores)"
    await update.message.reply_text(msg, parse_mode='Markdown')

async def ram_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    stats = get_system_stats()
    msg = f"💾 *RAM*: `{stats['ram']['used_gb']}GB / {stats['ram']['total_gb']}GB` ({stats['ram']['percent']}%)"
    await update.message.reply_text(msg, parse_mode='Markdown')

async def disk_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    stats = get_system_stats()
    msg = f"💿 *Disc*: `{stats['disk']['used_gb']}GB / {stats['disk']['total_gb']}GB` ({stats['disk']['percent']}%)"
    await update.message.reply_text(msg, parse_mode='Markdown')

# --- Funció Principal ---

def main():
    try:
        check_config()
    except Exception as e:
        logger.error(f"Error de configuració: {e}")
        return

    logger.info("Iniciant el bot de monitoratge...")
    
    # Crear aplicació
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Afegir handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("cpu", cpu_info))
    app.add_handler(CommandHandler("ram", ram_info))
    app.add_handler(CommandHandler("disk", disk_info))
    
    # Ignorar missatges d'usuaris no autoritzats que no siguin comandes
    async def ignore_unauthorized(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await auth_check(update, context)
        
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, ignore_unauthorized))
    
    # Iniciar polling
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
