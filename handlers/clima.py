from config import CIUDAD, HISTORIAL_LIMIT
from db import add_history, get_history
from weather_api import get_current, get_forecast
from handlers.format import DIAS, _fecha

async def get_clima_dia(chat_id):
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
    return text

async def get_clima_semanal(chat_id):
    f = await get_forecast()
    lines = [f'📅 PRONÓSTICO 5 DÍAS — {CIUDAD.upper()}\n']
    for d in f:
        dia = DIAS[d['dt'].weekday()]
        lines.append(f'📆 {dia} {d["dt"].day}/{d["dt"].month}  ┃ {d["min"]}° / {d["max"]}° {d["emoji"]} {d["desc"]}')
    text = '\n'.join(lines)
    if f:
        await add_history(chat_id, f[0]['min'], None, None, f'Pronóstico: {f[0]["desc"]}', None, 'forecast')
    return text

ICONS = {'current': '🌤', 'forecast': '📅', 'sismo': '🌍'}

async def get_historial(chat_id):
    h = await get_history(chat_id, HISTORIAL_LIMIT)
    if not h:
        return '📋 *Historial*\n\n_Sin consultas aún._'
    lines = [f'📋 *Historial — últimas {len(h)} consultas*\n']
    for i, row in enumerate(h, 1):
        icon = ICONS.get(row['type'], '📋')
        temp = f'{row["temp"]}°C' if row['temp'] is not None else '--'
        lines.append(f'#{i}  {row["timestamp"][:16]}  {temp}  {row["description"]} {icon}')
    return '\n'.join(lines)
