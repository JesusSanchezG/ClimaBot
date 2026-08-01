from telegram import Update
from telegram.ext import ContextTypes

from handlers.common import (
    ACTIONS,
    EMPTY_KB,
    _edit_or_send,
    _menu_text,
    start,
    unknown_command,
)
from handlers import clima, sismos


async def _action_text(action: str, chat_id: int):
    if action == 'clima_dia':
        return await clima.get_clima_dia(chat_id), EMPTY_KB
    if action == 'clima_semanal':
        return await clima.get_clima_semanal(chat_id), EMPTY_KB
    if action == 'historial':
        return await clima.get_historial(chat_id), EMPTY_KB
    if action == 'sismos':
        return sismos.get_sismos_menu()
    return _menu_text(), EMPTY_KB


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    action = ACTIONS.get(update.message.text.strip().lower())

    try:
        await update.message.delete()
    except Exception:
        pass

    if action is None:
        return

    try:
        text, kb = await _action_text(action, chat_id)
    except Exception:
        text, kb = '⚠️ Error al obtener los datos. Intenta más tarde.', EMPTY_KB

    await _edit_or_send(update, context, text, kb)


from handlers.sismos import check_earthquakes, sismo_callback  # noqa: E402

__all__ = [
    'start',
    'unknown_command',
    'handle_text',
    'sismo_callback',
    'check_earthquakes',
]
