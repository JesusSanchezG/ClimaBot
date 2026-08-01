from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import math

from config import LAT, LON, TZ, CACHE_TTL, SISMO_MEX_BBOX, SISMO_MEX_MIN_MAG, SISMO_RADIUS_KM
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

async def get_recent_mexico(limit=5):
    return await _query({
        **_bbox_params(SISMO_MEX_BBOX),
        'minmagnitude': str(SISMO_MEX_MIN_MAG),
        'orderby': 'time',
        'limit': str(limit),
    }, cache_key='sismo_recent')

async def get_strongest_today():
    start = (datetime.now(UTC) - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S')
    return await _query({
        **_bbox_params(SISMO_MEX_BBOX),
        'starttime': start,
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
