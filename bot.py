import logging
import sys

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from config import TOKEN
from db import init_db
from handlers import start, handle_text, unknown_command

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

async def post_init(app):
    await init_db()
    logger.info('DB inicializada, bot listo')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error('Excepción no manejada', exc_info=context.error)
    try:
        if update and update.effective_chat:
            await context.bot.send_message(
                update.effective_chat.id,
                '⚠️ Ocurrió un error inesperado. Intenta de nuevo.',
            )
    except Exception:
        pass

def main():
    if not TOKEN:
        sys.exit('Error: falta TELEGRAM_BOT_TOKEN en el archivo .env')

    app = Application.builder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    app.add_error_handler(error_handler)

    logger.info('Bot iniciando polling...')
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
