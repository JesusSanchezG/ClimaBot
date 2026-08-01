from datetime import datetime
from zoneinfo import ZoneInfo
import math

from config import LAT, LON, TZ, CACHE_TTL, SISMO_BC_BBOX, SISMO_BC_MIN_MAG, SISMO_RADIUS_KM
from http_client import get_json, cache_get, cache_set

QUERY_URL = 'https://earthquake.usgs.gov/fdsnws/event/1/query'
UTC = ZoneInfo('UTC')
TZ_LOCAL = ZoneInfo(TZ)

def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))

def _normalize(feature):
    p = feature['properties']
    g = feature['geometry']['coordinates']
    return {
        'id': feature['id'],
        'mag': p.get('mag'),
        'place': p.get('place'),
        'depth_km': g[2] if len(g) > 2 else None,
        'lat': g[1],
        'lon': g[0],
        'time': datetime.fromtimestamp(p['time'] / 1000, UTC).astimezone(TZ_LOCAL),
        'felt': p.get('felt'),
        'alert': p.get('alert'),
        'tsunami': p.get('tsunami') == 1,
        'url': p.get('url'),
        'status': p.get('status'),
    }

def _bbox_params(bbox):
    return {
        'minlatitude': str(bbox['minlat']),
        'maxlatitude': str(bbox['maxlat']),
        'minlongitude': str(bbox['minlon']),
        'maxlongitude': str(bbox['maxlon']),
    }

async def _query(params, cache_key=None, ttl=CACHE_TTL):
    if cache_key:
        cached = cache_get(cache_key, ttl)
        if cached:
            return cached
    data = await get_json(QUERY_URL, {
        'format': 'geojson',
        'jsonerror': 'true',
        **params,
    })
    events = [_normalize(f) for f in data.get('features', [])]
    if cache_key:
        cache_set(cache_key, events)
    return events

def _today_start():
    start = datetime.now(TZ_LOCAL).replace(hour=0, minute=0, second=0, microsecond=0)
    return start.astimezone(UTC).strftime('%Y-%m-%dT%H:%M:%S')

async def get_recent_bc(limit=5):
    return await _query({
        **_bbox_params(SISMO_BC_BBOX),
        'minmagnitude': str(SISMO_BC_MIN_MAG),
        'orderby': 'time',
        'limit': str(limit),
    }, cache_key='sismo_recent')

async def get_today_bc(limit=100):
    date = datetime.now(TZ_LOCAL).strftime('%Y-%m-%d')
    return await _query({
        **_bbox_params(SISMO_BC_BBOX),
        'minmagnitude': str(SISMO_BC_MIN_MAG),
        'starttime': _today_start(),
        'orderby': 'time',
        'limit': str(limit),
    }, cache_key=f'sismo_today_{date}')

async def get_strongest_today():
    return await _query({
        **_bbox_params(SISMO_BC_BBOX),
        'starttime': _today_start(),
        'orderby': 'magnitude',
        'limit': '1',
    }, cache_key='sismo_strongest')

async def get_region_quakes(radius_km=SISMO_RADIUS_KM, limit=10, use_cache=False):
    params = {
        'latitude': str(LAT),
        'longitude': str(LON),
        'maxradiuskm': str(radius_km),
        'orderby': 'time',
        'limit': str(limit),
    }
    if use_cache:
        return await _query(params, cache_key='sismo_region')
    return await _query(params)
