# BotClima 🤖🌤️

Bot de Telegram que muestra el clima de **El Paraíso, Mexicali, Baja California**. Navegación exclusiva por botones, mensaje único auto-actualizable, historial de consultas y pronóstico a 5 días.

## Tecnologías

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.12+ |
| Bot Framework | [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) v22 |
| Clima API | [OpenWeatherMap 2.5](https://openweathermap.org/api) (gratuita) |
| HTTP | httpx (async) |
| Base de datos | SQLite (nativo, sin ORM) |
| Cache | Diccionario en memoria con TTL de 5 min |
| Servicio | systemd (VPS) |

## Estructura

```
BotClima/
├── bot.py               # Entry point, configura la app e inicia polling
├── config.py            # Variables de entorno y constantes
├── db.py                # SQLite: chat_state (message_id) + historial
├── weather_api.py       # Cliente OpenWeatherMap + cache en memoria
├── handlers.py          # Botones, formato de mensajes, borrado de texto
├── .env                 # Tokens (NO se sube a git)
├── requirements.txt     # Dependencias
├── .gitignore
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
- **Mensaje único**: las respuestas se muestran en un único mensaje auto-actualizable, separado del menú.
- **Persistencia**: el message_id se guarda en SQLite, sobrevive a reinicios del bot.
- **Cache**: los datos del clima se cachean 5 minutos en memoria para no golpear la API innecesariamente.
- **Historial**: las últimas 10 consultas se guardan por chat y son accesibles desde el menú; los registros más antiguos se eliminan automáticamente.
