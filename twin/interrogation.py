"""Задача 19: допрос пленного (spec 19). Двойник считает арифметику; Creation Kit не описывает. Модуль листовой: сам в мир не пишет, вызывает чужие правила."""


def label_of(p, bucket, label=None):
    return p.interrogation_bucket_label[bucket] if label is None else label


def fear_of(p, label, pressure, morale, fear_named=0.0):
    """Страх допроса = база по ярлыку + давление × step_pressure + (100 − мораль) × morale_k [+ Fear именного]."""
    return p.interrogation_base[label] + pressure * p.step_pressure + (100.0 - morale) * p.morale_k + fear_named


def outcome_of(p, label, fear, morale, paid=False):
    """truth | lie | trap | silent (spec 19 п. 4)."""
    if fear < p.talk_threshold:
        return "silent"
    if label == "Упёртый":
        return "truth" if (morale < p.stubborn_morale or p.int_bug_stubborn_talks) else "silent"
    if label == "Вспыльчивый":
        return "lie" if fear < p.lie_fear_cap else "truth"
    if label == "Хладнокровный":
        return "trap"
    if label == "Бродяга":
        return "truth" if paid else "silent"
    return "truth"   # Пугливый и без ярлыка


def act(w, a: dict):
    p = w.p
    do = a.get("do")
    if not p.interrogation_enabled:
        return w._fail(do or "?", "DISABLED")
    if do == "capture":
        return capture(w, a)
    rec = w.prisoners.get(a.get("id"))
    if rec is None or rec["state"] != "held":
        raise ValueError(f"пленного {a.get('id')} нет или он уже не в плену")
    if do == "interrogate":
        return interrogate(w, rec, a)
    if do in ("release", "hand_over", "execute"):
        return finish(w, rec, do, a)
    raise ValueError(f"неизвестное действие допроса: {do}")


def capture(w, a):
    p = w.p
    f = w.factions[a["target"]]
    b = a["bucket"]
    if b not in ("skittish", "ordinary", "steady") or getattr(f, b) < 1:
        raise ValueError(f"в ведре {b} фракции {f.name} нет людей")
    by = a.get("by")
    if by not in w.factions or by == f.name:
        raise ValueError("capture: нужна фракция игрока by, отличная от цели")
    w.prison_seq += 1
    n = w.prison_seq
    label = label_of(p, b, a.get("label"))
    w.setf(f, b, getattr(f, b) - 1, 7, "03", "CAPTURE")
    if not p.int_bug_uncounted:
        w.setf(f, "held", f.held + 1, 7, "03", "CAPTURE")
    w.tier_remove(f, 1, 7)
    w.prisoners[n] = dict(id=n, faction=f.name, bucket=b, label=label, by=by, state="held", fear=fear_of(p, label, 0, f.morale), done=False)
    w.rec(7, "19", f"prisoner.{n}.state", None, "held", "CAPTURE")


def interrogate(w, rec, a):
    p = w.p
    if rec["done"] and not p.int_bug_repeat:
        raise ValueError(f"пленный {rec['id']} уже допрошен: один секрет на пленного (spec 19)")
    f = w.factions[rec["faction"]]
    fear = fear_of(p, rec["label"], a.get("pressure", 0), f.morale)
    out = outcome_of(p, rec["label"], fear, f.morale, a.get("paid", False))
    site = f.depot if (f.depot in {s.name for s in w.sites}) else None
    if out == "trap":
        if site is None:
            out = "silent"
        elif len(w.traps) >= p.max_traps and site not in w.traps:
            raise ValueError(f"ловушек не больше {p.max_traps} на мир (spec 19)")
    rec["fear"], rec["done"] = fear, True
    w.rec(7, "19", f"prisoner.{rec['id']}.outcome", None, out, "INTERROGATE")
    ev = dict(kind="interrogation", tick=w.tick, id=rec["id"], faction=f.name, by=rec["by"], outcome=out, fear=fear)
    if out == "truth" and site is not None:
        w._know_set(rec["by"], site, f.name, "INTERROGATE_TRUE")
    elif out == "lie":
        w.events.append(dict(kind="interrogation_lie", tick=w.tick, id=rec["id"], faction=f.name))
        if p.int_bug_lie_knowledge and site is not None:
            w._know_set(rec["by"], site, f.name, "INTERROGATE_TRUE")
    elif out == "trap":
        w.traps[site] = rec["by"]
        w.rec(7, "19", f"trap.{site}", None, rec["by"], "INTERROGATE_TRAP")
    w.events.append(ev)


def finish(w, rec, do, a):
    p = w.p
    f = w.factions[rec["faction"]]
    mp0 = f.manpower
    rec["state"] = {"release": "released", "hand_over": "handed", "execute": "executed"}[do]
    w.rec(7, "19", f"prisoner.{rec['id']}.state", "held", rec["state"], do.upper())
    w.setf(f, "held", f.held - 1, 7, "03", do.upper())
    if do == "release":
        if rec["fear"] >= p.talk_threshold and not p.int_bug_scared_returns:
            w.setf(f, "deserted", f.deserted + 1, 7, "03", "RELEASED_DESERTED")
        else:
            w.setf(f, rec["bucket"], getattr(f, rec["bucket"]) + 1, 7, "03", "RELEASED_SUSPECT")
            w.tier_add(f, (1, 0, 0), 7)
            w.setf(f, "shock", f.shock + p.purge_shock, 7, "04", "RELEASED_SUSPECT")
    elif do == "hand_over":
        w.setf(f, "captured", f.captured + 1, 7, "03", "CAPTURED")
    else:
        w.setf(f, "dead", f.dead + 1, 7, "03", "EXECUTE")
        w.add_personnel_shock(f, 1, mp0 + 1, 1.0, 7, "EXECUTE")
        if p.reputation_enabled:
            w._rep_kill(f.name, f"prisoner{rec['id']}", {"masked": a.get("masked", False), "witnesses": a.get("witnesses", 0)})
