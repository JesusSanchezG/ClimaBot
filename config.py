import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OWM_API_KEY = os.getenv('OWM_API_KEY')

LAT = 32.6172
LON = -115.5706
CIUDAD = 'El Paraíso, Mexicali'
DB_PATH = 'botclima.db'

CACHE_TTL = 300
HISTORIAL_LIMIT = 10
