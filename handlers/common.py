import logging

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from config import CIUDAD
from db import get_chat_state, set_chat_state, set_menu_state

logger = logging.getLogger(__name__)

LABELS = ['🌤 Clima Del Día', '📅 Clima Semanal', '🌍 Sismos', '📋 Historial', '🏠 Menú']

ACTIONS = {
    '🌤 clima del día': 'clima_dia',
    'clima del día': 'clima_dia',
    '📅 clima semanal': 'clima_semanal',
    'clima semanal': 'clima_semanal',
    '🌍 sismos': 'sismos',
    'sismos': 'sismos',
    '📋 historial': 'historial',
    'historial': 'historial',
    '🏠 menú': 'menu',
    'menú': 'menu',
    'menu': 'menu',
}

EMPTY_KB = InlineKeyboardMarkup([])

def _reply_kb():
    return ReplyKeyboardMarkup(
        [LABELS[:2], LABELS[2:4], LABELS[4:]],
        resize_keyboard=True,
        input_field_placeholder='Selecciona una opción',
    )

def _menu_text():
    return f'🤖 *BotClima* — {CIUDAD}\n\nSelecciona una opción:'

async def _edit_or_send(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, reply_markup=EMPTY_KB):
    chat_id = update.effective_chat.id
    state = await get_chat_state(chat_id)
    mid = state['message_id'] if state else None

    if mid:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id, message_id=mid, text=text,
                parse_mode='Markdown', reply_markup=reply_markup,
            )
            return
        except BadRequest as e:
            if 'not modified' in str(e).lower():
                return
            logger.info('No se pudo editar el mensaje %s: %s', mid, e)

    msg = await context.bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=reply_markup)
    await set_chat_state(chat_id, msg.message_id)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    state = await get_chat_state(chat_id)
    if state:
        for mid in (state.get('menu_message_id'), state.get('message_id')):
            if mid:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=mid)
                except Exception:
                    pass
    msg = await update.message.reply_text(_menu_text(), parse_mode='Markdown', reply_markup=_reply_kb())
    await set_menu_state(chat_id, msg.message_id)

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.delete()
    except Exception:
        pass
    await _edit_or_send(update, context, _menu_text())
