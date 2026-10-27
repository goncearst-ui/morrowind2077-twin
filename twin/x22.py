"""Задача 22: мир «всё включено» (spec 22). Сценарии IG1–IG7, обратные R145–R149. Двойник; Creation Kit не описывает."""
import json
from dataclasses import replace
from pathlib import Path

from . import integration as I
from . import scenarios as S
from .params import Params

IG = ("IG1", "IG2", "IG3", "IG4", "IG5", "IG6", "IG7")
ROOT = Path(__file__).resolve().parent.parent
WANT = ("assault", "war_declared", "archetype_change", "leader_killed", "objective_done", "interrogation")   # события IG5


def _all_off(p):
    """Все выключатели, выключенные по умолчанию, выключены явно (прежний мир)."""
    return replace(p, **{f: False for f in I.flags() if not getattr(Params(), f)})


def build(sc):
    def f(p):
        if sc == "IG4":
            w, h = S.build("DS1", _all_off(p))
            return w, h
        w, h, _ = I.everything(p)
        I.instrument(w)
        return w, h
    return f


def _chk(sc):
    def f(w, series):
        res = []
        ok = lambda n, c, d: res.append((n, bool(c), d))
        p = w.p
        if sc == "IG1":
            bad = w.ig_bad
            ok("инварианты (а)–(д) на каждом из 1000 тиков в мире «всё включено»", w.tick == 1000 and not bad, f"тиков {w.tick}, нарушений {len(bad)}: {bad[:2]}")
        elif sc == "IG2":
            q, h, _ = I.everything(p)
            for _ in range(h):
                q.step()
            ok("два прогона мира «всё включено» дают идентичные журналы", q.log == w.log and len(w.log) > 1000, f"строк {len(w.log)} и {len(q.log)}")
        elif sc == "IG3":
            t = I.table(p)
            red = [(r["flag"], r["red"], r["first_red"]) for r in t["rows"] if r["red"]]
            ok(f"при выключении любого одного флага (из {len(I.flags())}) инварианты выполняются", not red and len(t["rows"]) == len(I.flags()), f"прогонов {len(t['rows'])}, красных: {red[:3]}")
        elif sc == "IG4":
            base = json.loads((ROOT / "tests" / "baseline_pre19.json").read_text(encoding="utf-8"))["DS1"]
            ok("все выключатели выключены явно: журнал DS1 совпадает с эталоном tests/baseline_pre19.json строка в строку", [list(r) for r in w.log] == base, f"строк {len(w.log)} и {len(base)}")
        elif sc == "IG5":
            k = I.kinds(w)
            dead = [n for n, fx in w.factions.items() if fx.manpower == 0]
            miss = [x for x in WANT if not k[x]]
            ok("за 1000 тиков есть штурм, война, смена уклада, смена вожака, достигнутая цель, допрос; вымерших не больше одной", not miss and len(dead) <= 1, f"нет событий: {miss}; вымерших {dead}; {dict((x, k[x]) for x in WANT)}")
        elif sc == "IG6":
            t = I.table(p)
            text = I.render(p)
            want = I.flags()
            rows = [ln for ln in text.splitlines() if ln.startswith("| ") and ln.split("|")[1].strip() in want]
            miss = [x for x in want if not any(ln.split("|")[1].strip() == x for ln in rows)]
            nums = [r["flag"] for r in t["rows"] if not any(ch.isdigit() for ch in I.recommend(r))]
            path = ROOT / I.TABLE_PATH
            fresh = path.exists() and path.read_text(encoding="utf-8") == text
            ok("reports/22-flag-table.md есть, актуален, содержит строку на каждый флаг; у каждой рекомендации есть число", not miss and not nums and fresh,
               f"флагов {len(want)}, строк {len(rows)}, нет строк: {miss}, без числа: {nums}, файл {'актуален' if fresh else 'отсутствует или устарел (python3 -m twin.integration --write)'}")
        elif sc == "IG7":
            t = I.table(p)
            a, b = len(t["base"].log), len(t["none"].log)
            ok("строк журнала с флагами не больше 20 × строк без флагов", a <= 20 * b and b > 0, f"с флагами {a}, без флагов {b}, рост ×{a / max(1, b):.2f}")
        return res
    return f


for _sc in IG:
    S.EXTRA[_sc] = (build(_sc), _chk(_sc))

S.REVERSE_EXTRA.update({
    "R145": (replace(Params(), ig_bug_people=True), ("IG1",), "тайный прирост людей"),
    "R146": (replace(Params(), ig_bug_nolog=True), ("IG1",), "поле меняется без строки журнала"),
    "R147": (replace(Params(), ig_bug_table_skip=True), ("IG6",), "таблица пропускает флаг"),
    "R148": (replace(Params(), ig_bug_random=True), ("IG1",), "вызов случайности в прогоне"),
    "R149": (replace(Params(), ig_bug_nocap=True), ("IG1",), "потолок активных целей снят"),
})
