"""Задача 16a: цель лидера и ключевые результаты (spec 16a). Чистые функции над миром: ничего не пишут."""

NAMES = {0: "ВЫЖИВАНИЕ", 1: "МОНОПОЛИЯ_УЗЛА", 2: "АВТАРКИЯ", 3: "ГЕГЕМОНИЯ", 4: "ИСХОД", 5: "ОСВОБОЖДЕНИЕ"}
OPS = {">": lambda a, b: a > b, ">=": lambda a, b: a >= b, "<": lambda a, b: a < b, "<=": lambda a, b: a <= b}


def is_active(f, obj):
    """Активные цели — 1, 3, 4, 5; пассивные — 0, и 2 при доктрине 2 [док 16]."""
    return obj in (1, 3, 4, 5) or (obj == 2 and f.doctrine != 2)


def duration_kr(kr):
    return kr[0] in ("hold", "rival_supply_low")


def _metric(w, f, name):
    if name == "ctl":
        return f.ctl
    if name == "days_supply":
        return f.days_supply
    if name == "manpower_ratio":
        return f.manpower / f.obj_start["mp"] if f.obj_start.get("mp") else None
    raise ValueError(f"неизвестная метрика KR: {name}")


def cond(w, f, kr):
    """Мгновенное условие KR (для видов с длительностью — условие, которое накапливает счётчик)."""
    k = kr[0]
    rival = w.factions.get(f.obj_rival) if f.obj_rival else None
    if k == "owns":
        return bool(f.obj_target) and w.site(f.obj_target).owner == f.name
    if k == "hold":
        v = _metric(w, f, kr[1])
        return v is not None and OPS[kr[2]](v, kr[3])
    if k == "rival_below":
        return rival is not None and f.obj_rival_start > 0 and rival.manpower < kr[1] * f.obj_rival_start
    if k == "rival_supply_low":
        return rival is not None and rival.days_supply < kr[1]
    if k == "prosperity_at_least":
        return w.regions[f.home] >= kr[1]
    if k == "rival_arch":
        return rival is not None and (rival.archetype in kr[1] or (f.name, rival.name) in w.p.obj_vassal_pairs)
    if k == "manpower_ratio_at_least":
        return bool(f.obj_start.get("mp")) and f.manpower / f.obj_start["mp"] >= kr[1]
    if k == "supply_at_least":
        return f.days_supply >= kr[1]
    if k == "mp_up_c_not_up":
        return bool(f.obj_start) and f.manpower > f.obj_start["mp"] and f.ctl is not None and f.ctl <= f.obj_start["ctl"]
    raise ValueError(f"неизвестный вид KR: {k}")
