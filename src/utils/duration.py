"""
Utilidades para parsear duraciones expresadas de forma humana.

Soporta formatos:
- Enteros o floats con unidad: "15m", "2h", "1d"
- Múltiples segmentos: "1h30m", "2d 3h", "90m"
- Palabras completas: "minutes", "hours", "days" (y sus variantes en español)
- Valores numéricos sin unidad: se interpretan según default_unit (por defecto minutos)

Retorna segundos (int).
"""

from __future__ import annotations

import re
from typing import Any

_UNITS = {
    "s": 1,
    "sec": 1,
    "second": 1,
    "seconds": 1,
    "seg": 1,
    "segundo": 1,
    "segundos": 1,

    "m": 60,
    "min": 60,
    "mins": 60,
    "minute": 60,
    "minutes": 60,
    "minuto": 60,
    "minutos": 60,

    "h": 3600,
    "hr": 3600,
    "hrs": 3600,
    "hour": 3600,
    "hours": 3600,
    "hora": 3600,
    "horas": 3600,

    "d": 86400,
    "day": 86400,
    "days": 86400,
    "dia": 86400,
    "días": 86400,
    "dias": 86400,
}

_SEGMENT_RE = re.compile(r"(?P<value>\d+(?:[\.,]\d+)?)(?:\s*(?P<unit>[a-zA-ZáéíóúñÁÉÍÓÚ]+))?")


def parse_duration_to_seconds(value: Any, default_unit: str = "m") -> int:
    """
    Parsea una duración y devuelve los segundos.

    value puede ser:
      - int/float: interpretado con default_unit
      - str: puede contener múltiples segmentos, p.ej. "1h 30m" o "2d3h"

    default_unit: unidad por defecto para valores sin unidad ("s", "m", "h", "d").
    """
    if value is None:
        return 0

    # Si es numérico, interpretar con la unidad por defecto
    if isinstance(value, (int, float)):
        factor = _UNITS.get(default_unit.lower(), 60)
        return int(float(value) * factor)

    if not isinstance(value, str):
        # Cualquier otro tipo no reconocido -> 0 segundos
        return 0

    text = value.strip().lower()
    if not text:
        return 0

    total_seconds = 0
    for m in _SEGMENT_RE.finditer(text):
        raw_v = m.group("value")
        raw_u = (m.group("unit") or "").lower().strip()

        # Normalizar coma decimal a punto
        try:
            num = float(raw_v.replace(",", "."))
        except ValueError:
            continue

        # Unidad: si no hay, usar la por defecto
        unit_key = raw_u or default_unit
        # Quitar plural simple en inglés (s) si aplica, pero ya tenemos variantes
        unit_key = unit_key.rstrip(".")
        factor_val: int | None = _UNITS.get(unit_key)
        if factor_val is None:
            # Intento con primeras letras comunes (p.ej., "hs" -> "h")
            # y sin acentos
            simplified = unit_key.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
            factor_val = _UNITS.get(simplified)
        if factor_val is None:
            # Si sigue sin reconocerse, usar default_unit
            factor_val = _UNITS.get(default_unit.lower(), 60)

        # factor_val ahora es int garantizado
        total_seconds += int(num * factor_val)

    return total_seconds


__all__ = ["parse_duration_to_seconds"]
