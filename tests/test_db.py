import asyncio

import pytest

import db


@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'DB_PATH', str(tmp_path / 'test.db'))
    asyncio.run(db.init_db())


def _run(coro):
    return asyncio.run(coro)


def test_history_pruned_to_limit(tmp_db):
    for i in range(12):
        _run(db.add_history(1, float(i), None, None, f'desc {i}', None, 'current'))
    rows = _run(db.get_history(1, 99))
    assert len(rows) == 10
    assert rows[0]['description'] == 'desc 11'
    assert rows[-1]['description'] == 'desc 2'


def test_history_kept_per_chat(tmp_db):
    _run(db.add_history(1, 1.0, None, None, 'a', None, 'current'))
    _run(db.add_history(2, 2.0, None, None, 'b', None, 'current'))
    rows = _run(db.get_history(2))
    assert len(rows) == 1
    assert rows[0]['chat_id'] == 2


def test_kv_roundtrip(tmp_db):
    assert _run(db.kv_get('x')) is None
    _run(db.kv_set('x', 123))
    assert _run(db.kv_get('x')) == '123'
    _run(db.kv_set('x', 456))
    assert _run(db.kv_get('x')) == '456'


def test_chat_state_and_menu(tmp_db):
    _run(db.set_chat_state(5, 100))
    state = _run(db.get_chat_state(5))
    assert state['message_id'] == 100

    _run(db.set_menu_state(5, 200))
    state = _run(db.get_chat_state(5))
    assert state['menu_message_id'] == 200
    assert state['message_id'] is None

    assert _run(db.get_all_chat_ids()) == [5]
