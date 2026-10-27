"""Задача 10: стенд сверки озвучки (spec 10). Сценарии LL1–LL9, обратные R136–R140. Модуль только читает мир."""
import re
from dataclasses import replace
from pathlib import Path

from . import scenarios as S
from . import voice as V
from .params import Params

LL = ("LL1", "LL2", "LL3", "LL4", "LL5", "LL6", "LL7", "LL8", "LL9")
CHRON = ("DS1", "DS2", "OB1", "WS1", "EV3", "EV13", "EV24", "PH7", "HC1")   # сценарии, где хроника непуста
WRITE_RX = re.compile(r"\b(setf|rec|player_action)\s*\(")
NET_RX = re.compile(r"^\s*(import|from)\s+(random|secrets|socket|ssl|http|urllib|requests|httpx|aiohttp|asyncio|ftplib|smtplib)\b", re.M)


def _ds1(p, n=100):
    w, _ = S.build("DS1", replace(p, evolution_enabled=False))
    return w, n


def build(sc):
    def f(p):
        if sc in ("LL1", "LL2", "LL4", "LL7", "LL8", "LL9"):
            return _ds1(p)
        if sc == "LL3":
            return _ds1(p, 1)
        if sc == "LL5":
            from . import x19
            return x19._plan("ID2", x19._p(p))
        if sc == "LL6":
            from . import x19
            w = x19._world(x19._p(p))
            S.give_named(w, "F", officers=1)
            w.factions["F"].named[0]["traits"] = ("Neuroticism_Low", "Conscientiousness_High")
            w.factions["F"].named[1]["traits"] = ("Neuroticism_High", "Agreeableness_Low")
            return w, 3
    return f


def _all_texts(w):
    return [(fa, V.render_prompt(V.facts(w, fa)), [(l["text"], l["statement"]) for l in V.stub_voice(w, fa)]) for fa in sorted(w.factions)]


def _chk(sc):
    def f(w, series):
        res = []
        ok = lambda n, c, d: res.append((n, bool(c), d))
        p = w.p
        if sc == "LL1":
            try:
                V.assert_read_only(w, lambda: [(V.facts(w, fa), V.render_prompt(V.facts(w, fa)), V.verify([l["statement"] for l in V.stub_voice(w, fa)], w)) for fa in w.factions])
                err = None
            except AssertionError as e:
                err = str(e)
            ok("facts / render_prompt / stub_voice / verify на мире после 100 тиков не меняют журнал, состояние и события", err is None and w.tick == 100, f"тик {w.tick}, журнал {len(w.log)}, ошибка: {err}")
            def bad_writer():
                w.rec(7, "99", "test", 0, 1, "TEST")
            try:
                V.assert_read_only(w, bad_writer)
                caught = False
            except AssertionError:
                caught = True
                w.log.pop()
            ok("сам assert_read_only ловит запись в журнал", caught, "")
        elif sc == "LL2":
            a, _ = _ds1(p)
            for _ in range(100):
                a.step()
            ok("два вызова на одном мире и два прогона мира дают тот же текст", _all_texts(w) == _all_texts(w) == _all_texts(a), f"фракций {len(w.factions)}")
        elif sc == "LL3":
            q, _ = _ds1(p)
            q.p = replace(q.p, **{k: getattr(p, k) for k in ("voice_bug_facts", "voice_bug_leak_depot")})
            bad = []
            for t in range(1, 201):
                q.step()
                if t in (1, 50, 100, 200):
                    for n, fx in q.factions.items():
                        d = V.facts(q, n)
                        raw = {"archetype": fx.archetype, "doctrine": fx.doctrine, "axis_R": fx.ax_r, "axis_P": fx.ax_p, "axis_C": fx.ctl, "axis_M": fx.morale,
                               "leader": fx.leader, "captured": fx.captured, "tick": q.tick, "faction": n}
                        bad += [(t, n, k, d[k], v) for k, v in raw.items() if d[k] != v]
                        bad += [(t, n, k) for k in d if k.startswith(("know.", "depot.")) and not any((n, s) in q.know for s in [k.split(".", 1)[1]] + [x.depot for x in q.factions.values() if x.depot])]
            ok("каждое утверждение facts совпадает с полем мира на тиках 1, 50, 100, 200 (DS1, все фракции)", not bad, f"расхождений {len(bad)}: {bad[:2]}")
        elif sc == "LL4":
            q = w.factions["A"]
            true_st = ("fact", "A", "archetype", q.archetype)
            lie = ("fact", "A", "archetype", "Хищники" if q.archetype != "Хищники" else "Контролёры")
            ok("подложенное «A — Хищники/Контролёры» при другом архетипе даёт одно расхождение; верное — ноль", len(V.verify([lie], w)) == 1 and V.verify([true_st], w) == [], f"архетип A: {q.archetype}, ложь: {lie[3]}, расхождения: {V.verify([lie], w)}")
        elif sc == "LL5":
            from . import x19
            q = x19._plan("ID2", p)[0]
            for _ in range(2):
                q.step()
            before = V.facts(q, "G")
            after = V.facts(w, "G")
            lie = ("fact", "G", "depot.F", "Склад2")
            leak = ("fact", "G", "depot.F", "Склад")
            ok("склад F не в facts(G), пока know пуст; после допроса (08c) попадает; ложь про чужой склад и утечка без знания ловятся",
               "depot.F" not in before and after.get("depot.F") == "Склад" and len(V.verify([lie], w)) == 1 and len(V.verify([leak], q)) == 1 and V.verify([leak], w) == [],
               f"до: {[k for k in before if k.startswith('depot')]}, после: {after.get('depot.F')}, ложь: {len(V.verify([lie], w))}, утечка: {len(V.verify([leak], q))}")
        elif sc == "LL6":
            a, b = V.facts(w, "F", "F:вожак"), V.facts(w, "F", "F:офицер1")
            strip = lambda d: {k: v for k, v in d.items() if not k.startswith("npc")}
            ok("два персонажа с разными трейтами: промпты различны, факты состояния одинаковы", V.render_prompt(a) != V.render_prompt(b) and strip(a) == strip(b) and a["npc_traits"] != b["npc_traits"], f"{a['npc_traits']} против {b['npc_traits']}")
        elif sc == "LL7":
            bad, total = [], 0
            for name in CHRON:
                q, _ = S.run(name)
                q.p = replace(q.p, **{k: getattr(p, k) for k in ("voice_bug_facts", "voice_bug_verify_pass", "voice_bug_leak_depot")})
                for fa in q.factions:
                    sts = [l["statement"] for l in V.stub_voice(q, fa)]
                    total += len(sts)
                    bad += [(name, fa, m) for m in V.verify(sts, q)]
            ok("утверждения заглушки по сценариям хроники проходят verify без расхождений", total > 0 and not bad, f"утверждений {total}, расхождений {len(bad)}: {bad[:2]}")
        elif sc in ("LL8", "LL9"):
            src = (Path(__file__).parent / "voice.py").read_text(encoding="utf-8")
            if sc == "LL8":
                if p.voice_bug_inject_write:
                    src += "\n    world.rec(0, '99', 'x', 0, 1, 'BUG')\n"
                hits = WRITE_RX.findall(src)
                ok("в voice.py нет вызовов setf / rec / player_action (статическая проверка исходника)", not hits, f"вызовов записи: {hits}")
            else:
                if p.voice_bug_inject_import:
                    src = "import random\n" + src
                hits = NET_RX.findall(src)
                ok("voice.py не импортирует сетевых и случайных библиотек (статическая проверка исходника)", not hits, f"импорты: {hits}")
        return res
    return f


for _sc in LL:
    S.EXTRA[_sc] = (build(_sc), _chk(_sc))

S.REVERSE_EXTRA.update({
    "R136": (replace(Params(), voice_bug_facts=True), ("LL3",), "facts подменяет архетип"),
    "R137": (replace(Params(), voice_bug_verify_pass=True), ("LL4",), "verify всегда пропускает"),
    "R138": (replace(Params(), voice_bug_leak_depot=True), ("LL5",), "facts раскрывает чужой склад без знания"),
    "R139": (replace(Params(), voice_bug_inject_write=True), ("LL8",), "в voice.py появился вызов записи"),
    "R140": (replace(Params(), voice_bug_inject_import=True), ("LL9",), "в voice.py импорт случайных чисел"),
})
