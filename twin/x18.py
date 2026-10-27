"""Задача 18: личная арка (spec 18). Сценарии AR1–AR10, обратные R103–R108."""
from dataclasses import replace

from .arc import clamp, factor, promote
from .extra import clean, rows
from .model import BUCKETS_OUT, Site, World
from .params import Params
from . import scenarios as S

AR = ("AR1", "AR2", "AR3", "AR4", "AR5", "AR6", "AR7", "AR7b", "AR8", "AR9", "AR10")


def _p(p, **kw):
    return replace(clean(p), arc_enabled=True, **kw)


def _war(p, n_b=30, officer_traits=None, **kw):
    """A (80 чел.) штурмует B; у B — именные (вожак, офицер) при npc_state_enabled."""
    named = officer_traits is not None
    if named:
        p = replace(p, evolution_enabled=True, leader_enabled=True, evo_rule_order=(), npc_state_enabled=True)
    fs = {"A": S.faction(p, "A", "Хищники", 80, 30, 0), "B": S.faction(p, "B", "Хранители", n_b, 30, 40)}
    w = World(fs, [Site("Перевал", 40, 90, 4, owner="B")], p)
    if named:
        S.give_named(w, "B", officers=1)
        w.factions["B"].named[1]["traits"] = tuple(officer_traits)
    return w


def build(sc):
    def f(p):
        if sc in ("AR1", "AR2", "AR3", "AR4"):
            return _war(_p(p)), 1
        if sc == "AR5":
            q = _p(p)
            fa = S.faction(q, "A", "Хищники", 100, 30, 0)
            fa.steady, fa.ordinary, fa.skittish = 30, 40, 30
            w = World({"A": fa}, [], q)
            return w, 1
        if sc == "AR6":
            w = _war(_p(p))
            w.forced_assaults = {1: [("A", "Перевал")]}
            return w, 3
        if sc in ("AR7", "AR8"):
            w = _war(_p(p, drain_order="steady_first"), officer_traits=("Neuroticism_Low", "Conscientiousness_High"))
            w.forced_assaults = {5: [("A", "Перевал")]}
            return w, 8 if sc == "AR7" else 210
        if sc == "AR7b":
            w = _war(_p(p), officer_traits=("Neuroticism_High",))
            w.forced_assaults = {5: [("A", "Перевал")]}
            return w, 8
        if sc == "AR9":
            w = _war(_p(p))
            w.forced_assaults = {t: [("A" if t % 2 else "B", "Перевал")] for t in range(1, 21)}
            def own(w, t):
                s = w.site("Перевал")
                s.owner = "B" if t % 2 else "A"
            for t in range(1, 21):
                w.scheduled[t] = [lambda w, t=t: setattr(w.site("Перевал"), "owner", "B" if t % 2 else "A")]
            # B — всегда защитник на нечётных тиках, A — на чётных; пополнение: раз в 5 тиков +6 людей каждой стороне
            def refill(w):
                for fx in w.factions.values():
                    fx.ordinary += 6
                    fx.rank += 6
            for t in range(5, 21, 5):
                w.scheduled[t].append(refill)
            w.refill_total = {"A": 24 - 0, "B": 24 - 0}
            return w, 21
        if sc == "AR10":
            w = _war(replace(clean(p), arc_enabled=False))
            w.forced_assaults = {1: [("A", "Перевал")]}
            return w, 3
    return f


def _chk(sc):
    def f(w, series):
        res = []
        ok = lambda n, c, d: res.append((n, bool(c), d))
        p = w.p
        if sc == "AR1":
            h, b, hv = promote((30, 20, 10), (20, 15, 5), {}, {}, p)
            ok("потери 33/25/50%: закалённых +3, сломленных +1, Ordinary без изменений", h.get("steady") == 3 and h.get("ordinary", 0) == 0 and b.get("skittish") == 1 and hv == ["steady", "skittish"], f"hard {h}, brk {b}, тяжёлые {hv}")
        elif sc == "AR2":
            h, b, hv = promote((30, 20, 10), (28, 18, 8), {}, {}, p)
            ok("потери 6.7/10/20%: ни одного переезда", not any(h.values()) and not any(b.values()) and not hv, f"hard {h}, brk {b}")
        elif sc == "AR3":
            h, b, hv = promote((30, 20, 10), (20, 15, 5), {"steady": 5}, {}, p)
            ok("помеченные не считаются: floor(0.15·15) = 2 (было 5 → 7)", h["steady"] == 7, f"steady {h['steady']}")
        elif sc == "AR4":
            h, b = clamp((10, 20, 5), {"steady": 18, "ordinary": 4}, {"skittish": 9}, p.arc_clamp)
            bad, n = [], 0
            for bs in range(0, 31, 5):
                for bo in range(0, 31, 5):
                    for bk in range(0, 31, 5):
                        for a in ((bs, bo, bk), (bs // 2, bo // 2, bk // 2), (0, 0, 0)):
                            for hd in ({"steady": bs, "ordinary": bo}, {"steady": bs // 2, "ordinary": 0}):
                                n += 1
                                h2, b2, _ = promote((bs, bo, bk), a, hd, {"skittish": bk // 2}, p)
                                h2, b2 = clamp(a, h2, b2, p.arc_clamp)
                                if h2["steady"] > a[0] or h2["ordinary"] > a[1] or b2["skittish"] > a[2]:
                                    bad.append((bs, bo, bk, a))
            ok("закалённых 18, Steady стало 10 → ≤ 10; инварианты на сетке не нарушены", h["steady"] <= 10 and not bad and n > 1000, f"steady {h['steady']}, нарушений {len(bad)} из {n}")
        elif sc == "AR5":
            fa = w.factions["A"]
            fa.arc_hard, fa.arc_brk = {"steady": 10, "ordinary": 10}, {"skittish": 10}
            k = factor(fa.arc_hard, fa.arc_brk, fa.manpower, p)
            with_arc = w.power(fa)
            w.p = replace(p, arc_enabled=False)
            base = w.power(fa)
            fa.arc_hard, fa.arc_brk = {}, {}
            w.p = p
            empty = w.power(fa)
            ok("1.03; power = прежняя × 1.03; пустые вёдра → множитель 1.0 и сила побитово прежняя", abs(k - 1.03) < 1e-12 and abs(with_arc - base * k) < 1e-9 and empty == base, f"k {k}, с аркой {with_arc}, прежняя {base}, пустые {empty}")
        elif sc == "AR6":
            pr = rows(w, "B.arc.brk", "ARC_PROMOTE")
            vr = rows(w, "B.brk_ratio")
            fb = w.factions["B"]
            ok("ARC_PROMOTE на тике штурма, brk_ratio обновлён", len(pr) == 1 and pr[0][0] == 1 and pr[0][5] >= 1 and vr and vr[0][0] == 1, f"promote {pr}, ratio {vr}")
            ok("Manpower и сумма вёдер сходятся", all(fx.manpower + fx.wounded + sum(getattr(fx, b) for b in BUCKETS_OUT) == series[n][0][1] + fx.absorbed for n, fx in w.factions.items()), "люди сохранены")
        elif sc in ("AR7", "AR7b"):
            o = w.factions["B"].named[1]
            pk = o["pkg"]
            if sc == "AR7":
                ok("Steady-офицер: убран Neuroticism_High, добавлены Neuroticism_Low и TF_Hardened, пакет Hardened_Train_Pkg", "Neuroticism_High" not in o["traits"] and {"Neuroticism_Low", "TF_Hardened"} <= set(o["traits"]) and pk == "Hardened_Train_Pkg", f"traits {o['traits']}, пакет {pk}")
            else:
                ok("Skittish-офицер: TF_Broken и Broken_Drink_Pkg", "TF_Broken" in o["traits"] and "Neuroticism_Low" not in o["traits"] and pk == "Broken_Drink_Pkg", f"traits {o['traits']}, пакет {pk}")
        elif sc == "AR8":
            o = w.factions["B"].named[1]
            ok("200 спокойных тиков: traits и пакет те же", {"Neuroticism_Low", "TF_Hardened"} <= set(o["traits"]) and o["pkg"] == "Hardened_Train_Pkg" and w.tick >= 205, f"traits {o['traits']}, пакет {o['pkg']}, тик {w.tick}")
        elif sc == "AR9":
            conserved = all(fx.manpower + fx.wounded + sum(getattr(fx, b) for b in BUCKETS_OUT) == series[n][0][1] + fx.absorbed + 24 for n, fx in w.factions.items())
            sat = {n: (round(sum(fx.arc_hard.values()) / max(1, fx.manpower), 3), round(sum(fx.arc_brk.values()) / max(1, fx.manpower), 3)) for n, fx in w.factions.items()}
            ok("арка не создаёт и не убирает людей (с учётом 24 добавленных); тяжёлые события были", conserved and any(r[6] == "ARC_PROMOTE" for r in w.log), f"метрика насыщения (закалённые, сломленные) после 20 штурмов: {sat}")
        elif sc == "AR10":
            ok("arc_enabled = False: ни одной строки арки, power не меняется", not [r for r in w.log if r[2] == "18"], f"строк модуля 18: {len([r for r in w.log if r[2] == '18'])}")
        return res
    return f


for _sc in AR:
    S.EXTRA[_sc] = (build(_sc), _chk(_sc))

S.REVERSE_EXTRA.update({
    "R103": (replace(Params(), arc_severe_loss=0.0), ("AR2",), "порог тяжёлого события 0 (всегда тяжёлое)"),
    "R104": (replace(Params(), arc_harden_steady=0.20, arc_break_skittish=0.15), ("AR1",), "доли Steady и Skittish поменяны"),
    "R105": (replace(Params(), arc_count_marked=True), ("AR3",), "помеченные снова считаются"),
    "R106": (replace(Params(), arc_clamp=False), ("AR4",), "клэмпа арки нет"),
    "R107": (replace(Params(), arc_vet_w=0.0, arc_brk_w=0.0), ("AR5",), "веса ФакторАрки 0"),
    "R108": (replace(Params(), arc_revert_ticks=50), ("AR8",), "откат keyword'ов через 50 тиков"),
})
