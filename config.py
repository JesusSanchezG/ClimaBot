import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OWM_API_KEY = os.getenv('OWM_API_KEY')

LAT = float(os.getenv('BOT_LAT', '32.6172'))
LON = float(os.getenv('BOT_LON', '-115.5706'))
CIUDAD = os.getenv('BOT_CIUDAD', 'El Paraíso, Mexicali')
TZ = os.getenv('BOT_TZ', 'America/Tijuana')
DB_PATH = os.getenv('BOT_DB_PATH', 'botclima.db')

CACHE_TTL = int(os.getenv('CACHE_TTL', '300'))
HISTORIAL_LIMIT = int(os.getenv('HISTORIAL_LIMIT', '10'))

SISMO_RADIUS_KM = int(os.getenv('SISMO_RADIUS_KM', '30'))
SISMO_ALERT_MAG = float(os.getenv('SISMO_ALERT_MAG', '4.5'))
SISMO_ALERT_INTERVAL = int(os.getenv('SISMO_ALERT_INTERVAL', '60'))
SISMO_MEX_MIN_MAG = float(os.getenv('SISMO_MEX_MIN_MAG', '1.0'))
SISMO_MEX_BBOX = {
    'minlat': float(os.getenv('SISMO_MEX_MINLAT', '14')),
    'maxlat': float(os.getenv('SISMO_MEX_MAXLAT', '33')),
    'minlon': float(os.getenv('SISMO_MEX_MINLON', '-118')),
    'maxlon': float(os.getenv('SISMO_MEX_MAXLON', '-86')),
}
