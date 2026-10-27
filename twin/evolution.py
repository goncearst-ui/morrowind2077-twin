"""Модуль 07 в двойнике (spec 21a): чистые функции осей, стека правил, выхода и обхода.

Без состояния и без случайности. Состояние и журнал — в model.py (evolution_step).
"""
from math import ceil

RULE_TARGET = {3: "Хранители", 4: "Культисты", 5: "Хищники", 6: "Контролёры", 7: "Хранители", 8: "Дрейфующие", 9: "Regime"}


def clamp(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, x))


def axis_r(p, days_supply, manpower):
    if manpower == 0:
        return 0.0
    return clamp(100.0 * min(days_supply, 999.0) / p.evo_r_full_days)


def axis_p(p, shock, tshock=0.0):
    return clamp(p.evo_p_scale * (shock + tshock))


def fires(p, rule, r, pp, c, m, asset, arche=None, owns=True, force=True):
    if rule == 3:
        return m < p.evo_rule3_m and c > p.evo_rule3_c
    if rule == 4:
        return m < p.evo_rule4_m and pp > p.evo_rule4_p
    if rule == 5:
        if p.evo_rule5_needs_force and not force:
            return False
        return r < p.evo_rule5_r and pp > p.evo_rule5_p
    if rule == 6:
        return asset and c > p.evo_rule6_c
    if rule == 7:
        if p.evo_drifter_needs_site and arche == "Дрейфующие" and not owns:
            return False
        return r > p.evo_rule7_r and pp < p.evo_rule7_p
    if rule == 8:
        return m < p.evo_rule8_m
    if rule == 9:
        return c > p.evo_rule9_c and pp > p.evo_rule9_p and m >= p.evo_rule9_m
    raise ValueError(rule)


def first_rule(p, r, pp, c, m, asset, arche=None, owns=True, force=True):
    for rule in p.evo_rule_order:
        if fires(p, rule, r, pp, c, m, asset, arche, owns, force):
            return rule
    return None


def exit_open(p, arche, r, pp, c, asset, m=100.0, doctrine=0):
    """Шаг 3 фазы 5: условие выхода из текущего уклада (гистерезис).
    Доктрина 1 [док 07]: порог выхода отодвигается от порога входа в doctrine_gap_mult раз дальше; доктрина 2: выход закрыт."""
    if not p.evo_hysteresis:
        return True
    if doctrine == 2 and p.doctrine2_freezes:
        return False
    k = p.doctrine_gap_mult if doctrine == 1 else 1.0

    def thr(entry, exit_):
        return entry + k * (exit_ - entry)

    if arche == "Хищники":
        return r > thr(p.evo_rule5_r, p.evo_exit_pred_r) or pp < thr(p.evo_rule5_p, p.evo_exit_pred_p)
    if arche == "Хранители":
        return r < thr(p.evo_rule7_r, p.evo_exit_guard_r) or pp > thr(p.evo_rule7_p, p.evo_exit_guard_p)
    if arche == "Контролёры":
        return (not asset) or c < thr(p.evo_rule6_c, p.evo_exit_ctrl_c) or m < p.evo_rule3_m   # коллапс морали открывает выход, иначе бунт (правило 3) недостижим у Контролёров
    if arche == "Культисты":
        return m > thr(p.evo_rule4_m, p.evo_exit_cult_m) or pp < thr(p.evo_rule4_p, p.evo_exit_cult_p)
    if arche == "Regime":
        return c < thr(p.evo_rule9_c, p.evo_exit_regime_c) or pp < thr(p.evo_rule9_p, p.evo_exit_regime_p) or m < p.evo_rule9_m   # на дне морали жёсткий контроль ломается [док 07]
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
