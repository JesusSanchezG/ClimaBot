from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from datetime import datetime
from config import CIUDAD, HISTORIAL_LIMIT
from db import get_chat_state, set_chat_state, add_history, get_history
from weather_api import get_current, get_forecast

DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

def _fecha(dt):
    return f"{DIAS[dt.weekday()]}, {dt.day} de {MESES[dt.month - 1]} de {dt.year}"

def _menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('🌤 Clima Del Día', callback_data='clima_dia'),
         InlineKeyboardButton('📅 Clima Semanal', callback_data='clima_semanal')],
        [InlineKeyboardButton('📋 Historial', callback_data='historial')],
    ])

def _back_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('◀️ Volver', callback_data='volver')],
    ])

def _menu_text():
    return f'🤖 *BotClima* — {CIUDAD}\n\nSelecciona una opción:'

async def _edit_or_send(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, reply_markup=None):
    chat_id = update.effective_chat.id
    state = await get_chat_state(chat_id)
    mid = state['message_id'] if state else None

    if mid:
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=mid, text=text, reply_markup=reply_markup)
            return
        except BadRequest as e:
            if 'not modified' in str(e).lower():
                return
            if 'message to edit' not in str(e).lower():
                raise

    msg = await context.bot.send_message(chat_id, text, reply_markup=reply_markup)
    await set_chat_state(chat_id, msg.message_id)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text(_menu_text(), reply_markup=_menu_kb())
    await set_chat_state(update.effective_chat.id, msg.message_id)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    chat_id = update.effective_chat.id

    if data == 'volver':
        await _edit_or_send(update, context, _menu_text(), _menu_kb())
        return

    try:
        if data == 'clima_dia':
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

        elif data == 'clima_semanal':
            f = await get_forecast()
            lines = [f'📅 PRONÓSTICO 5 DÍAS — {CIUDAD.upper()}\n']
            for d in f:
                dia = DIAS[d['dt'].weekday()]
                lines.append(f'📆 {dia} {d["dt"].day}/{d["dt"].month}  ┃ {d["min"]}° / {d["max"]}° {d["emoji"]} {d["desc"]}')
            text = '\n'.join(lines)
            if f:
                await add_history(chat_id, f[0]['min'], None, None, f'Pronóstico: {f[0]["desc"]}', None, 'forecast')

        elif data == 'historial':
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

    except Exception:
        text = '⚠️ Error al obtener datos del clima. Intenta más tarde.'

    kb = _back_kb() if data != 'volver' else _menu_kb()
    await _edit_or_send(update, context, text, kb)

async def delete_user_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.delete()
    except Exception:
        pass
