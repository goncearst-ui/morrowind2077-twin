"""Задача 23b: именные из фиксированного списка (spec 23). Без случайности и без продвижения из вёдер [решение Стана 2026-10-28]."""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data" / "named_roster.json"
_TABLE = None


def table():
    """Фиксированный список именных (twin/data/named_roster.json): роль, профиль, трейты по порядку; 25 мест."""
    global _TABLE
    if _TABLE is None:
        _TABLE = json.loads(DATA.read_text(encoding="utf-8"))
    return _TABLE


def named_roster(fname, n, p=None):
    """Первые n мест списка для фракции fname: вожак, преемники, офицеры; имена как у roster() (twin/scenarios.py).
    n не больше p.named_max (если p задан) и не больше длины списка."""
    rows = table()
    if p is not None and p.nn_bug_roster_cap:
        n = min(n, 10)                      # R154: параметр численности игнорируется выше 10
    if n > len(rows):
        raise ValueError(f"в списке именных {len(rows)} мест, запрошено {n}")
    if p is not None and n > p.named_max:
        raise ValueError(f"именных {n} больше named_max {p.named_max} (spec 23b)")
    out, si, oi = [], 0, 0
    for r in rows[:n]:
        if r["role"] == "вожак":
            name = f"{fname}:вожак"
        elif r["role"] == "преемник":
            si += 1
            name = f"{fname}:преемник{si}"
        else:
            oi += 1
            name = f"{fname}:офицер{oi}"
        out.append(dict(name=name, role=r["role"], profile=r["profile"], alive=True, traits=tuple(r["traits"])))
    return out
