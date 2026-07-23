from datetime import datetime
from collections import Counter
import time
import httpx

from config import OWM_API_KEY, LAT, LON, CACHE_TTL

CURRENT_URL = 'https://api.openweathermap.org/data/2.5/weather'
FORECAST_URL = 'https://api.openweathermap.org/data/2.5/forecast'

_cache = {}

def _cached(key, ttl=CACHE_TTL):
    now = time.monotonic()
    if key in _cache and (now - _cache[key]['ts']) < ttl:
        return _cache[key]['val']
    return None

def _set_cache(key, val):
    _cache[key] = {'val': val, 'ts': time.monotonic()}

ICON_MAP = {
    '01': '☀️', '02': '🌤', '03': '⛅', '04': '☁️',
    '09': '🌧', '10': '🌦', '11': '⛈', '13': '❄️', '50': '🌫',
}

def _emoji(icon):
    return ICON_MAP.get(icon[:2], '🌡')

async def _get(url, params):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json()

async def get_current():
    cached = _cached('current')
    if cached:
        return cached

    data = await _get(CURRENT_URL, {
        'lat': LAT, 'lon': LON,
        'appid': OWM_API_KEY,
        'units': 'metric', 'lang': 'es',
    })

    now = datetime.now()
    r = {
        'temp': data['main']['temp'],
        'feels_like': data['main']['feels_like'],
        'humidity': data['main']['humidity'],
        'desc': data['weather'][0]['description'].capitalize(),
        'wind': data['wind']['speed'],
        'emoji': _emoji(data['weather'][0]['icon']),
        'dt': now,
    }
    _set_cache('current', r)
    return r

async def get_forecast():
    cached = _cached('forecast')
    if cached:
        return cached

    data = await _get(FORECAST_URL, {
        'lat': LAT, 'lon': LON,
        'appid': OWM_API_KEY,
        'units': 'metric', 'lang': 'es',
    })

    days = {}
    for item in data['list']:
        dt = datetime.fromtimestamp(item['dt'])
        dk = dt.strftime('%Y-%m-%d')
        if dk not in days:
            days[dk] = {'t': [], 'd': [], 'i': []}
        days[dk]['t'].append(item['main']['temp'])
        days[dk]['d'].append(item['weather'][0]['description'])
        days[dk]['i'].append(item['weather'][0]['icon'])

    result = []
    for dk in sorted(days.keys())[:5]:
        d = days[dk]
        dt = datetime.strptime(dk, '%Y-%m-%d')
        desc = Counter(d['d']).most_common(1)[0][0].capitalize()
        icon = Counter(d['i']).most_common(1)[0][0]
        result.append({
            'dt': dt,
            'min': round(min(d['t'])),
            'max': round(max(d['t'])),
            'desc': desc,
            'emoji': _emoji(icon),
        })

    _set_cache('forecast', result)
    return result
