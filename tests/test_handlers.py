from datetime import datetime
from zoneinfo import ZoneInfo

from handlers.common import ACTIONS, LABELS, _reply_kb
from handlers.format import _fecha, _mag_emoji, translate_place


def test_mag_emoji():
    assert _mag_emoji(None) == '🌡'
    assert _mag_emoji(3.2) == '🟢'
    assert _mag_emoji(4.5) == '🟡'
    assert _mag_emoji(5.8) == '🟠'
    assert _mag_emoji(7.1) == '🔴'


def test_fecha():
    dt = datetime(2026, 8, 1, 14, 30, tzinfo=ZoneInfo('UTC'))
    assert _fecha(dt) == 'sábado, 1 de agosto de 2026'


def test_translate_place():
    assert translate_place('18 km WNW of Progreso, B.C., MX') == '18 km al Oeste-Noroeste de Progreso, Baja California, México'
    assert translate_place('5 km N of Progreso, B.C., MX') == '5 km al Norte de Progreso, Baja California, México'
    assert translate_place('30 km SSE of La Paz, B.C.S., MX') == '30 km al Sur-Sureste de La Paz, Baja California Sur, México'
    assert translate_place('12 km ENE of San Felipe, B.C., MX') == '12 km al Este-Noreste de San Felipe, Baja California, México'


def test_translate_place_without_distance():
    assert translate_place('Los Angeles, CA') == 'Los Angeles, California'
    assert translate_place('') == ''


def test_actions_cover_labels():
    for label in LABELS:
        assert label.lower() in ACTIONS, label


def test_actions_return_valid():
    for key, action in ACTIONS.items():
        assert action in {'clima_dia', 'clima_semanal', 'historial', 'sismos', 'menu'}, action


def test_reply_kb_rows():
    kb = _reply_kb()
    flat = [btn.text for row in kb.keyboard for btn in row]
    assert flat == LABELS
    assert kb.resize_keyboard is True
