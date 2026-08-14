"""Display helpers. Keep arithmetic in analytics; this is presentation only."""

from __future__ import annotations


def usd(value: float | None, places: int = 2) -> str:
    if value is None:
        return "—"
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.{places}f}"


def signed_usd(value: float | None) -> str:
    if value is None:
        return "—"
    if value > 0:
        return f"+{usd(value)}"
    if value < 0:
        return usd(value)
    return usd(0)


def pct(value: float | None, places: int = 2) -> str:
    if value is None:
        return "—"
    return f"{value * 100:.{places}f}%"


def signed_pct(value: float | None, places: int = 2) -> str:
    if value is None:
        return "—"
    prefix = "+" if value > 0 else ""
    return f"{prefix}{pct(value, places)}"


def compact_number(value: float | int | None) -> str:
    if value is None:
        return "—"
    n = float(value)
    abs_n = abs(n)
    for unit, size in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs_n >= size:
            return f"{n / size:.2f}{unit}"
    return f"{n:,.0f}"


def shares(value: int | float | None) -> str:
    if value is None:
        return "—"
    return f"{int(value):,}"
