"""Задача 24a: слой сцены (spec 24a). Двойник; Creation Kit, SFSE и плагин не описывает.

Игрок рядом с объектом: тик не считает штурм числом, а открывает сцену (расстановка и бюджеты); результат игры
возвращается действием ("scene_result", ...), записывается теми же путями, что числовой штурм; выход и таймаут
разрешает штурм числом. Все числа в twin/params.py (scene_*, метки там же). Без события «присутствие» модуль ничего не меняет.
"""
from .arith import fsum

KINDS = ("presence", "scene_open", "scene_result", "scene_leave")
BUCKETS = ("skittish", "ordinary", "steady")     # порядок записи потерь по ведрам: фиксированный
SIDES = ("attacker", "defender")
PHASE = 7


# ---------- расстановка (чистая функция, состояние не пишет) ----------
def setup(w, a, s, d):
    """Расстановка сцены: участники, на экране, запас, качество сторон, кто выиграл бы по числу (a = None: игрок нападает сам)."""
    p = w.p
    part = {d.name: min(d.manpower, w.crew(d, s) + p.defense_reinforcement)}
    if a is not None:
        part[a.name] = min(a.manpower, p.strike_group_max)
    on_screen = {k: min(v, p.scene_fighters_max) for k, v in part.items()}
    pressure = {k: part[k] - on_screen[k] for k in part}
    dfn = w.power(d) * p.defense_factor
    if a is not None:
        atk = w.power(a)
        quality = {a.name: min(atk / max(1e-9, dfn), p.scene_adv_cap), d.name: min(dfn / max(1e-9, atk), p.scene_adv_cap)}
        ratio = max(atk, dfn) / max(1e-9, min(atk, dfn))
        tick_wins = atk > dfn
    else:
        quality = {d.name: min(dfn / max(1.0, float(p.strike_group_max)), p.scene_adv_cap)}   # [предл] эталон нападающего: strike_group_max бойцов силы 1.0
        ratio = None
        tick_wins = None
    return dict(kind="assault" if a is not None else "strike", attacker=a.name if a is not None else None, defender=d.name,
                site=s.name, opened=w.tick, deadline=w.tick + p.scene_timeout, part=part, on_screen=on_screen, pressure=pressure,
                quality=quality, ratio=ratio, tick_attacker_wins=tick_wins)


# ---------- открытие ----------
def _open(w, a, s, d, forced):
    sc = setup(w, a, s, d)
    sc["forced"] = bool(forced)
    w.scenes[s.name] = sc
    w.rec(PHASE, "24", f"scene.{s.name}.state", None, "open", "SCENE_OPEN")
    for fname in sorted(sc["part"]):
        w.rec(PHASE, "24", f"scene.{s.name}.budget.{fname}", None, sc["part"][fname], "SCENE_OPEN")
    w.events.append(dict(tick=w.tick, kind="scene_opened", site=s.name, scene=sc["kind"], attacker=sc["attacker"], defender=sc["defender"]))
    return sc


def open_assault(w, a, s, d, forced):
    """Вызывается из assault() после общей преамбулы: штурм становится сценой."""
    _open(w, a, s, d, forced)


# ---------- закрытие ----------
def _close(w, site, how):
    sc = w.scenes.get(site)
    if sc is None:
        return
    if not (how == "result" and w.p.sc_bug_no_close):                          # R171: сцена не закрывается
        for fname in sorted(sc["part"]):
            w.rec(PHASE, "24", f"scene.{site}.budget.{fname}", sc["part"][fname], None, "SCENE_" + how.upper())
        w.rec(PHASE, "24", f"scene.{site}.state", "open", None, "SCENE_" + how.upper())
        del w.scenes[site]
    w.events.append(dict(tick=w.tick, kind="scene_closed", site=site, how=how))


def _stale(w, sc):
    """Мир ушёл от расстановки: объект сменил владельца или у стороны нет людей."""
    s = w.site(sc["site"])
    d = w.factions[sc["defender"]]
    if s.owner != sc["defender"] or d.manpower == 0:
        return True
    return sc["attacker"] is not None and w.factions[sc["attacker"]].manpower == 0


def _resolve_by_tick(w, sc, how):
    """Выход и таймаут: штурм числом, тем же кодом, что без игрока (spec 24a §1.5)."""
    if _stale(w, sc):
        _close(w, sc["site"], "void")
        return
    s = w.site(sc["site"])
    if sc["kind"] == "assault":
        a, d = w.factions[sc["attacker"]], w.factions[sc["defender"]]
        _close(w, sc["site"], how)
        if w.p.sc_bug_leave_player:                                              # R168: выход решён в пользу атакующего
            old = s.owner
            s.owner = a.name
            w.rec(PHASE, "13", f"site.{s.name}.owner", old, a.name, "ASSAULT")
            return
        w._assault_resolve(a, s, d, sc["forced"])
    else:
        _close(w, sc["site"], how)


# ---------- шаг тика: таймауты и возвраты ----------
def step(w):
    p = w.p
    if not p.sc_bug_no_timeout:                                                  # R174
        for site in sorted(w.scenes):
            sc = w.scenes[site]
            if sc["deadline"] <= w.tick:
                _resolve_by_tick(w, sc, "timeout")
    if p.sc_bug_no_return:                                                       # R170
        return
    for e in list(w.scene_returns):
        due, site, former = e
        if due > w.tick:
            continue
        w.scene_returns.remove(e)
        s = w.site(site)
        f = w.factions[former]
        if s.owner is None and f.manpower >= s.min_crew:
            w.rec(PHASE, "24", f"scene.return.{site}", due, None, "SCENE_RETURN")
            s.owner = former
            w.rec(PHASE, "13", f"site.{site}.owner", None, former, "SCENE_RETURN")
            w.events.append(dict(tick=w.tick, kind="scene_return", site=site, faction=former))
        else:
            w.rec(PHASE, "24", f"scene.return.{site}", due, None, "SCENE_RETURN_DROP")


def keep_active(w):
    """Пока игрок у объекта, планета отмечается активной (spec 24a §1.6)."""
    if w.scene_presence is not None and not w.p.sc_bug_no_wake:
        w._touch_site(w.site(w.scene_presence))


# ---------- действия игрока ----------
def act(w, a):
    p = w.p
    if not p.scene_enabled:
        raise ValueError(f"действие {a[0]} требует scene_enabled (spec 24a)")
    kind = a[0]
    if kind == "presence":
        return _presence(w, a[1])
    if kind == "scene_open":
        return _strike(w, a[1])
    if kind == "scene_leave":
        return _leave(w, a[1])
    return _result(w, a[1], a[2])


def _presence(w, site):
    if site is not None and site not in {s.name for s in w.sites}:
        return w._fail("presence", "NO_SITE", site=site)
    old = w.scene_presence
    w.scene_presence = site
    w.rec(PHASE, "24", "player.presence", "-" if old is None else old, "-" if site is None else site, "SCENE_PRESENCE")
    if site is not None and not w.p.sc_bug_no_wake:
        w._touch_site(w.site(site))


def _strike(w, site):
    """Игрок нападает на объект сам: сцена «игрок против владельца»."""
    if site not in {s.name for s in w.sites}:
        return w._fail("scene_open", "NO_SITE", site=site)
    if w.scene_presence != site:
        return w._fail("scene_open", "NOT_PRESENT", site=site)
    s = w.site(site)
    if s.owner is None or w.factions[s.owner].manpower == 0:
        return w._fail("scene_open", "NO_OWNER", site=site)
    if site in w.scenes or len(w.scenes) >= w.p.scene_open_max:
        return w._fail("scene_open", "SCENE_BUSY", site=site)
    w._touch_site(s)
    _open(w, None, s, w.factions[s.owner], False)


def _leave(w, site):
    sc = w.scenes.get(site)
    if sc is None:
        return w._fail("scene_leave", "NO_SCENE", site=site)
    _resolve_by_tick(w, sc, "leave")


# ---------- результат ----------
def _validate(w, sc, out):
    """Проверка без записи состояния. Возвращает (код отказа или None, подробности)."""
    p = w.p
    if not isinstance(out, dict):
        return "BAD_OUTCOME", {}
    winner = out.get("winner")
    side = out.get("player_side")
    if winner not in SIDES or side not in (None,) + SIDES:
        return "BAD_OUTCOME", {}
    if sc["kind"] == "strike" and side != "attacker":
        return "BAD_OUTCOME", {}
    losses = out.get("losses", {})
    if not isinstance(losses, dict) or any(k not in sc["part"] for k in losses):
        return "BAD_OUTCOME", {}
    for fname, bl in losses.items():
        if not isinstance(bl, dict) or any(b not in BUCKETS for b in bl) or any((not isinstance(n, int)) or n < 0 for n in bl.values()):
            return "BAD_OUTCOME", {}
        f = w.factions[fname]
        officers = fsum(1 for it in out.get("named_dead", ()) if len(it) == 3 and it[0] == fname and
                        next((n["role"] for n in f.named if n["name"] == it[1]), None) == "офицер")   # офицер выбывает из состава сверх потерь по ведрам (kill_named)
        tot = fsum(bl.values()) + officers
        if not p.sc_bug_no_budget and tot > sc["part"][fname]:
            return "OVER_BUDGET", dict(faction=fname)
        if any(n > getattr(f, b) for b, n in bl.items()):
            return "OVER_BUDGET", dict(faction=fname)
    seen = set()
    for item in out.get("named_dead", ()):
        if len(item) != 3 or item[0] not in sc["part"] or item[2] not in ("player", "side") or tuple(item[:2]) in seen:
            return "BAD_OUTCOME", {}
        seen.add(tuple(item[:2]))
        if item[2] == "player" and side is None:
            return "NOT_SIDE", {}
        if item[2] == "side" and sc["kind"] == "strike":
            return "BAD_OUTCOME", {}
    wit = out.get("witnesses", 1)
    if not isinstance(wit, int) or wit < 0 or not isinstance(out.get("masked", False), bool):
        return "BAD_OUTCOME", {}
    return None, {}


def _named_ok(w, out):
    """Именные: принадлежат стороне и живы."""
    for fname, name, _ in out.get("named_dead", ()):
        n = next((x for x in w.factions[fname].named if x["name"] == name), None)
        if n is None or not n["alive"]:
            return False
    return True


def _kill_buckets(w, f, bl):
    """Потери по ведрам: ведро → мёртвые; ярусы (04) тем же кодом, что в _move."""
    moved = 0
    for b in BUCKETS:
        n = bl.get(b, 0)
        if not n:
            continue
        w.setf(f, b, getattr(f, b) - n, PHASE, "03", "SCENE_RESULT")
        w.setf(f, "dead", f.dead + n + (1 if w.p.sc_bug_no_conserve else 0), PHASE, "03", "SCENE_RESULT")
        moved += n
    if moved:
        w.tier_remove(f, moved, PHASE)
    return moved


def _result(w, site, out):
    p = w.p
    sc = w.scenes.get(site)
    if sc is None:
        return w._fail("scene_result", "NO_SCENE", site=site)
    if _stale(w, sc):
        _close(w, site, "void")
        return
    code, kw = _validate(w, sc, out)
    if code:
        return w._fail("scene_result", code, site=site, **kw)
    s = w.site(site)
    d = w.factions[sc["defender"]]
    a = w.factions[sc["attacker"]] if sc["attacker"] is not None else None
    losses = out.get("losses", {})
    winner = out["winner"]
    side = out.get("player_side")
    masked = out.get("masked", False)
    wit = out.get("witnesses", 1)
    mp_before = {f.name: f.manpower for f in (a, d) if f is not None}
    comp0 = {f.name: w._comp(f) for f in (a, d) if f is not None}
    attacker_wins = winner == "attacker"
    win = a if attacker_wins else d            # в сцене игрока против владельца при победе игрока win = None (игрок не фракция)
    lose = d if attacker_wins else a
    if p.sc_bug_partial:                       # R172: потери применяются до проверки именных
        kl0 = _kill_buckets(w, lose, losses.get(lose.name, {})) if lose is not None else 0
        if not _named_ok(w, out):
            return w._fail("scene_result", "NO_NAMED", site=site)
    elif not _named_ok(w, out):
        return w._fail("scene_result", "NO_NAMED", site=site)
    # 1. потери по ведрам (проигравший, затем победитель), 2. шок
    kl = 0
    if lose is not None:
        kl = kl0 if p.sc_bug_partial else _kill_buckets(w, lose, losses.get(lose.name, {}))
    kw = _kill_buckets(w, win, losses.get(win.name, {})) if win is not None else 0
    sh = {}
    for f, k in ((lose, kl), (win, kw)):
        if f is not None:
            sh[f.name] = w.add_personnel_shock(f, k, mp_before[f.name], 1.0, PHASE, "SCENE_RESULT")
    if p.arc_enabled:
        for fx in (win, lose):
            if fx is not None:
                w._arc_after(fx, comp0[fx.name])
    # 3. удар по складу и трофей (06), как в штурме
    if attacker_wins and d.depot == s.name:
        w.depot_strike(d, s)
    moved_supply = 0.0
    if win is not None and lose is not None:
        moved_supply = lose.supply * p.trophy_rate
        w.setf(lose, "supply", lose.supply - moved_supply, PHASE, "06", "TROPHY")
        w.setf(win, "supply", win.supply + moved_supply, PHASE, "06", "TROPHY")
        w.setf(win, "armory", min(100.0, win.armory + lose.armory * p.trophy_armory_rate), PHASE, "06", "TROPHY")
    # 4. именные погибшие по готовому пути (21b); опознание по 02
    known = wit >= 1 and ((not masked) or p.rep_masked_identifies)
    for fname, name, by in out.get("named_dead", ()):
        if by == "player":
            culprit = "player" if known else None
        else:
            culprit = a.name if (a is not None and fname == d.name) else (d.name if a is not None and fname == a.name else None)
        w.kill_named(w.factions[fname], name, "SCENE_NAMED", PHASE, culprit=culprit)
    # 5. владелец объекта
    takes = attacker_wins and (a is not None or p.scene_strike_takes_site)
    if takes:
        new = a.name if a is not None else None
        old = s.owner
        s.owner = new
        w.rec(PHASE, "13", f"site.{site}.owner", old, new, "SCENE_RESULT")
    # 6. событие: обиды, знание и слухи читают его как числовой штурм
    if a is not None:
        flipped = attacker_wins != sc["tick_attacker_wins"]
        w.events.append(dict(
            tick=w.tick, kind="assault", forced=sc["forced"], attacker=a.name, defender=d.name,
            site=site, attacker_wins=attacker_wins, ratio=sc["ratio"],
            losses={lose.name: kl, win.name: kw}, manpower_before=mp_before, shock_inc=sh,
            supply_moved=moved_supply, scene=True, player_side=side,
            tick_would_win="attacker" if sc["tick_attacker_wins"] else "defender", flipped=flipped))
    else:
        w.events.append(dict(
            tick=w.tick, kind="scene_strike", defender=d.name, site=site, player_wins=attacker_wins,
            losses={d.name: kl if lose is d else kw}, manpower_before=mp_before, shock_inc=sh,
            player_side=side))
    # 7. цена победы: сторона игрока победила
    if side is not None and side == winner and not p.sc_bug_no_cost:
        _cost(w, s, a, d, side, known, masked, wit, strike_site_taken=takes and a is None)
    elif side is not None and side != winner and not p.sc_bug_no_loss_enmity:
        # 8. поражение стороны игрока (spec 24a-2): вражда, если игрок убил людей противника (потери по ведрам или именной); объекта и возврата нет
        if win is not None:
            o_named = fsum(1 for it in out.get("named_dead", ()) if it[0] == win.name)
            if kw + o_named > 0:
                _enmity(w, win, known, masked, wit)
    _close(w, site, "result")


def _cost(w, s, a, d, side, known, masked, wit, strike_site_taken):
    """Цена победы (spec 24a §1.4): слух по 02, вендетта без продления, возврат «ничьего» объекта."""
    p = w.p
    o = d if side == "attacker" else a                       # противник игрока
    if strike_site_taken:
        due = w.tick + p.scene_return_days
        w.scene_returns.append([due, s.name, d.name])
        w.rec(PHASE, "24", f"scene.return.{s.name}", None, due, "SCENE_RETURN_SET")
    if o is None:
        return
    _enmity(w, o, known, masked, wit)


def _enmity(w, o, known, masked, wit):
    """Вражда игрока к противнику o (spec 24a §1.4 п.4–5; при поражении стороны игрока spec 24a-2): слух по 02 и вендетта без продления."""
    p = w.p
    w._rep_kill(o.name, "scene", {"masked": masked, "witnesses": wit})
    if known and o.manpower > 0 and (o.vendetta == 0 or p.sc_bug_extend_vendetta):
        w.rec(PHASE, "24", f"{o.name}.vendetta", o.vendetta, p.vendetta_max, "SCENE_VENDETTA")
        o.vendetta, o.vendetta_culprit = p.vendetta_max, "player"
