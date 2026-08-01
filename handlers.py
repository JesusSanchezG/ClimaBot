from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

import logging
from datetime import datetime
from config import CIUDAD, HISTORIAL_LIMIT
from db import get_chat_state, set_chat_state, add_history, get_history
from weather_api import get_current, get_forecast

logger = logging.getLogger(__name__)

DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

LABELS = ['🌤 Clima Del Día', '📅 Clima Semanal', '📋 Historial', '🏠 Menú']

ACTIONS = {
    '🌤 clima del día': 'clima_dia',
    'clima del día': 'clima_dia',
    '📅 clima semanal': 'clima_semanal',
    'clima semanal': 'clima_semanal',
    '📋 historial': 'historial',
    'historial': 'historial',
    '🏠 menú': 'menu',
    'menú': 'menu',
    'menu': 'menu',
}

def _fecha(dt):
    return f"{DIAS[dt.weekday()]}, {dt.day} de {MESES[dt.month - 1]} de {dt.year}"

def _reply_kb():
    return ReplyKeyboardMarkup(
        [LABELS[:2], LABELS[2:3], LABELS[3:]],
        resize_keyboard=True,
        input_field_placeholder='Selecciona una opción',
    )

def _menu_text():
    return f'🤖 *BotClima* — {CIUDAD}\n\nSelecciona una opción:'

async def _edit_or_send(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    chat_id = update.effective_chat.id
    state = await get_chat_state(chat_id)
    mid = state['message_id'] if state else None

    if mid:
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=mid, text=text, parse_mode='Markdown')
            return
        except BadRequest as e:
            if 'not modified' in str(e).lower():
                return
            if 'message to edit' in str(e).lower():
                pass
            else:
                logger.info('No se pudo editar el mensaje %s: %s', mid, e)

    try:
        msg = await context.bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=_reply_kb())
    except BadRequest:
        msg = await context.bot.send_message(chat_id, text, reply_markup=_reply_kb())
    await set_chat_state(chat_id, msg.message_id)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    state = await get_chat_state(chat_id)
    if state:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=state['message_id'])
        except Exception:
            pass
    msg = await update.message.reply_text(_menu_text(), parse_mode='Markdown', reply_markup=_reply_kb())
    await set_chat_state(chat_id, msg.message_id)

async def _handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> str:
    chat_id = update.effective_chat.id

    if action == 'clima_dia':
        w = await get_current()
        text = (
            f'🌤️ ESTE ES EL CLIMA EN {CIUDAD.upper()}\n\n'
            f'🌡️ Temperatura: {w["temp"]:.2f}°C\n'
            f'📖 Descripción: {w["desc"]}\n'
            f'💧 Humedad: {w["humidity"]}%\n'
            f'💨 Viento: {w["wind"]:.2f} m/s\n\n'
            f'📅 {_fecha(w["dt"])}\n'
            f'🕐 {w["dt"].strftime("%H:%M")} hrs\n\n'
            f'¡Que tengas un excelente día! ☀️'
        )
        await add_history(chat_id, w['temp'], w['feels_like'], w['humidity'], w['desc'], w['wind'], 'current')

    elif action == 'clima_semanal':
        f = await get_forecast()
        lines = [f'📅 PRONÓSTICO 5 DÍAS — {CIUDAD.upper()}\n']
        for d in f:
            dia = DIAS[d['dt'].weekday()]
            lines.append(f'📆 {dia} {d["dt"].day}/{d["dt"].month}  ┃ {d["min"]}° / {d["max"]}° {d["emoji"]} {d["desc"]}')
        text = '\n'.join(lines)
        if f:
            await add_history(chat_id, f[0]['min'], None, None, f'Pronóstico: {f[0]["desc"]}', None, 'forecast')

    elif action == 'historial':
        h = await get_history(chat_id, HISTORIAL_LIMIT)
        if not h:
            text = '📋 *Historial*\n\n_Sin consultas aún._'
        else:
            lines = [f'📋 *Historial — últimas {len(h)} consultas*\n']
            for i, row in enumerate(h, 1):
                icon = '🌤' if row['type'] == 'current' else '📅'
                temp = f'{row["temp"]}°C' if row['temp'] is not None else '--'
                lines.append(f'#{i}  {row["timestamp"][:16]}  {temp}  {row["description"]} {icon}')
            text = '\n'.join(lines)

    else:
        text = _menu_text()

    return text

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
        text = await _handle_action(update, context, action)
    except Exception:
        text = '⚠️ Error al obtener datos del clima. Intenta más tarde.'

    await _edit_or_send(update, context, text)

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.delete()
    except Exception:
        pass
    await _edit_or_send(update, context, _menu_text())
