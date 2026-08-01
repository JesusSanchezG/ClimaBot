from datetime import datetime
from zoneinfo import ZoneInfo
from collections import Counter

from config import OWM_API_KEY, LAT, LON, CACHE_TTL, TZ
from http_client import get_json, cache_get, cache_set

CURRENT_URL = 'https://api.openweathermap.org/data/2.5/weather'
FORECAST_URL = 'https://api.openweathermap.org/data/2.5/forecast'

ICON_MAP = {
    '01': '☀️', '02': '🌤', '03': '⛅', '04': '☁️',
    '09': '🌧', '10': '🌦', '11': '⛈', '13': '❄️', '50': '🌫',
}

def _emoji(icon):
    return ICON_MAP.get(icon[:2], '🌡')

async def get_current():
    cached = cache_get('current', CACHE_TTL)
    if cached:
        return cached

    data = await get_json(CURRENT_URL, {
        'lat': LAT, 'lon': LON,
        'appid': OWM_API_KEY,
        'units': 'metric', 'lang': 'es',
    })

    now = datetime.now(ZoneInfo(TZ))
    r = {
        'temp': data['main']['temp'],
        'feels_like': data['main']['feels_like'],
        'humidity': data['main']['humidity'],
        'desc': data['weather'][0]['description'].capitalize(),
        'wind': data['wind']['speed'],
        'emoji': _emoji(data['weather'][0]['icon']),
        'dt': now,
    }
    cache_set('current', r)
    return r

async def get_forecast():
    cached = cache_get('forecast', CACHE_TTL)
    if cached:
        return cached

    data = await get_json(FORECAST_URL, {
        'lat': LAT, 'lon': LON,
        'appid': OWM_API_KEY,
        'units': 'metric', 'lang': 'es',
    })

    tz = ZoneInfo(TZ)
    days = {}
    for item in data['list']:
        dt = datetime.fromtimestamp(item['dt'], tz)
        dk = dt.strftime('%Y-%m-%d')
        if dk not in days:
            days[dk] = {'t': [], 'd': [], 'i': []}
        days[dk]['t'].append(item['main']['temp'])
        days[dk]['d'].append(item['weather'][0]['description'])
        days[dk]['i'].append(item['weather'][0]['icon'])

    result = []
    for dk in sorted(days.keys())[:5]:
        d = days[dk]
        dt = datetime.strptime(dk, '%Y-%m-%d').replace(tzinfo=tz)
        desc = Counter(d['d']).most_common(1)[0][0].capitalize()
        icon = Counter(d['i']).most_common(1)[0][0]
        result.append({
            'dt': dt,
            'min': round(min(d['t'])),
            'max': round(max(d['t'])),
            'desc': desc,
            'emoji': _emoji(icon),
        })

    cache_set('forecast', result)
    return result
