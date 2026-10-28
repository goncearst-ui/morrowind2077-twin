"""Задача 23a: журнал в два уровня (spec 23). Сценарии LG1–LG5, обратные R150–R152. Двойник; Creation Kit не описывает."""
import json
from dataclasses import replace
from pathlib import Path

from . import integration as I
from . import scenarios as S
from .params import Params

LG = ("LG1", "LG2", "LG3", "LG4", "LG5")
ROOT = Path(__file__).resolve().parent.parent


def _flat(p):
    """Тот же мир при плоском журнале (все lg_bug_* сбрасываются: они касаются только режима двух уровней)."""
    return replace(p, log_two_level_enabled=False, lg_bug_named_summary=False, lg_bug_drop_sum=False, lg_bug_affects_world=False)


def build(sc):
    def f(p):
        if sc == "LG1":
            return S.build("DS1", _flat(p))
        w, h, _ = I.everything(replace(p, log_two_level_enabled=True))
        return w, h
    return f


# ---- оракул: независимая от model.py запись правил классификации ----
def ref_detail(p, target, reason):
    return (".named." in target or reason in p.disputed_reasons or any(reason.startswith(x) for x in p.disputed_prefixes)
            or any(target.endswith(x) for x in p.disputed_target_suffixes) or "hegemon" in target)


def ref_class(w, target):
    parts = target.split(".")
    h = parts[0]
    if h in w.factions:
        parts[0] = "F"
    elif ">" in h:
        parts[0] = "pair"
    elif h in ("site", "region") and len(parts) > 1:
        parts[1] = "X"
    elif h in w.regions:
        parts[0] = "R"
    return ".".join(parts)


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _expected(w, flat_rows):
    p = w.p
    detail = [r for r in flat_rows if ref_detail(p, r[3], r[6])]
    summ = {}
    for r in flat_rows:
        if ref_detail(p, r[3], r[6]):
            continue
        key = (r[0] - r[0] % p.log_sum_window, r[2], ref_class(w, r[3]), r[6], "main")
        e = summ.setdefault(key, [0, 0, 0])
        e[0] += 1
        if _num(r[4]) and _num(r[5]):
            e[1] = round(e[1] + (r[5] - r[4]), 4)
        else:
            e[2] += 1
    return detail, summ


_CACHE = {}


def _pair(w):
    """Плоский прогон того же мира; кэш по параметрам, чтобы пять проверок не гоняли его пять раз."""
    key = repr(w.p)
    if key not in _CACHE:
        q, h, _ = I.everything(_flat(w.p))
        for _ in range(h):
            q.step()
        _CACHE.clear()
        _CACHE[key] = q
    return _CACHE[key]


def _chk(sc):
    def f(w, series):
        res = []
        ok = lambda n, c, d: res.append((n, bool(c), d))
        if sc == "LG1":
            base = json.loads((ROOT / "tests" / "baseline_pre23a.json").read_text(encoding="utf-8"))["DS1"]
            ok("при log_two_level_enabled = False журнал DS1 совпадает с эталоном tests/baseline_pre23a.json строка в строку и сводного уровня нет",
               [list(r) for r in w.log] == base and not w.log_sum, f"строк {len(w.log)} и {len(base)}, сводных записей {len(w.log_sum)}")
            return res
        q = _pair(w)
        det, summ = _expected(w, q.log)
        if sc == "LG2":
            named_flat = sum(1 for r in q.log if ".named." in r[3])
            named_two = sum(1 for r in w.log if ".named." in r[3])
            ok("подробные строки режима «два уровня» = строки плоского журнала с именными и спорными причинами, в том же порядке; все строки именных на месте",
               w.log == det and named_flat > 0 and named_two == named_flat,
               f"подробных {len(w.log)} из ожидаемых {len(det)}, именных {named_two} из {named_flat}")
        elif sc == "LG3":
            tot_flat = round(sum(r[5] - r[4] for r in q.log if _num(r[4]) and _num(r[5])), 2)
            tot_two = round(sum(r[5] - r[4] for r in w.log if _num(r[4]) and _num(r[5])) + sum(e[1] for e in w.log_sum.values()), 2)
            ok("каждая сводная запись равна сумме строк плоского журнала по её ключу (число, сумма разностей); общая сумма разностей совпадает",
               w.log_sum == summ and tot_flat == tot_two and len(summ) > 0,
               f"сводных записей {len(w.log_sum)} из ожидаемых {len(summ)}, сумма разностей плоский {tot_flat} и два уровня {tot_two}")
        elif sc == "LG4":
            same = (repr(w.factions) == repr(q.factions) and repr(w.sites) == repr(q.sites) and w.regions == q.regions
                    and w.events == q.events and w.tick == q.tick and repr(w.rel) == repr(q.rel) and w.hegemon == q.hegemon)
            ok("состояние мира на тике 1000 при двух режимах журнала идентично", same, f"тик {w.tick}")
        elif sc == "LG5":
            two = len(w.log) + len(w.log_sum)
            ok("подробных + сводных записей не больше 30% строк плоского журнала [предл]", two <= 0.30 * len(q.log),
               f"плоский {len(q.log)}, два уровня {two} (подробных {len(w.log)}, сводных {len(w.log_sum)}), доля {100.0 * two / max(1, len(q.log)):.1f}%")
        return res
    return f


for _sc in LG:
    S.EXTRA[_sc] = (build(_sc), _chk(_sc))

_ON = replace(Params(), log_two_level_enabled=True)
S.REVERSE_EXTRA.update({
    "R150": (replace(_ON, lg_bug_named_summary=True), ("LG2",), "строки именных уходят в сводный уровень"),
    "R151": (replace(_ON, lg_bug_drop_sum=True), ("LG3",), "сводная запись теряется"),
    "R152": (replace(_ON, lg_bug_affects_world=True), ("LG4",), "запись журнала меняет состояние мира"),
})
