import asyncio

import pytest

import earthquakes_api as ea


def test_haversine_zero():
    assert ea.haversine_km(32.6172, -115.5706, 32.6172, -115.5706) == 0.0


def test_haversine_one_degree_lat():
    d = ea.haversine_km(0, 0, 1, 0)
    assert 110.0 < d < 112.0


def test_haversine_mexicali():
    # El Paraíso (32.6172, -115.5706) vs centro de Mexicali (~32.66, -115.47)
    d = ea.haversine_km(32.6172, -115.5706, 32.66, -115.47)
    assert 8.0 < d < 14.0


def test_normalize():
    feature = {
        'id': 'us7000xyz',
        'properties': {
            'mag': 4.5,
            'place': '12 km al NE de Mexicali',
            'time': 1785597896000,
            'felt': 24,
            'alert': 'green',
            'tsunami': 1,
            'url': 'https://earthquake.usgs.gov/earthquakes/eventpage/us7000xyz',
            'status': 'reviewed',
        },
        'geometry': {'coordinates': [-115.3, 32.7, 10.0]},
    }
    e = ea._normalize(feature)
    assert e['mag'] == 4.5
    assert e['place'] == '12 km al NE de Mexicali'
    assert e['depth_km'] == 10.0
    assert e['lat'] == 32.7
    assert e['lon'] == -115.3
    assert e['tsunami'] is True
    assert e['felt'] == 24
    assert e['time'].tzinfo is not None


def test_normalize_without_depth():
    feature = {
        'id': 'x',
        'properties': {'time': 1785597896000, 'mag': 3.0},
        'geometry': {'coordinates': [-115.3, 32.7]},
    }
    e = ea._normalize(feature)
    assert e['depth_km'] is None
    assert e['tsunami'] is False


def _make_feature(eid, mag, t_ms):
    return {
        'id': eid,
        'properties': {'mag': mag, 'place': f'Lugar {eid}', 'time': t_ms, 'tsunami': 0},
        'geometry': {'coordinates': [-115.0, 32.0, 5.0]},
    }


def test_query_builds_params_and_caches(monkeypatch):
    calls = []
    feature = _make_feature('ev1', 4.2, 1000)

    async def fake_get_json(url, params, retries=3):
        calls.append(params)
        return {'features': [feature]}

    monkeypatch.setattr(ea, 'get_json', fake_get_json)

    evs = asyncio.run(ea.get_recent_mexico(1))
    assert len(evs) == 1
    assert evs[0]['id'] == 'ev1'
    assert calls[0]['format'] == 'geojson'
    assert calls[0]['orderby'] == 'time'
    assert calls[0]['limit'] == '1'

    # segunda llamada usa cache, no vuelve a golpear la API
    asyncio.run(ea.get_recent_mexico(1))
    assert len(calls) == 1


def test_region_query_uses_cache_flag(monkeypatch):
    calls = []
    feature = _make_feature('ev2', 3.3, 2000)

    async def fake_get_json(url, params, retries=3):
        calls.append(params)
        return {'features': [feature]}

    monkeypatch.setattr(ea, 'get_json', fake_get_json)

    asyncio.run(ea.get_region_quakes(use_cache=False))
    asyncio.run(ea.get_region_quakes(use_cache=False))
    assert len(calls) == 2
    assert calls[0]['latitude'] == '32.6172'
    assert 'maxradiuskm' in calls[0]
