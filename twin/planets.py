"""Задача 23c: фабрика мира с несколькими планетами (spec 23). Двойник; Creation Kit не описывает."""
from dataclasses import replace

from . import integration as I
from . import scenarios as S
from .model import Planet, Site, World
from .named import named_roster

FACTIONS = (("Метрополия", "Контролёры"), ("Налётчики", "Хищники"), ("Колония", "Хранители"), ("Дрейф", "Дрейфующие"))


def planet_world(p, n_planets=20, named=0, multi=True, off=(), y1=90, y2=40, dos=30):
    """Четыре фракции, n_planets планет по два объекта; объекты раздаются по кругу, дома фракций на первых четырёх планетах;
    все флаги *_enabled включены (кроме off), multi_planet_enabled = multi. Без случайности. Возвращает (мир, выключенные)."""
    q, cut = I.all_on(p, off)
    q = replace(q, multi_planet_enabled=multi)
    if named:
        q = replace(q, named_max=max(q.named_max, named))
    pn = [f"П{i:02d}" if n_planets < 100 else f"П{i:04d}" for i in range(1, n_planets + 1)]
    sites, owners = [], [n for n, _ in FACTIONS]
    for k, name in enumerate(pn):
        sites.append(Site(f"{name}-1", 20, y1, 2, owner=owners[k % 4], region=name))
        sites.append(Site(f"{name}-2", 20, y2, 2, owner=owners[(k + 1) % 4], region=name))
    owned = {n: sum(1 for s in sites if s.owner == n) for n in owners}
    fs = {n: S.faction(q, n, a, 3 * owned[n] + 40, dos, 20 * owned[n]) for n, a in FACTIONS}
    for i, n in enumerate(owners):
        fs[n].home = pn[i]
    planets = {name: Planet(name, (name,)) for name in pn}
    w = World(fs, sites, q, planets=planets)
    if named:
        for n in owners:
            w.factions[n].named = named_roster(n, named, q)
            w.factions[n].leader = f"{n}:вожак"
    for f in w.factions.values():
        w.publish_dos(f, phase=0)
    return w, cut
