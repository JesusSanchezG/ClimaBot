# BotClima 🤖🌤️

Bot de Telegram que muestra el clima de **El Paraíso, Mexicali, Baja California** y los **sismos de Baja California** (USGS). Navegación por teclado de respuesta en el campo de mensaje, mensaje único auto-actualizable, historial de consultas, pronóstico a 5 días y **alertas automáticas de sismos fuertes en la región**.

## Tecnologías

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.12+ |
| Bot Framework | [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) v22 |
| Clima API | [OpenWeatherMap 2.5](https://openweathermap.org/api) (gratuita) |
| Sismos API | [USGS FDSN Event](https://earthquake.usgs.gov/fdsnws/event/1/) (gratuita, sin API key) |
| HTTP | httpx (async) |
| Base de datos | SQLite (nativo, sin ORM) |
| Cache | Diccionario en memoria con TTL de 5 min |
| Tests | pytest |
| Servicio | systemd (VPS) |

## Estructura

```
BotClima/
├── bot.py               # Entry point: app, polling, job de alertas de sismos
├── config.py            # Variables de entorno y constantes
├── http_client.py       # Cliente HTTP compartido (retries) + cache en memoria
├── weather_api.py       # Cliente OpenWeatherMap
├── earthquakes_api.py   # Cliente USGS FDSN (sismos) + haversine
├── db.py                # SQLite: chat_state, historial y tabla kv (alertas)
├── handlers/
│   ├── __init__.py      # Routing de acciones y handle_text
│   ├── common.py        # Teclados, mensaje único, /start
│   ├── clima.py         # Clima del día, semanal e historial
│   ├── sismos.py        # Consultas de sismos + alertas automáticas
│   └── format.py        # Fechas, emojis de magnitud
├── tests/               # pytest
├── .env                 # Tokens (NO se sube a git)
├── requirements.txt     # Dependencias
├── README.md
└── deploy/
    └── botclima.service # systemd unit para el VPS
```

## Requisitos

- Python 3.12+
- Token de bot de Telegram ([@BotFather](https://t.me/BotFather))
- API Key de [OpenWeatherMap](https://openweathermap.org/api) (gratis)

## Uso en local

```bash
# 1. Clonar
git clone git@github.com:JesusSanchezG/ClimaBot.git BotClima
cd BotClima

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar tokens
nano .env
# TELEGRAM_BOT_TOKEN=tu_token
# OWM_API_KEY=tu_api_key

# 5. Ejecutar
python bot.py
```

## Despliegue en VPS (IONOS)

```bash
# 1. Conectarse al VPS
ssh root@ip-del-vps

# 2. Instalar python3-venv (si no está)
apt update && apt install -y python3-venv

# 3. Clonar
cd /root
git clone git@github.com:JesusSanchezG/ClimaBot.git BotClima

# 4. Entorno virtual y dependencias
cd BotClima
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Configurar tokens
nano .env
# TELEGRAM_BOT_TOKEN=tu_token
# OWM_API_KEY=tu_api_key

# 6. Instalar servicio systemd
cp deploy/botclima.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now botclima

# 7. Verificar
systemctl status botclima
journalctl -u botclima -f
```

## Actualizar el bot

```bash
# En el VPS
cd /root/BotClima
git pull
systemctl restart botclima
journalctl -u botclima -f   # opcional: ver logs
```

## Comandos útiles

```bash
# Ver estado
systemctl status botclima

# Ver logs en tiempo real
journalctl -u botclima -f

# Detener
systemctl stop botclima

# Iniciar
systemctl start botclima

# Reiniciar
systemctl restart botclima
```

## Funcionamiento

- **Botones en el campo de mensaje**: el menú aparece como teclado de respuesta (reply keyboard) en el campo donde se escribe, como en otros bots. El mensaje del menú nunca se edita porque Telegram no permite editar mensajes con teclado de respuesta.
- **Mensaje único**: las respuestas se muestran en un único mensaje auto-actualizable, separado del menú. El submenú de sismos usa botones inline (sí permiten edición). Las consultas de sismos están limitadas a Baja California (M > 1.0) y "Sismos de hoy" muestra todos los del día.
- **Persistencia**: el message_id se guarda en SQLite, sobrevive a reinicios del bot.
- **Cache**: los datos del clima y de los sismos se cachean 5 minutos en memoria para no golpear las APIs innecesariamente. **El escaneo de alertas no usa cache** para detectar eventos nuevos.
- **Historial**: las últimas 10 consultas se guardan por chat y son accesibles desde el menú; los registros más antiguos se eliminan automáticamente.
- **Alertas de sismos**: cada 60 s el bot consulta los sismos en un radio de 30 km de El Paraíso y avisa por mensaje a todos los chats activos cuando hay un sismo nuevo de magnitud ≥ 4.5. El último evento notificado se guarda en la tabla `kv` para no repetir avisos tras un reinicio.

## Variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | — | Token del bot (obligatorio) |
| `OWM_API_KEY` | — | API key de OpenWeatherMap |
| `BOT_LAT` / `BOT_LON` | `32.6172` / `-115.5706` | Coordenadas de referencia |
| `BOT_CIUDAD` | `El Paraíso, Mexicali` | Nombre mostrado |
| `BOT_TZ` | `America/Tijuana` | Zona horaria para horas locales |
| `BOT_DB_PATH` | `botclima.db` | Ruta de la base SQLite |
| `CACHE_TTL` | `300` | TTL del cache (segundos) |
| `HISTORIAL_LIMIT` | `10` | Consultas guardadas por chat |
| `SISMO_RADIUS_KM` | `30` | Radio de la región para alertas |
| `SISMO_ALERT_MAG` | `4.5` | Magnitud mínima para alertar |
| `SISMO_ALERT_INTERVAL` | `60` | Intervalo de escaneo (segundos) |
| `SISMO_BC_MIN_MAG` | `1.0` | Magnitud mínima en consultas de Baja California |
| `SISMO_BC_MINLAT/MAXLAT/MINLON/MAXLON` | `28.0/32.72/-117.2/-112.2` | Bbox de Baja California |

## Tests

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest tests/
```
