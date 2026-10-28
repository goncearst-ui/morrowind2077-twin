"""Задача 23c: несколько планет и ленивый пересчёт «тихих» (spec 23). Сценарии MP1–MP8, обратные R155–R160. Двойник; Creation Kit не описывает."""
import time
from dataclasses import replace

from . import integration as I
from . import scenarios as S
from .extra import clean
from .model import Planet, Site, World
from .params import Params
from .planets import planet_world

MP = ("MP1", "MP2", "MP3", "MP4", "MP5", "MP6", "MP7", "MP8")
STABLE = dict(y1=60, y2=26, dos=30)     # мир без вымирания: для сравнения ленивого и пошагового
STRESS = dict(y1=42, y2=18, dos=30)     # живой мир: штурмы, дезертирство, вымирание части фракций


def _small(p, multi, forced=None, hegemon=False):
    """Планеты H (дом A), X (объекты A), Y (дом и объект B). Чистая обстановка: ничего, кроме выбранных событий, не происходит."""
    q = replace(clean(p), multi_planet_enabled=multi, planet_hegemon_enabled=hegemon, quiet_window_k=10, quiet_period_p=7)
    ss = [Site("X1", 20, 80, 2, owner="A", region="X"), Site("X2", 20, 40, 2, owner="A", region="X"), Site("Y1", 20, 60, 2, owner="B", region="Y")]
    fs = {"A": S.faction(q, "A", "Хранители", 30, 50, 40), "B": S.faction(q, "B", "Хранители", 30, 50, 20)}
    fs["A"].home, fs["B"].home = "H", "Y"
    pls = {"H": Planet("H", ("H",)), "X": Planet("X", ("X",)), "Y": Planet("Y", ("Y",))}
    w = World(fs, ss, q, planets=pls)
    if forced:
        w.forced_assaults = forced
    for f in w.factions.values():
        w.publish_dos(f, phase=0)
    return w


def _two(p):
    """MP5: две планеты, на каждой свой хозяин (A на PA, B на PB)."""
    q = replace(clean(p), multi_planet_enabled=True, planet_hegemon_enabled=True)
    ss = [Site("PA1", 20, 60, 2, owner="A", region="PA"), Site("PA2", 20, 40, 2, owner="A", region="PA"),
          Site("PB1", 20, 60, 2, owner="B", region="PB"), Site("PB2", 20, 40, 2, owner="B", region="PB")]
    fs = {"A": S.faction(q, "A", "Хранители", 30, 50, 40), "B": S.faction(q, "B", "Хранители", 30, 50, 40)}
    fs["A"].home, fs["B"].home = "PA", "PB"
    w = World(fs, ss, q, planets={"PA": Planet("PA", ("PA",)), "PB": Planet("PB", ("PB",))})
    for f in w.factions.values():
        w.publish_dos(f, phase=0)
    return w


def build(sc):
    def f(p):
        if sc == "MP1":
            return S.build("DS1", replace(p, multi_planet_enabled=False))
        if sc == "MP2":
            w, _ = planet_world(p, 20, named=25, **STRESS)
            I.instrument(w)
            return w, 1000
        if sc == "MP3":
            return _small(p, True), 66
        if sc == "MP4":
            return _small(p, True, forced={30: [("B", "X1")]}), 60
        if sc == "MP5":
            return _two(p), 12
        if sc == "MP6":
            w, _ = planet_world(p, 20, multi=True, **STABLE)
            return w, 1000
        if sc == "MP7":
            w, _ = planet_world(p, 1000, multi=True, **STABLE)
            w.t0 = time.perf_counter()
            return w, 200
        w, _ = planet_world(p, 20, multi=True, **STABLE)
        return w, 300
    return f


def _run(w, n):
    for _ in range(n):
        w.step()
    return w


def _chk(sc):
    def f(w, series):
        res = []
        ok = lambda n, c, d: res.append((n, bool(c), d))
        p = w.p
        if sc == "MP1":
            import json
            from pathlib import Path
            base = json.loads((Path(__file__).resolve().parent.parent / "tests" / "baseline_pre23a.json").read_text(encoding="utf-8"))["DS1"]
            ok("при multi_planet_enabled = False журнал DS1 совпадает с эталоном tests/baseline_pre23a.json строка в строку и планет нет",
               [list(r) for r in w.log] == base and not w.planets, f"строк {len(w.log)} и {len(base)}, планет {len(w.planets)}")
        elif sc == "MP2":
            st = [r for r in w.log if r[3].endswith(".state")]
            act = sum(1 for r in st if r[6] == "PLANET_ACTIVE")
            qt = sum(1 for r in st if r[6] == "PLANET_QUIET")
            ok("мир 4 фракции × 20 планет × 100 именных, 1000 тиков, все флаги: инварианты (а)–(д) задачи 22 зелёные, были переходы в тихие и обратно",
               w.tick == 1000 and not w.ig_bad and qt > 0 and act > 0, f"тик {w.tick}, нарушений {len(w.ig_bad)}: {w.ig_bad[:2]}, в тихие {qt}, в активные {act}, именных {sum(len(x.named) for x in w.factions.values())}")
        elif sc == "MP3":
            q = _run(_small(replace(p, multi_planet_enabled=False), False), 66)
            dx = abs(w.regions["X"] - q.regions["X"])
            ds = abs(w.factions["A"].supply - q.factions["A"].supply)
            ok("тихая планета без событий: достаток региона и запас фракции после пакетного пересчёта совпадают с пошаговым (тик 66 — граница пакета)",
               w.planets["X"].state == "quiet" and dx < 1e-9 and ds < 1e-6 * max(1.0, q.factions["A"].supply),
               f"состояние {w.planets['X'].state}, достаток {w.regions['X']:.6f} и {q.regions['X']:.6f} (разница {dx:.2e}), запас A {w.factions['A'].supply:.4f} и {q.factions['A'].supply:.4f} (разница {ds:.2e})")
        elif sc == "MP4":
            st = [(r[0], r[5]) for r in w.log if r[3] == "planet.X.state"]
            bt = [(e["tick"], e["n"]) for e in w.events if e["kind"] == "planet_batch" and e["planet"] == "X"]
            hm = [r for r in w.log if r[3] in ("planet.H.state", "planet.Y.state")]
            ok("планета X: тихая на тике 10, активная в тик штурма (30) в тот же тик, снова тихая на тике 40; пакеты на 17, 24 (по 7), 30 (догон 6), 47, 54; дома фракций (H, Y) всегда активны",
               st == [(10, "quiet"), (30, "active"), (40, "quiet")] and bt == [(17, 7), (24, 7), (30, 6), (47, 7), (54, 7)] and not hm,
               f"переходы {st}, пакеты {bt}, переходы домов {len(hm)}")
        elif sc == "MP5":
            hp = {k: v[0] for k, v in w.hegemon_p.items()}
            rows = [(r[3], r[5]) for r in w.log if r[6] == "HEGEMON"]
            ok("две планеты с разными хозяевами одновременно: PA — A, PB — B (отдельные строки журнала)",
               hp.get("PA") == "A" and hp.get("PB") == "B" and ("planet.PA.hegemon", "A") in rows and ("planet.PB.hegemon", "B") in rows, f"хозяева {hp}, строки {rows}")
        elif sc == "MP6":
            q, _ = planet_world(replace(p, multi_planet_enabled=False), 20, multi=False, **STABLE)
            _run(q, 1000)
            tm = lambda x: sum(f_.manpower for f_ in x.factions.values())
            ts = lambda x: sum(f_.supply for f_ in x.factions.values())
            dm, dsp = abs(tm(w) - tm(q)) / max(1, tm(q)), abs(ts(w) - ts(q)) / max(1.0, ts(q))
            qs, _ = planet_world(replace(p, multi_planet_enabled=False), 20, multi=False, **STRESS)
            ws, _ = planet_world(p, 20, multi=True, **STRESS)
            _run(qs, 1000)
            _run(ws, 1000)
            sm = abs(tm(ws) - tm(qs)) / max(1, tm(qs))
            ok("расхождение ленивого и пошагового на 1000 тиках (мир без вымирания): людей и запаса не больше 5% [предл]; для справки расхождение живого мира дано в детали",
               dm <= 0.05 and dsp <= 0.05,
               f"стабильный мир: людей {tm(w)} и {tm(q)} ({100 * dm:.2f}%), запаса {ts(w):.0f} и {ts(q):.0f} ({100 * dsp:.2f}%); живой мир (справка, без порога): людей {tm(ws)} и {tm(qs)} ({100 * sm:.1f}%), "
               f"итоги по фракциям ленивый {[x.manpower for x in ws.factions.values()]}, пошаговый {[x.manpower for x in qs.factions.values()]}")
        elif sc == "MP7":
            el = time.perf_counter() - w.t0
            quiet = sum(1 for pl in w.planets.values() if pl.state == "quiet")
            ok("мир 4 фракции × 1000 планет, 200 тиков: завершён, не менее 90% планет тихие [предл], время прогона записано (порог 120 с, стенд HP OMEN не запускался)",
               w.tick == 200 and quiet >= 0.9 * len(w.planets) and el <= 120.0,
               f"планет {len(w.planets)}, тихих {quiet} ({100.0 * quiet / len(w.planets):.1f}%), время {el:.1f} с (облачный контейнер, не HP OMEN), строк журнала {len(w.log)}")
        elif sc == "MP8":
            q, _ = planet_world(p, 20, multi=True, **STABLE)
            _run(q, 300)
            ok("два прогона мира с планетами дают идентичные журналы", q.log == w.log and len(w.log) > 1000, f"строк {len(w.log)} и {len(q.log)}")
        return res
    return f


for _sc in MP:
    S.EXTRA[_sc] = (build(_sc), _chk(_sc))

_ON = Params()
S.REVERSE_EXTRA.update({
    "R155": (replace(_ON, mp_bug_off_by_one=True), ("MP3",), "пакет тихой планеты считает на тик меньше"),
    "R156": (replace(_ON, mp_bug_skip_income=True), ("MP3",), "доход тихих объектов теряется"),
    "R157": (replace(_ON, mp_bug_no_wake=True), ("MP4",), "событие не будит тихую планету"),
    "R158": (replace(_ON, mp_bug_never_quiet=True), ("MP4",), "планета не возвращается в тихие"),
    "R159": (replace(_ON, mp_bug_shared_hegemon=True), ("MP5",), "хозяин каждой планеты считается по всем объектам мира"),
    "R160": (replace(_ON, mp_bug_batch_every_tick=True), ("MP4",), "тихая планета пересчитывается каждый тик"),
})
