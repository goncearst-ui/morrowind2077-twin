"""Задача 24a: слой сцены в двойнике (spec 24a). Сценарии SC1–SC17, обратные R165–R174. Двойник; Creation Kit и плагин не описывает."""
from dataclasses import replace

from . import scenarios as S
from . import snapshot as SN
from .arith import fsum
from .extra import clean, rows
from .model import BUCKETS_OUT, Planet, Site, World
from .params import Params

SC = tuple(f"SC{i}" for i in range(1, 19))
FORT = "Форт"


def _p(p, **kw):
    base = dict(evolution_enabled=True, leader_enabled=True, npc_state_enabled=True, obj_enabled=True, strategy_enabled=True,
                player_levers_enabled=True, reputation_enabled=True, inheritance_enabled=True, evo_rule_order=(), scene_enabled=True)
    return replace(clean(p), **{**base, **kw})


def _world(p, script=None, forced=None, n=(40, 40, 30), pins=True, shaft=False, planets=None):
    """Три фракции; «Форт» (доход 60) у B; базы без дохода. Оси подвязаны, решений при голоде нет: событий нет, кроме заданных."""
    ss = [Site(FORT, 20, 60, 3, owner="B", region="X" if planets else "common"),
          Site("База", 10, 0, 4, owner="A", income_disabled=True, region="H" if planets else "common"),
          Site("ПостB", 10, 0, 4, owner="B", income_disabled=True, region="Y" if planets else "common")]
    if shaft:
        ss.append(Site("Шахта", 15, 0, 3, owner="C", income_disabled=True))
    fs = {"A": S.faction(p, "A", "Хранители", n[0], 30, 10), "B": S.faction(p, "B", "Хранители", n[1], 30, 30),
          "C": S.faction(p, "C", "Хранители", n[2], 30, 0)}
    if planets:
        fs["A"].home, fs["B"].home, fs["C"].home = "H", "Y", "H"
    w = World(fs, ss, p, planets=planets or {})
    S.give_named(w, "A", ("Радикальный",), 2)
    S.give_named(w, "B", ("Радикальный",), 2)
    S.give_named(w, "C")
    if pins:
        for t in range(1, 101):
            for f in "ABC":
                w.scheduled.setdefault(t, []).append(S.ev_pins(f, [(10**6, 30.0, None, None, 80.0)]))
    w.player_script = script or {}
    w.forced_assaults = forced or {}
    for f in fs.values():
        w.publish_dos(f, phase=0)
    return w


def _go(w, n):
    for _ in range(n):
        w.step()
    return w


def _res(**kw):
    out = dict(winner="attacker", player_side="attacker", losses={}, named_dead=[], masked=False, witnesses=1)
    out.update(kw)
    return out


def _tot(f):
    return f.manpower + f.wounded + fsum(getattr(f, b) for b in BUCKETS_OUT)


def _fails(w):
    return [(e["tick"], e["action"], e["code"]) for e in w.events if e["kind"] == "player_failed"]


def _alive(f, name):
    return next(n["alive"] for n in f.named if n["name"] == name)


def _ev(w, kind):
    return [e for e in w.events if e["kind"] == kind]


def _mk(p, horizon, **kw):
    return _go(_world(p, **kw), horizon)


def _fact_rows(w, tick):
    """Строки штурма и его последствий на тике (без порядка): цель, было, стало, причина."""
    keep = ("ASSAULT", "TROPHY", "DEPOT_STRIKE", "DEPOT_MOVE")
    return sorted((r[3], str(r[4]), str(r[5]), r[6]) for r in w.log if r[0] == tick and r[6] in keep)


def _loss(**kw):
    """Поражение стороны игрока: игрок за атакующего A, победила оборона B; по умолчанию игрок убил 2 человека B, A потеряла 3."""
    base = dict(winner="defender", player_side="attacker", losses={"A": {"skittish": 3}, "B": {"skittish": 2}})
    base.update(kw)
    return _res(**base)


_LOSS = _loss()


def build(sc):
    def f(p):
        q = _p(p)
        pre = {3: [("presence", FORT)]}
        a5 = {5: [("A", FORT)]}
        if sc == "SC1":
            return _world(q), 1
        if sc == "SC2":
            return _world(q, pre, a5), 5
        if sc == "SC3":
            q = _p(p, relations_enabled=True)
            return _world(q, {**pre, 6: [("scene_result", FORT, _res(losses={"B": {"skittish": 3, "ordinary": 1}, "A": {"skittish": 1}},
                                                                   named_dead=[("B", "B:офицер1", "player")]))]}, a5), 12
        if sc == "SC4":
            return _world(q, {**pre, 6: [("scene_result", FORT, _res(winner="defender", player_side="defender",
                                                                   losses={"A": {"skittish": 2}, "B": {"skittish": 1}}))]}, a5), 12
        if sc == "SC5":
            return _world(q, {**pre, 6: [("scene_leave", FORT)]}, a5), 8
        if sc == "SC6":
            return _world(q, pre, a5), 8
        if sc == "SC7":
            return _world(q, {3: [("presence", FORT)], 4: [("scene_open", FORT), ("scene_result", FORT, _res(losses={"B": {"skittish": 3, "ordinary": 2}}))]}), 36
        if sc == "SC8":
            return _world(q, {**pre, 6: [("scene_result", FORT, _res(losses={"A": {"skittish": 9}}))]}, a5), 6
        if sc == "SC9":
            return _world(q, {**pre, 6: [("scene_result", FORT, _res(named_dead=[("B", "B:вожак", "player")]))]}, a5), 7
        if sc == "SC10":
            return _world(q, {**pre, 6: [("scene_result", FORT, _res(losses={"B": {"skittish": 2}}, named_dead=[("B", "B:офицер9", "player")]))]}, a5), 6
        if sc == "SC11":
            q = _p(p, multi_planet_enabled=True, quiet_window_k=10, quiet_period_p=7)
            pl = {"H": Planet("H", ("H",)), "X": Planet("X", ("X",)), "Y": Planet("Y", ("Y",))}
            return _world(q, {20: [("presence", FORT)], 40: [("presence", None)]}, planets=pl), 56
        if sc == "SC12":
            return _world(q, {3: [("presence", FORT)], 6: [("scene_result", FORT, _res(winner="defender", player_side="defender")),
                                                          ("presence", "Шахта"), ("scene_open", "Шахта")],
                              7: [("presence", FORT), ("scene_open", FORT)]}, {5: [("A", FORT), ("C", FORT)]}, shaft=True), 9
        if sc == "SC13":
            q = _p(p, scene_return_days=4)
            script = {1: [("presence", FORT)]}
            for k in range(10):
                script.setdefault(10 * k + 1, []).extend([("scene_open", FORT), ("scene_result", FORT, _res(losses={"B": {"skittish": 1}}))])
            return _world(q, script), 100
        if sc == "SC14":
            q = _p(p, relations_enabled=True)
            return _world(q, {**pre, 6: [("scene_result", FORT, _res(losses={"B": {"skittish": 3}}))]}, a5, pins=False), 5
        if sc == "SC15":
            q = _p(p, log_two_level_enabled=True)
            return _world(q, {**pre, 6: [("scene_result", FORT, _res(losses={"B": {"skittish": 3}}, named_dead=[("B", "B:офицер1", "player")]))]}, a5), 12
        if sc == "SC16":
            return _world(q), 1
        if sc == "SC18":
            return _world(q, {**pre, 6: [("scene_result", FORT, _LOSS)]}, a5), 6 + q.rep_rumor_delay + 2
        # SC17
        return _world(q, {**pre, 6: [("scene_result", FORT, _res(losses={"B": {"skittish": 3}}))]}, a5), 7
    return f


def _chk(sc):
    def f(w, series):
        res = []
        ok = lambda n, c, d: res.append((n, bool(c), d))
        p = w.p
        dly = p.rep_rumor_delay
        if sc == "SC1":
            seen = []
            for name in ("DS1", "DS2", "DS4"):
                logs = []
                for on in (False, True):
                    w1, _ = S.run(name, replace(p, scene_enabled=on), evo=True)
                    logs.append(w1.log)
                seen.append((name, logs[0] == logs[1], len(logs[0])))
            m24 = [r for r in w.log if r[2] == "24"]
            ok("scene_enabled без действий игрока: журналы DS1, DS2, DS4 совпадают строка в строку с выключенным флагом; строк модуля 24 нет",
               all(x[1] and x[2] > 100 for x in seen) and not m24, f"{seen}, строк модуля 24: {len(m24)}")
        elif sc == "SC2":
            sc2 = w.scenes.get(FORT, {})
            q2 = _mk(replace(p, scene_adv_cap=2.0), 5, script={3: [("presence", FORT)]}, forced={5: [("A", FORT)]}, n=(10, 80, 30))
            qs = q2.scenes.get(FORT, {})
            part, on, pr = sc2.get("part", {}), sc2.get("on_screen", {}), sc2.get("pressure", {})
            ok("штурм при игроке рядом: числового штурма нет, сцена открыта, расстановка: на экране не больше 6, на экране + запас = участники, ничего не выбыло",
               bool(sc2) and not _ev(w, "assault") and not [r for r in w.log if r[6] == "ASSAULT"] and on == {"A": 6, "B": 5} and pr == {"A": 2, "B": 0}
               and all(on[k] + pr[k] == part[k] for k in part) and all(v <= p.scene_fighters_max for v in on.values())
               and rows(w, f"scene.{FORT}.state") == [(5, 7, "24", f"scene.{FORT}.state", None, "open", "SCENE_OPEN")] and w.factions["A"].dead == 0
               and w.factions["A"].last_assault == 5 and len(_ev(w, "scene_opened")) == 1,
               f"расстановка {sc2}, строки состояния {rows(w, f'scene.{FORT}.state')}")
            ok("качество стороны растёт с перевесом, но не выше потолка scene_adv_cap",
               sc2["quality"]["B"] > sc2["quality"]["A"] and qs.get("quality", {}).get("B") == p.scene_adv_cap and qs["quality"]["A"] < 1.0,
               f"перевес B слабый {sc2.get('quality')}, перевес B сильный {qs.get('quality')}, потолок {p.scene_adv_cap}")
        elif sc == "SC3":
            a, b, c = w.factions["A"], w.factions["B"], w.factions["C"]
            ctrl = _go(_world(replace(p), n=(80, 30, 30), forced={6: [("A", FORT)]}), 8)
            rel = lambda x: {(r[3], r[6]) for r in x.log if r[2] == "08" and r[3].startswith("rel.B>A")}
            ev = next(iter(_ev(w, "assault")), {})
            ok("победа атакующего: потери по ведрам применены (B 4 и офицер, A 1), людей не стало больше или меньше, шок обеим, владелец сменился, именной погиб от игрока",
               (b.dead, a.dead, b.manpower, a.manpower) == (5, 1, 35, 39) and (_tot(a), _tot(b), _tot(c)) == (40, 40, 30)
               and [(r[0], r[5]) for r in rows(w, "B.shock", "SCENE_RESULT")] == [(6, 10.0)] and rows(w, "A.shock", "SCENE_RESULT")
               and [(r[0], r[4], r[5], r[6]) for r in rows(w, f"site.{FORT}.owner")] == [(6, "B", "A", "SCENE_RESULT")]
               and not _alive(b, "B:офицер1") and rows(w, "B.named.B:офицер1", "SCENE_NAMED"),
               f"мертвые B {b.dead}, A {a.dead}; людей {(_tot(a), _tot(b), _tot(c))}; владелец {[(r[0], r[4], r[5]) for r in rows(w, f'site.{FORT}.owner')]}")
            ok("событие assault с scene=True, ключи как у числового; обиды 08a те же, что у числового штурма",
               ev.get("scene") is True and ev.get("attacker_wins") is True and ev.get("player_side") == "attacker"
               and {"losses", "manpower_before", "shock_inc", "supply_moved", "ratio", "forced"} <= set(ev) and rel(w) == rel(ctrl) and rel(w),
               f"событие {ev}, обиды сцены {sorted(rel(w))}, обиды числового {sorted(rel(ctrl))}")
        elif sc == "SC4":
            b, a = w.factions["B"], w.factions["A"]
            ev = next(iter(_ev(w, "assault")), {})
            tr = rows(w, "B.supply", "TROPHY")
            ok("победа обороны: владелец не меняется, потери по ведрам, трофей победителю (B), цена победы по противнику игрока (A)",
               not rows(w, f"site.{FORT}.owner") and (a.dead, b.dead) == (2, 1) and tr and tr[0][5] > tr[0][4] and ev.get("attacker_wins") is False
               and ev.get("flipped") is False and a.vendetta > 0 and a.vendetta_culprit == "player"
               and [(e["tick"], e["faction"]) for e in _ev(w, "rep_identified")] == [(6 + dly, "A")],
               f"владелец: {rows(w, f'site.{FORT}.owner')}, потери {(a.dead, b.dead)}, событие {ev}, вендетта A {a.vendetta}, слухи {_ev(w, 'rep_identified')}")
        elif sc in ("SC5", "SC6"):
            t_res = 6 if sc == "SC5" else 7
            ctrl = _go(_world(p, forced={t_res: [("A", FORT)]}), 8)
            how = "SCENE_LEAVE" if sc == "SC5" else "SCENE_TIMEOUT"
            cl = rows(w, f"scene.{FORT}.state", how)
            quiet = not [r for r in w.log if r[2] == "02" or r[6] in ("SCENE_VENDETTA", "SCENE_RESULT")] and not w.scenes
            ok(("выход" if sc == "SC5" else "таймаут") + f": сцена закрыта причиной {how}; штурм разрешён числом, строки совпадают с прогоном без игрока; вражды, мести, слуха нет",
               len(cl) == 1 and cl[0][0] == t_res and _fact_rows(w, t_res) == _fact_rows(ctrl, t_res) and _fact_rows(w, t_res) and quiet,
               f"закрытие {cl}, строк штурма {len(_fact_rows(w, t_res))} и {len(_fact_rows(ctrl, t_res))}, тихо: {quiet}")
        elif sc == "SC7":
            b = w.factions["B"]
            q2 = _mk(replace(p), 36, script={3: [("presence", FORT)], 4: [("scene_open", FORT), ("scene_result", FORT, _res(masked=True, losses={"B": {"skittish": 3, "ordinary": 2}}))]})
            own = [(r[0], r[4], r[5], r[6]) for r in rows(w, f"site.{FORT}.owner")]
            vd = rows(w, "B.vendetta", "SCENE_VENDETTA")
            rep = [(r[0], r[4], r[5]) for r in rows(w, "player.rep.B", "RUMOR_DELIVERED")]
            reg = rows(w, "rep.region.common", "RUMOR_DELIVERED")
            ok("игрок против владельца: потери B 5, объект «ничей», возврат ровно в срок, вендетта 20, слух и падение репутации через rep_rumor_delay",
               b.dead == 5 and own == [(4, "B", None, "SCENE_RESULT"), (4 + p.scene_return_days, None, "B", "SCENE_RETURN")]
               and [(r[0], r[4], r[5]) for r in vd] == [(4, 0, p.vendetta_max)] and b.vendetta_culprit in ("player", None)
               and rep == [(4 + dly, 50.0, 20.0)] and reg and rows(w, f"scene.return.{FORT}", "SCENE_RETURN_SET") and _ev(w, "scene_strike")[0]["player_wins"] is True,
               f"потери {b.dead}, владелец {own}, вендетта {[(r[0], r[4], r[5]) for r in vd]}, репутация {rep}")
            b2 = q2.factions["B"]
            own2 = [(r[0], r[5]) for r in rows(q2, f"site.{FORT}.owner")]
            ok("то же в маске: потери и объект есть, возврат есть, вражды и мести нет (слух безымянный)",
               b2.dead == 5 and own2 == [(4, None), (34, "B")] and not rows(q2, "B.vendetta", "SCENE_VENDETTA") and not rows(q2, "player.rep.B")
               and [(e["tick"]) for e in _ev(q2, "rep_unidentified")] == [4 + dly],
               f"потери {b2.dead}, владелец {own2}, вендетта {rows(q2, 'B.vendetta', 'SCENE_VENDETTA')}, слухи {_ev(q2, 'rep_unidentified')}")
        elif sc == "SC8":
            a = w.factions["A"]
            q2 = _mk(w.p, 6, script={3: [("presence", FORT)], 6: [("scene_result", FORT, _res(winner="defender", player_side=None, losses={"A": {"skittish": 8}}))]}, forced={5: [("A", FORT)]})
            ok("результат с потерями больше бюджета стороны (9 > 8) отклонён: OVER_BUDGET, строк результата нет, сцена открыта",
               _fails(w) == [(6, "scene_result", "OVER_BUDGET")] and a.dead == 0 and not [r for r in w.log if r[6] == "SCENE_RESULT"] and FORT in w.scenes,
               f"отказы {_fails(w)}, мертвых A {a.dead}, сцены {list(w.scenes)}")
            ok("ровно бюджет (8) принимается: A выбыло 8, сцена закрыта",
               not _fails(q2) and q2.factions["A"].dead == 8 and FORT not in q2.scenes, f"отказы {_fails(q2)}, мертвых {q2.factions['A'].dead}, сцены {list(q2.scenes)}")
        elif sc == "SC9":
            ev = _ev(w, "leader_killed")
            wl = _mk(w.p, 7, script={3: [("presence", FORT)], 6: [("scene_result", FORT, _res(named_dead=[("B", "B:вожак", "side")]))]}, forced={5: [("A", FORT)]})
            w2 = _mk(w.p, 7, script={3: [("presence", FORT)], 6: [("scene_result", FORT, _res(named_dead=[("B", "B:офицер9", "player")]))]}, forced={5: [("A", FORT)]})
            w3 = _mk(w.p, 7, script={3: [("presence", FORT)], 4: [("kill", "B", "B:офицер1")], 6: [("scene_result", FORT, _res(named_dead=[("B", "B:офицер1", "player")]))]}, forced={5: [("A", FORT)]})
            w4 = _mk(w.p, 7, script={3: [("presence", FORT)], 6: [("scene_result", FORT, _res(player_side=None, named_dead=[("B", "B:вожак", "player")]))]}, forced={5: [("A", FORT)]})
            ok("вожак погиб от игрока: leader_killed с culprit player; погиб «стороной»: culprit A",
               len(ev) == 1 and ev[0]["culprit"] == "player" and ev[0]["reason"] == "SCENE_NAMED" and _ev(wl, "leader_killed")[0]["culprit"] == "A",
               f"события {[(e['tick'], e['culprit']) for e in ev]} и {[(e['tick'], e['culprit']) for e in _ev(wl, 'leader_killed')]}")
            ok("несуществующий, уже мёртвый именной: NO_NAMED; by=player без стороны игрока: NOT_SIDE; ничего не применено",
               _fails(w2) == [(6, "scene_result", "NO_NAMED")] and [f[2] for f in _fails(w3)] == ["NO_NAMED"] and _fails(w4) == [(6, "scene_result", "NOT_SIDE")]
               and not [r for r in w2.log + w3.log + w4.log if r[6] in ("SCENE_RESULT", "SCENE_NAMED")],
               f"{_fails(w2)}, {_fails(w3)}, {_fails(w4)}")
        elif sc == "SC10":
            before = _mk(w.p, 5, script={3: [("presence", FORT)]}, forced={5: [("A", FORT)]})
            n0 = len(before.log)
            scn0 = dict(before.scenes[FORT])
            after = w
            changed = [r for r in after.log[n0:] if r[2] in ("03", "04", "06", "13", "02") and r[0] == 6 and r[6] in ("SCENE_RESULT", "SCENE_NAMED")]
            ok("результат с ошибкой в именных: отказ NO_NAMED, ни одной строки результата, потерь нет, репутация и сцена прежние",
               _fails(after) == [(6, "scene_result", "NO_NAMED")] and not changed and after.factions["B"].dead == 0 and not after.rep_rumors
               and after.scenes[FORT] == scn0 and not rows(after, "player.rep.B"),
               f"отказы {_fails(after)}, строк результата {len(changed)}, мертвых B {after.factions['B'].dead}")
        elif sc == "SC11":
            st = [(r[0], r[5], r[6]) for r in rows(w, "planet.X.state")]
            ctrl = _mk(w.p, 56, script={}, planets={"H": Planet("H", ("H",)), "X": Planet("X", ("X",)), "Y": Planet("Y", ("Y",))})
            st0 = [(r[0], r[5], r[6]) for r in rows(ctrl, "planet.X.state")]
            k = p.quiet_window_k
            between = [x for x in st if 21 <= x[0] <= 40 + k - 2]
            ok("игрок у объекта на тихой планете: планета просыпается (PLANET_ACTIVE на тике 20), пока игрок рядом остаётся активной, после ухода засыпает по правилу 23c",
               st[:2] == [(k, "quiet", "PLANET_QUIET"), (20, "active", "PLANET_ACTIVE")] and not between and len(st) == 3 and st[2][1] == "quiet" and 40 + k - 2 <= st[2][0] <= 40 + k,
               f"переходы X: {st}")
            ok("без присутствия планета X сама не просыпается (23c: игрок планету не будит)", st0 == [(k, "quiet", "PLANET_QUIET")], f"переходы X без игрока: {st0}")
        elif sc == "SC12":
            a5 = [e for e in w.events if e["kind"] == "assault_deferred"]
            ok("второй штурм на объект с открытой сценой отложен; результат закрыл сцену; следующая сцена открыта; третья сцена (одновременно) отклонена SCENE_BUSY; сцены закрываются",
               [(e["attacker"], e["tick"]) for e in a5] == [("C", 5)] and rows(w, f"scene.{FORT}.state", "SCENE_RESULT") and rows(w, "scene.Шахта.state", "SCENE_OPEN")
               and _fails(w) == [(7, "scene_open", "SCENE_BUSY")],
               f"отложено {[(e['attacker'], e['tick']) for e in a5]}, отказы {_fails(w)}, сцены {list(w.scenes)}")
            ok("открытых сцен не больше scene_open_max; после таймаута сцен нет", len(w.scenes) <= p.scene_open_max and not w.scenes, f"сцены {list(w.scenes)}")
        elif sc == "SC13":
            tot0 = {"A": 40, "B": 40, "C": 30}
            vd = rows(w, "B.vendetta", "SCENE_VENDETTA")
            rep = rows(w, "player.rep.B")
            ret = rows(w, f"site.{FORT}.owner", "SCENE_RETURN")
            ok("10 нападений на один объект за 100 суток: людей не меньше нуля, сумма сохранена, вендетта ни разу не продлена, репутация не растёт, объект возвращается после каждого",
               all(_tot(w.factions[n]) == tot0[n] for n in tot0) and w.factions["B"].manpower == 30 and w.factions["B"].dead == 10
               and vd and all(r[4] == 0 for r in vd) and rep and all(r[5] < r[4] for r in rep) and len(ret) == 10 and w.site(FORT).owner == "B",
               f"людей {[(n, _tot(w.factions[n])) for n in tot0]}, B {w.factions['B'].manpower}, вендетта {[(r[0], r[4], r[5]) for r in vd]}, возвратов {len(ret)}, репутация {[(r[0], r[5]) for r in rep]}")
        elif sc == "SC14":
            a = SN.snapshot_write(w)
            w2 = SN.snapshot_read(a)
            n = len(w.log)
            _go(w, 8)
            _go(w2, 8)
            w3 = _mk(w.p, 13, script=w.player_script, forced=w.forced_assaults, pins=False)
            mid = SN.snapshot_read(a)
            ok("снимок при открытой сцене: сцена в снимке, читается и пишется байт в байт, продолжение идентично непрерывному прогону, прогон повторяем",
               FORT in mid.scenes and mid.scene_presence == FORT and SN.snapshot_write(mid) == a and w.log[n:] == w2.log and w.log == w3.log
               and [r for r in w2.log if r[6] == "SCENE_RESULT"],
               f"сцена в снимке {FORT in mid.scenes}, строк после {len(w2.log)} и {len(w.log[n:])}")
        elif sc == "SC15":
            m24 = [r for r in w.log if r[2] == "24"]
            kinds = {r[6] for r in w.log if r[6].startswith("SCENE_")}
            in_sum = [k for k in w.log_sum if k[1] == "24" or str(k[3]).startswith("SCENE_")]
            ok("при двухуровневом журнале строки модуля 24 и причины SCENE_* идут в подробный уровень, в сводном их нет",
               len(m24) >= 6 and {"SCENE_OPEN", "SCENE_RESULT", "SCENE_NAMED"} <= kinds and not in_sum and w.log_sum,
               f"строк 24 в подробном {len(m24)}, причины {sorted(kinds)}, в сводном {in_sum[:3]}")
        elif sc == "SC16":
            from . import refworld as R
            from pathlib import Path
            gold = Path(__file__).resolve().parent.parent / "tests" / "golden"
            files = R.generate(Params())
            same = (gold / "MANIFEST.json").exists() and (gold / "MANIFEST.json").read_text(encoding="utf-8") == R.manifest(files) \
                and all((gold / n).read_text(encoding="utf-8") == files[n] for n in R.FILES)
            ds = [(n, S.evaluate(n)[0]) for n in ("DS1", "DS2", "DS4")]
            ok("при scene_enabled = False золотые файлы tests/golden/ совпадают с повторной генерацией; штопор DS1, DS2, DS4 зелёный",
               same and all(x[1] for x in ds) and not Params().scene_enabled, f"золото {'совпало' if same else 'расходится'}, штопор {ds}")
        elif sc == "SC18":
            a, b = w.factions["A"], w.factions["B"]
            vd = rows(w, "B.vendetta", "SCENE_VENDETTA")
            rep = [(r[0], r[4], r[5]) for r in rows(w, "player.rep.B", "RUMOR_DELIVERED")]
            reg = rows(w, "rep.region.common", "RUMOR_DELIVERED")
            ok("поражение игрока, B потеряла 2, игрок опознан: слух и падение репутации через rep_rumor_delay, вендетта B 20 суток (culprit player), объект остаётся у B, возврата нет",
               a.dead == 3 and b.dead == 2 and [(r[0], r[4], r[5]) for r in vd] == [(6, 0, p.vendetta_max)] and b.vendetta_culprit in ("player", None)
               and len(rep) == 1 and rep[0][0] == 6 + dly and rep[0][2] < rep[0][1] and reg
               and w.site(FORT).owner == "B" and not rows(w, f"site.{FORT}.owner") and not w.scene_returns and not rows(w, f"scene.return.{FORT}"),
               f"потери A {a.dead}, B {b.dead}, вендетта {[(r[0], r[4], r[5]) for r in vd]}, репутация {rep}, владелец {w.site(FORT).owner}")
            pre, a5, hz = {3: [("presence", FORT)]}, {5: [("A", FORT)]}, 6 + dly + 2
            qb = _mk(replace(p), hz, script={**pre, 6: [("scene_result", FORT, _loss(losses={"A": {"skittish": 3}}))]}, forced=a5)
            ok("поражение игрока без потерь у B: ни слуха, ни вендетты",
               qb.factions["A"].dead == 3 and qb.factions["B"].dead == 0 and not rows(qb, "B.vendetta", "SCENE_VENDETTA")
               and not rows(qb, "player.rep.B") and not _ev(qb, "rep_unidentified"),
               f"вендетта {rows(qb, 'B.vendetta', 'SCENE_VENDETTA')}, репутация {rows(qb, 'player.rep.B')}, слухи {_ev(qb, 'rep_unidentified')}")
            qm = _mk(replace(p), hz, script={**pre, 6: [("scene_result", FORT, _loss(masked=True))]}, forced=a5)
            ok("поражение игрока в маске без свидетелей: потери есть, вражды нет (слух безымянный)",
               qm.factions["B"].dead == 2 and not rows(qm, "B.vendetta", "SCENE_VENDETTA") and not rows(qm, "player.rep.B")
               and [e["tick"] for e in _ev(qm, "rep_unidentified")] == [6 + dly],
               f"вендетта {rows(qm, 'B.vendetta', 'SCENE_VENDETTA')}, слухи {[e['tick'] for e in _ev(qm, 'rep_unidentified')]}")
            qn = _mk(replace(p), hz, script={**pre, 6: [("scene_result", FORT, _loss(losses={"A": {"skittish": 1}}, named_dead=[("B", "B:офицер1", "player")]))]}, forced=a5)
            ok("поражение игрока, B потеряла только именного: вендетта B есть",
               not _alive(qn.factions["B"], "B:офицер1") and len(rows(qn, "B.vendetta", "SCENE_VENDETTA")) == 1,
               f"вендетта {rows(qn, 'B.vendetta', 'SCENE_VENDETTA')}")
            script = {1: [("presence", FORT)]}
            for t in (2, 7, 12):
                script[t] = [("scene_open", FORT), ("scene_result", FORT, _loss(losses={"B": {"skittish": 1}}))]
            qr = _mk(replace(p), 14, script=script)
            vr = rows(qr, "B.vendetta", "SCENE_VENDETTA")
            rr = rows(qr, "player.rep.B", "RUMOR_DELIVERED")
            ok("три проигранных нападения на владельца за 12 суток: вендетта выставлена один раз, не продлена; объект у владельца, возвратов нет; репутация падает; людей не больше, чем было",
               len(vr) == 1 and vr[0][0] == 2 and qr.factions["B"].dead == 3 and _tot(qr.factions["B"]) == 40 and qr.site(FORT).owner == "B"
               and not qr.scene_returns and not rows(qr, f"scene.return.{FORT}") and rr and all(r[5] < r[4] for r in rr),
               f"вендетта {[(r[0], r[4], r[5]) for r in vr]}, B мёртвых {qr.factions['B'].dead}, репутация {[(r[0], r[5]) for r in rr]}")
        else:   # SC17
            ev = _ev(w, "assault")
            q2 = _mk(w.p, 7, script={3: [("presence", FORT)], 6: [("scene_result", FORT, _res(winner="defender", player_side="defender"))]}, forced={5: [("A", FORT)]})
            ev2 = _ev(q2, "assault")
            ok("событие хранит, кто выиграл бы по числу, и перевернул ли игрок исход: игрок за слабого атакующего перевернул (flipped), игрок за оборону не менял",
               len(ev) == 1 and ev[0]["tick_would_win"] == "defender" and ev[0]["attacker_wins"] is True and ev[0]["flipped"] is True
               and len(ev2) == 1 and ev2[0]["tick_would_win"] == "defender" and ev2[0]["attacker_wins"] is False and ev2[0]["flipped"] is False,
               f"{[(e['tick_would_win'], e['attacker_wins'], e['flipped']) for e in ev + ev2]}")
        return res
    return f


for _sc in SC:
    S.EXTRA[_sc] = (build(_sc), _chk(_sc))

_ON = Params()
S.REVERSE_EXTRA.update({
    "R165": (replace(_ON, sc_bug_no_budget=True), ("SC8",), "проверка бюджета стороны выключена"),
    "R166": (replace(_ON, sc_bug_no_conserve=True), ("SC3",), "потери записываются в мёртвые с лишним человеком"),
    "R167": (replace(_ON, sc_bug_no_cost=True), ("SC7",), "цена победы не применяется"),
    "R168": (replace(_ON, sc_bug_leave_player=True), ("SC5",), "выход решается в пользу атакующего"),
    "R169": (replace(_ON, sc_bug_no_wake=True), ("SC11",), "присутствие не будит планету"),
    "R170": (replace(_ON, sc_bug_no_return=True), ("SC7",), "объект не возвращается"),
    "R171": (replace(_ON, sc_bug_no_close=True), ("SC12",), "сцена не закрывается после результата"),
    "R172": (replace(_ON, sc_bug_partial=True), ("SC10",), "потери применяются до проверки именных"),
    "R173": (replace(_ON, sc_bug_extend_vendetta=True), ("SC13",), "вендетта продлевается повторной сценой"),
    "R174": (replace(_ON, sc_bug_no_timeout=True), ("SC6",), "таймаут не срабатывает"),
    "R175": (replace(_ON, sc_bug_no_loss_enmity=True), ("SC18",), "при поражении стороны игрока вражда не создаётся"),
})
