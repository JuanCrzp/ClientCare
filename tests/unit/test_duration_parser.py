from src.utils.duration import parse_duration_to_seconds


def test_parse_simple_units():
    assert parse_duration_to_seconds("15m") == 15 * 60
    assert parse_duration_to_seconds("2h") == 2 * 3600
    assert parse_duration_to_seconds("1d") == 86400


def test_parse_multiple_segments():
    assert parse_duration_to_seconds("1h 30m") == 5400
    assert parse_duration_to_seconds("2d3h") == 2 * 86400 + 3 * 3600


def test_parse_numeric_default_unit_minutes():
    assert parse_duration_to_seconds(30) == 1800
    assert parse_duration_to_seconds("45") == 2700


def test_spanish_units():
    assert parse_duration_to_seconds("1 hora") == 3600
    assert parse_duration_to_seconds("2 dias") == 2 * 86400
    assert parse_duration_to_seconds("10 minutos") == 600


def test_invalid_values():
    assert parse_duration_to_seconds(None) == 0
    assert parse_duration_to_seconds(0) == 0
    assert parse_duration_to_seconds("xyz") == 0
