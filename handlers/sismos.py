import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import SISMO_ALERT_MAG, CIUDAD
from db import add_history, get_all_chat_ids, kv_get, kv_set
from earthquakes_api import get_recent_bc, get_today_bc, get_strongest_today, get_region_quakes
from handlers.common import _edit_or_send
from handlers.format import _fecha, _mag_emoji

logger = logging.getLogger(__name__)

ALERT_KV_KEY = 'sismo_last_seen_ms'

MAX_MSG_LEN = 4000

def _sismos_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('🕐 Sismos de hoy', callback_data='sismo_hoy'),
         InlineKeyboardButton('💪 Más fuerte hoy', callback_data='sismo_fuerte')],
        [InlineKeyboardButton('📜 Últimos 5 sismos', callback_data='sismo_recientes')],
    ])

def get_sismos_menu():
    text = '🌍 *SISMOS — BAJA CALIFORNIA*\n\nSelecciona una opción:'
    return text, _sismos_kb()

def _format_sismo(e):
    lines = [f'📊 Magnitud: {e["mag"]:.1f} {_mag_emoji(e["mag"])}']
    if e['place']:
        lines.append(f'📍 {e["place"]}')
    if e['depth_km'] is not None:
        lines.append(f'📏 Profundidad: {e["depth_km"]:.1f} km')
    lines.append(f'🕐 {_fecha(e["time"])} {e["time"].strftime("%H:%M")} hrs')
    if e['felt']:
        lines.append(f'👥 Reportado sentido por {e["felt"]} personas')
    lines.append('🌊 Tsunami: Sí ⚠️' if e['tsunami'] else '🌊 Tsunami: No')
    if e['url']:
        lines.append(f'🔗 {e["url"]}')
    return '\n'.join(lines)

async def get_sismo_text(action: str, chat_id: int):
    if action == 'sismo_hoy':
        evs = await get_today_bc()
        if not evs:
            return 'Sin sismos hoy en Baja California.', _sismos_kb()
        lines = [f'🕐 *SISMOS DE HOY — BAJA CALIFORNIA* ({len(evs)})\n']
        for e in evs:
            lines.append(f'M {e["mag"]:.1f} {_mag_emoji(e["mag"])}  {e["time"].strftime("%H:%M")}  —  {e["place"]}')
        text = '\n'.join(lines)
        if len(text) > MAX_MSG_LEN:
            head, total = [], 0
            for ln in lines:
                if total + len(ln) + 1 > MAX_MSG_LEN:
                    break
                head.append(ln)
                total += len(ln) + 1
            text = '\n'.join(head) + f'\n… y {len(evs) - len(head) + 1} más'
        strongest = max(evs, key=lambda e: e['mag'])
        await add_history(chat_id, strongest['mag'], None, None, f'{len(evs)} sismos hoy (BC)', strongest['depth_km'], 'sismo')

    elif action == 'sismo_fuerte':
        evs = await get_strongest_today()
        if not evs:
            return 'Sin sismos hoy en Baja California.', _sismos_kb()
        e = evs[0]
        text = f'💪 *MÁS FUERTE DE HOY — BAJA CALIFORNIA*\n\n{_format_sismo(e)}'
        await add_history(chat_id, e['mag'], None, None, e['place'], e['depth_km'], 'sismo')

    else:
        evs = await get_recent_bc(5)
        if not evs:
            return 'Sin sismos registrados.', _sismos_kb()
        lines = [f'📜 *ÚLTIMOS 5 SISMOS — BAJA CALIFORNIA*\n']
        for e in evs:
            lines.append(f'M {e["mag"]:.1f} {_mag_emoji(e["mag"])}  {e["time"].strftime("%d/%m %H:%M")}  —  {e["place"]}')
        text = '\n'.join(lines)

    return text, _sismos_kb()

async def sismo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    chat_id = update.effective_chat.id
    try:
        text, kb = await get_sismo_text(q.data, chat_id)
    except Exception:
        text, kb = '⚠️ Error al obtener datos de sismos. Intenta más tarde.', _sismos_kb()
    await _edit_or_send(update, context, text, kb)

async def check_earthquakes(context: ContextTypes.DEFAULT_TYPE):
    try:
        events = await get_region_quakes()
    except Exception:
        logger.warning('Fallo el escaneo de sismos para alertas', exc_info=True)
        return
    if not events:
        return

    newest = max(e['time'] for e in events)
    newest_ms = newest.timestamp() * 1000
    last_ms = float(await kv_get(ALERT_KV_KEY) or 0)

    if last_ms == 0:
        await kv_set(ALERT_KV_KEY, int(newest_ms))
        return

    new = [
        e for e in events
        if e['time'].timestamp() * 1000 > last_ms
        and e['mag'] is not None
        and e['mag'] >= SISMO_ALERT_MAG
    ]

    if new:
        strongest = max(new, key=lambda e: e['mag'])
        text = (
            f'🚨 *SISMO DETECTADO — {CIUDAD.upper()}* 🚨\n\n'
            f'{_format_sismo(strongest)}'
        )
        chat_ids = await get_all_chat_ids()
        for chat_id in chat_ids:
            try:
                await context.bot.send_message(chat_id, text, parse_mode='Markdown')
            except Exception:
                continue
        logger.info('Alerta de sismo M%.1f enviada a %d chats', strongest['mag'], len(chat_ids))

    if newest_ms > last_ms:
        await kv_set(ALERT_KV_KEY, int(newest_ms))
