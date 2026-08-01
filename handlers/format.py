import re

DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

_DIRS = {
    'N': 'Norte', 'S': 'Sur', 'E': 'Este', 'W': 'Oeste',
    'NE': 'Noreste', 'NW': 'Noroeste', 'SE': 'Sureste', 'SW': 'Suroeste',
    'NNE': 'Nor-Noreste', 'ENE': 'Este-Noreste', 'ESE': 'Este-Sureste', 'SSE': 'Sur-Sureste',
    'SSW': 'Sur-Suroeste', 'WSW': 'Oeste-Suroeste', 'WNW': 'Oeste-Noroeste', 'NNW': 'Nor-Noroeste',
}

_REGIONS = {
    'B.C.': 'Baja California',
    'B.C.S.': 'Baja California Sur',
    'BC': 'Baja California',
    'SON': 'Sonora',
    'MX': 'México',
    'MEX': 'México',
    'Mexico': 'México',
    'CA': 'California',
    'AZ': 'Arizona',
    'NV': 'Nevada',
    'USA': 'EE.UU.',
    'United States': 'EE.UU.',
}

_PLACE_RE = re.compile(r'^(?P<dist>\d+(?:\.\d+)?)\s*km\s+(?P<dir>[NSEW]{1,3})\s+of\s+(?P<rest>.+)$', re.IGNORECASE)

def _translate_regions(text):
    return ', '.join(_REGIONS.get(p.strip(), p.strip()) for p in text.split(','))

def translate_place(place):
    if not place:
        return place
    m = _PLACE_RE.match(place.strip())
    if m:
        dist = m.group('dist')
        d = _DIRS.get(m.group('dir').upper(), m.group('dir').upper())
        return f'{dist} km al {d} de {_translate_regions(m.group("rest"))}'
    return _translate_regions(place)

def _fecha(dt):
    return f"{DIAS[dt.weekday()]}, {dt.day} de {MESES[dt.month - 1]} de {dt.year}"

def _mag_emoji(mag):
    if mag is None:
        return '🌡'
    if mag < 4:
        return '🟢'
    if mag < 5:
        return '🟡'
    if mag < 6:
        return '🟠'
    return '🔴'
