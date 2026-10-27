"""Модуль 07 в двойнике (spec 21a): чистые функции осей, стека правил, выхода и обхода.

Без состояния и без случайности. Состояние и журнал — в model.py (evolution_step).
"""
from math import ceil

RULE_TARGET = {3: "Хранители", 5: "Хищники", 6: "Контролёры", 7: "Хранители", 8: "Дрейфующие"}


def clamp(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, x))


def axis_r(p, days_supply, manpower):
    if manpower == 0:
        return 0.0
    return clamp(100.0 * min(days_supply, 999.0) / p.evo_r_full_days)


def axis_p(p, shock, tshock=0.0):
    return clamp(p.evo_p_scale * (shock + tshock))


def fires(p, rule, r, pp, c, m, asset, arche=None, owns=True):
    if rule == 3:
        return m < p.evo_rule3_m and c > p.evo_rule3_c
    if rule == 5:
        return r < p.evo_rule5_r and pp > p.evo_rule5_p
    if rule == 6:
        return asset and c > p.evo_rule6_c
    if rule == 7:
        if p.evo_drifter_needs_site and arche == "Дрейфующие" and not owns:
            return False
        return r > p.evo_rule7_r and pp < p.evo_rule7_p
    if rule == 8:
        return m < p.evo_rule8_m
    raise ValueError(rule)


def first_rule(p, r, pp, c, m, asset, arche=None, owns=True):
    for rule in p.evo_rule_order:
        if fires(p, rule, r, pp, c, m, asset, arche, owns):
            return rule
    return None


def exit_open(p, arche, r, pp, c, asset, m=100.0):
    """Шаг 3 фазы 5: условие выхода из текущего уклада (гистерезис)."""
    if not p.evo_hysteresis:
        return True
    if arche == "Хищники":
        return r > p.evo_exit_pred_r or pp < p.evo_exit_pred_p
    if arche == "Хранители":
        return r < p.evo_exit_guard_r or pp > p.evo_exit_guard_p
    if arche == "Контролёры":
        return (not asset) or c < p.evo_exit_ctrl_c or m < p.evo_rule3_m   # коллапс морали открывает выход, иначе бунт (правило 3) недостижим у Контролёров
    return True   # Дрейфующие: выход открыт (решение Стана, intent 21 вопрос 3)


def dwell(p, rule):
    return max(1, ceil(p.evo_dwell[rule] * p.evo_dwell_scale))


def walk(p, step=5):
    """Обход стека (модуль 11, полосы достижимости): по сетке осей.
    Возвращает {правило: dict(any=число точек, где срабатывает, first=число точек, где срабатывает первым,
    band_any=(min M, max M) где срабатывает, band_first=(min M, max M) где срабатывает первым)}."""
    pts = range(0, 101, step)
    out = {x: dict(any=0, first=0, band_any=None, band_first=None) for x in p.evo_rule_order}

    def widen(b, m):
        return (m, m) if b is None else (min(b[0], m), max(b[1], m))

    for r in pts:
        for pp in pts:
            for c in pts:
                for m in pts:
                    for asset in (False, True):
                        hit = [x for x in p.evo_rule_order if fires(p, x, r, pp, c, m, asset)]
                        for x in hit:
                            out[x]["any"] += 1
                            out[x]["band_any"] = widen(out[x]["band_any"], m)
                        if hit:
                            out[hit[0]]["first"] += 1
                            out[hit[0]]["band_first"] = widen(out[hit[0]]["band_first"], m)
    return out


def shadowed(p):
    """Правила, у которых полоса по M, где они срабатывают первыми, уже полосы, где они срабатывают вообще (затенение, в том числе частичное)."""
    w = walk(p)
    return sorted(x for x, d in w.items() if d["any"] > 0 and d["band_first"] != d["band_any"])


def dead(p):
    w = walk(p)
    return sorted(x for x, d in w.items() if d["any"] == 0)
