"""Задача 10: стенд сверки озвучки (spec 10). Мир только читается; языковой модели нет. Источник шаблонов хроники — twin/chronicle.py."""
import copy

from .chronicle import _manpower_series, render
from .objective import NAMES

FALSE_ARCH = {"Хищники": "Контролёры"}


def _depots(world, faction):
    out = {}
    for (kf, site), owner in sorted(world.know.items()):
        if kf == faction and owner in world.factions and world.factions[owner].depot == site:
            out[f"depot.{owner}"] = site
    return out


def facts(world, faction, npc=None):
    """Утверждения о фракции, которые говорящему можно знать: свои оси и цель, трейты вожака, записная книжка. Чужой склад — только из know."""
    f, p = world.factions[faction], world.p
    leader = next((n for n in f.named if n["name"] == f.leader), None) if f.leader else None
    d = {"_version": p.voice_template_version, "faction": faction, "tick": world.tick, "archetype": f.archetype, "doctrine": f.doctrine,
         "axis_R": f.ax_r, "axis_P": f.ax_p, "axis_C": f.ctl, "axis_M": f.morale,
         "leader": f.leader, "leader_status": "alive" if f.leader else ("dead" if f.named else "none"), "captured": f.captured}
    if p.obj_enabled:
        d["objective"], d["obj_stage"] = f.objective, f.obj_stage
    if leader is not None and "traits" in leader:
        d["leader_traits"] = tuple(leader["traits"])
    for (kf, site), owner in sorted(world.know.items()):
        if kf == faction:
            d[f"know.{site}"] = owner
    d.update(_depots(world, faction))
    if p.voice_bug_leak_depot:   # R138
        for g, fg in world.factions.items():
            if g != faction and fg.depot:
                d[f"depot.{g}"] = fg.depot
    if npc is not None:
        n = next(x for x in f.named if x["name"] == npc)
        d["npc"], d["npc_role"], d["npc_traits"] = npc, n["role"], tuple(n.get("traits", ()))
    if p.voice_bug_facts:   # R136
        d["archetype"] = FALSE_ARCH.get(f.archetype, "Хищники")
    return d


def render_prompt(fx):
    version = fx.get("_version", "v1")
    head = [f"[голос {version}]", "Говори только по списку фактов ниже. Не придумывай фактов, которых в списке нет."]
    return "\n".join(head + [f"{k} = {fx[k]!r}" for k in sorted(fx) if not k.startswith("_")])


def _oracle(world, faction, key):
    """Ожидание из состояния мира для ключа утверждения: (говорящему можно знать, значение)."""
    f = world.factions[faction]
    raw = {"archetype": f.archetype, "doctrine": f.doctrine, "axis_R": f.ax_r, "axis_P": f.ax_p, "axis_C": f.ctl, "axis_M": f.morale,
           "leader": f.leader, "captured": f.captured, "objective": f.objective, "obj_stage": f.obj_stage}
    if key in raw:
        return True, raw[key]
    if key.startswith("know."):
        v = world.know.get((faction, key[5:]))
        return v is not None, v
    if key.startswith("depot."):
        g = key[6:]
        site = world.factions[g].depot if g in world.factions else None
        known = site is not None and world.know.get((faction, site)) == g
        return known, site if known else None
    return False, None


def _event_ok(world, kind, tick, target):
    ev = world.events
    if kind == "assault":
        return any(e["kind"] == "assault" and e["tick"] == tick and target in (e["site"], e["attacker"], e["defender"]) for e in ev)
    if kind == "archetype_change":
        return any(e["kind"] == kind and e["tick"] == tick and e["faction"] == target for e in ev)
    if kind == "hegemon_change":
        return any(e["kind"] == kind and e["tick"] == tick for e in ev)
    if kind == "absorb":
        return any(e["kind"] == kind and e["tick"] == tick and e["faction"] == target for e in ev)
    if kind == "owner":
        return any(r[0] == tick and r[3] == f"site.{target}.owner" for r in world.log)
    if kind == "supply_cross":
        thr = world.p.hunger_threshold
        return any(r[0] == tick and r[3] == f"{target}.days_supply" and r[4] is not None and r[4] >= thr > r[5] for r in world.log)
    if kind == "people_drop":
        ser = _manpower_series(world).get(target, ({}, 0))[0]
        w = world.p.chronicle_window
        ref = max([ser[x] for x in range(max(0, tick - w), tick) if x in ser] or [0])
        return tick in ser and ref > 0 and (ref - ser[tick]) / ref >= world.p.chronicle_people_drop
    return False


def verify(statements, world, log=None):
    """Список расхождений. Утверждение: ("fact", фракция, ключ, значение) или ("event", вид, тик, цель)."""
    if world.p.voice_bug_verify_pass:   # R137
        return []
    out = []
    for st in statements:
        if st[0] == "fact":
            _, fac, key, val = st
            known, exp = _oracle(world, fac, key)
            if not known:
                out.append(dict(statement=st, expected="говорящему это неизвестно"))
            elif exp != val:
                out.append(dict(statement=st, expected=exp))
        elif st[0] == "event":
            _, kind, tick, target = st
            if not _event_ok(world, kind, tick, target):
                out.append(dict(statement=st, expected="такого события в журнале нет"))
        else:
            out.append(dict(statement=st, expected="неизвестный вид утверждения"))
    return out


def stub_voice(world, faction):
    """Заглушка-озвучиватель: строки по шаблонам хроники (09) и фактам; к каждой приложено проверяемое утверждение."""
    fx = facts(world, faction)
    lines = [dict(text=f"Мы — {fx['archetype']}.", statement=("fact", faction, "archetype", fx["archetype"]))]
    if "objective" in fx:
        lines.append(dict(text=f"Наша цель — {NAMES[fx['objective']]}.", statement=("fact", faction, "objective", fx["objective"])))
    for r in render(world):
        if faction not in r["text"]:
            continue
        t, tk, txt = r["type"], r["tick"], r["text"]
        st = None
        if t == "T1":
            e = next((e for e in world.events if e["kind"] == "assault" and e["tick"] == tk and f"«{e['site']}»" in txt), None)
            st = ("event", "assault", tk, e["site"]) if e else None
        elif t == "T4":
            s = next((s.name for s in world.sites if f"«{s.name}»" in txt), None)
            st = ("event", "owner", tk, s) if s else None
        elif t == "T5":
            st = ("event", "archetype_change", tk, faction)
        elif t == "T7":
            st = ("event", "hegemon_change", tk, "")
        elif t == "T2":
            st = ("event", "people_drop", tk, faction)
        elif t == "T3":
            st = ("event", "supply_cross", tk, faction)
        elif t == "T6":
            st = ("event", "absorb", tk, faction)
        if st:
            lines.append(dict(text=txt, statement=st))
    return lines


def assert_read_only(world, fn):
    """Вызывает fn() и сравнивает журнал, события, фракции, объекты, знание и тик до и после; различие — AssertionError."""
    def snap():
        return (copy.deepcopy(world.log), copy.deepcopy(world.events), repr(world.factions), repr(world.sites), world.tick, dict(world.know), dict(world.regions), repr(world.rel) if hasattr(world, "rel") else None)
    before = snap()
    out = fn()
    after = snap()
    names = ("журнал", "события", "фракции", "объекты", "тик", "знание", "регионы", "отношения")
    bad = [n for n, a, b in zip(names, before, after) if a != b]
    assert not bad, f"озвучка изменила мир: {bad}"
    return out
