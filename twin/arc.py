"""Задача 18: личная арка — чистая арифметика вёдер арки (spec 18)."""
from math import floor

STEADY, ORDINARY, SKITTISH = "steady", "ordinary", "skittish"


def promote(before, after, hard, brk, p):
    """before/after — составы (steady, ordinary, skittish) до и после штурма; hard {"steady","ordinary"}, brk {"skittish"} — вёдра арки.
    Возвращает (hard', brk', тяжёлые ярусы). Выжившие без метки переезжают долей; помеченные не считаются (spec 18 §1.3)."""
    hard, brk = dict(hard), dict(brk)
    heavy = []
    names = (STEADY, ORDINARY, SKITTISH)
    for i, name in enumerate(names):
        b, a = before[i], after[i]
        if b <= 0:
            continue
        if (b - a) / b >= p.arc_severe_loss - 1e-12:
            heavy.append(name)
            marked = (brk if name == SKITTISH else hard).get(name, 0)
            free = a if p.arc_count_marked else max(0, a - marked)
            share = {STEADY: p.arc_harden_steady, ORDINARY: p.arc_harden_ordinary, SKITTISH: p.arc_break_skittish}[name]
            n = floor(share * free + 1e-9)
            if name == SKITTISH:
                brk[name] = brk.get(name, 0) + n
            else:
                hard[name] = hard.get(name, 0) + n
    return hard, brk, heavy


def clamp(comp, hard, brk, enabled=True):
    """Инвариант n1 ≤ steady, n2 ≤ ordinary, n3 ≤ skittish (spec 18 §1.2)."""
    if not enabled:
        return dict(hard), dict(brk)
    return ({STEADY: min(hard.get(STEADY, 0), comp[0]), ORDINARY: min(hard.get(ORDINARY, 0), comp[1])}, {SKITTISH: min(brk.get(SKITTISH, 0), comp[2])})


def factor(hard, brk, manpower, p):
    if manpower <= 0:
        return 1.0
    vet = (hard.get(STEADY, 0) + hard.get(ORDINARY, 0)) / manpower
    bk = brk.get(SKITTISH, 0) / manpower
    return 1 + p.arc_vet_w * vet - p.arc_brk_w * bk
