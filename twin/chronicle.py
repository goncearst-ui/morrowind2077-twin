"""Задача 09: хроника двойника (spec 09). Чистая функция над world.log и world.events; мир не меняет."""

# Таблица следов: тип → то, что игрок мог заметить в кадре (docs/09, правило следа). Тип без следа не рендерится.
TRACE = {
    "T1": "13 + 12a — накладка владельца и следы боя",
    "T2": "12 — пустые койки, могилы",
    "T3": "01 — ступень снаряжения; 12 — штабель ящиков",
    "T4": "12a — накладка владельца",
    "T5": "12 — набор «сборы» до, новый набор после",
    "T6": "12 — чужая одежда в наборе",
    "T7": "12a — накладки владельцев активов",
    # кандидаты после G6 [предл]; следы по смыслу docs/09, перепроверить на G6
    "C1": "12 — ящики на новом складе",
    "C2": "12 — новый набор вожака на месте прежнего",
    "C3": "12 — набор «война» у обеих сторон",
}
CANDIDATES = ("C1", "C2", "C3")
ORDER = ("T1", "T4", "T7", "T5", "T6", "T2", "T3", "C1", "C2", "C3")


def _manpower_series(world):
    """Manpower по тикам, восстановленный из журнала назад от конечного состояния: {фракция: ({тик: М на конец тика}, стартовый)}."""
    rows = [r for r in world.log if r[3].rsplit(".", 1)[-1] in ("steady", "ordinary", "skittish") and r[3].split(".")[0] in world.factions]
    last = max([r[0] for r in world.log] + [world.tick])
    out = {}
    for n, f in world.factions.items():
        st = {"steady": f.steady, "ordinary": f.ordinary, "skittish": f.skittish}
        mine = [r for r in rows if r[3].split(".")[0] == n]
        ser = {}
        for t in range(last, -1, -1):
            ser[t] = sum(st.values())
            for r in reversed([x for x in mine if x[0] == t]):
                st[r[3].rsplit(".", 1)[-1]] = r[4]
        out[n] = (ser, sum(st.values()))
    return out


def strength(world, faction):
    """Крепость 0..100 для сводки; в формулах мира не используется. «Кошелёк» заменён армори [предл]."""
    f = world.factions[faction]
    total = len(world.sites)
    share = sum(1 for s in world.sites if s.owner == faction) / total if total else 0.0
    start = _manpower_series(world)[faction][1] or f.manpower
    people = min(1.0, f.manpower / start) if start else 0.0
    arm = f.armory / 100
    sup = min(1.0, f.days_supply / 30)
    if world.p.chronicle_bug_unnorm:
        people, sup = f.manpower / start if start else 0.0, f.days_supply / 30
    v = 100 * (0.3 * share + 0.3 * people + 0.2 * arm + 0.2 * sup)
    return v if world.p.chronicle_bug_unnorm else max(0.0, min(100.0, v))


def render(world):
    p = world.p
    rows = []

    def add(kind, tick, text, **kw):
        trace = TRACE.get(kind)
        if kind == "T3" and p.chronicle_bug_no_trace:
            trace = ""            # R109: шаблон без следа
        elif trace is None:
            return                # тип без следа не рендерится
        rows.append(dict(tick=tick, type=kind, text=text, trace=trace))

    captured = set()
    for e in world.events:
        k = e.get("kind")
        t = e.get("tick")
        if k == "assault":
            a, d, s = e["attacker"], e["defender"], e["site"]
            n = sum(e["losses"].values())
            if e["attacker_wins"]:
                captured.add((t, s))
            verb = "взяла" if e["attacker_wins"] else "не взяла"
            text = f"Тик {t}: {a} {verb} «{s}» у {d}; погибло {n}."
            if p.chronicle_bug_numbers:
                text = f"Тик {t}: {n}."
            reps = 1
            if p.chronicle_bug_dup:     # R112: по строке на каждую запись журнала тика
                reps = max(1, sum(1 for r in world.log if r[0] == t and r[3].split(".")[0] in (a, d)))
            for _ in range(reps):
                add("T1", t, text)
        elif k == "archetype_change":
            add("T5", t, f"{e['faction']} больше не {e['frm']}: теперь {e['to']}.")
        elif k == "absorb":
            add("T6", t, f"{e['faction']} приняла {e['n']} чужих.")
        elif k == "hegemon_change":
            new = e["new"]
            add("T7", t, "Планета спорная." if new == "Contested" else f"Под {new} теперь большая часть планеты.")
        elif p.chronicle_candidates and k == "depot_move":
            add("C1", t, f"{e['faction']} перенесла склад: было {e['frm']}, стало {e['to']}.")
        elif p.chronicle_candidates and k == "leader_killed":
            succ = next((r[5] for r in world.log if r[3] == f"{e['faction']}.leader" and r[0] >= t and r[5]), None)
            tail = f"преемник {succ}" if succ else "преемника нет"
            add("C2", t, f"У {e['faction']} погиб вожак {e['name']}; {tail}.")
        elif p.chronicle_candidates and k == "war_declared":
            add("C3", t, f"{e['initiator']} объявила войну {e['victim']}.")
        elif p.chronicle_candidates and k == "war_end":
            add("C3", t, f"Война {e['initiator']} и {e['victim']} окончена.")
    for r in world.log:   # T4: смена владельца без боя-события (захват уже рассказан T1)
        tg = r[3]
        if tg.startswith("site.") and tg.endswith(".owner") and r[4] != r[5]:
            s = tg[5:-6]
            if (r[0], s) in captured:
                continue
            if r[4] and r[5]:
                text = f"«{s}» перешёл от {r[4]} к {r[5]}."
            elif r[5]:
                text = f"«{s}» занят: хозяин {r[5]}."
            else:
                text = f"«{s}» остался без хозяина: ушла {r[4]}."
            add("T4", r[0], text)
    thr = p.hunger_threshold
    if thr > 0:
        for r in world.log:   # T3: пересечение порога снабжения вниз
            if r[3].endswith(".days_supply") and r[4] is not None and r[4] >= thr > r[5]:
                add("T3", r[0], f"У {r[3].split('.')[0]} кончается снабжение: хватит на {int(r[5])} суток.")
    for n, (ser, _) in _manpower_series(world).items():   # T2: падение людей за окно
        last_t = -10**6
        for t in sorted(ser):
            ref = max([ser[x] for x in range(max(0, t - p.chronicle_window), t) if x in ser] or [0])
            if ref > 0 and (ref - ser[t]) / ref >= p.chronicle_people_drop and t - last_t > p.chronicle_window:
                add("T2", t, f"У {n} стало меньше людей: было {ref}, стало {ser[t]}.")
                last_t = t
    if p.chronicle_bug_mutate:    # R110: render() пишет в журнал
        world.log.append((world.tick, 0, "09", "chronicle", 0, 1, "BUG"))
    rows.sort(key=lambda r: (r["tick"], ORDER.index(r["type"])))
    return rows
