import asyncio
import time
import httpx

UA = 'BotClima/1.0 (bot de clima y sismos para Telegram)'
_cache = {}

def cache_get(key, ttl):
    now = time.monotonic()
    entry = _cache.get(key)
    if entry and (now - entry['ts']) < ttl:
        return entry['val']
    return None

def cache_set(key, val):
    _cache[key] = {'val': val, 'ts': time.monotonic()}

async def get_json(url, params, retries=3):
    last_err = None
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=10, headers={'User-Agent': UA}) as client:
                r = await client.get(url, params=params)
                r.raise_for_status()
                return r.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500 or attempt == retries - 1:
                raise
            last_err = e
        except httpx.TransportError as e:
            last_err = e
        await asyncio.sleep(0.5 * (2 ** attempt))
    raise last_err
