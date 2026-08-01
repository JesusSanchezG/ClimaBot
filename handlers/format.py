DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

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
