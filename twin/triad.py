"""Задача 17: триада профилей (spec 17) — фабрика мира из трёх фракций с разными целями и характерами лидеров. Новой механики нет."""
from dataclasses import replace

from .extra import clean
from .model import Site, World
from . import scenarios as S

M, K, F = "Метрополия", "Колония", "Тропа"   # Метрополия, Колония-проект, Вольная Тропа
LEADERS = {   # [док 17] трейты лидеров по видам
    "negotiator_m": ("Openness_High",),
    "hawk": ("Conscientiousness_High", "Agreeableness_Low"),
    "colony": ("Conscientiousness_High",),
    "negotiator_f": ("Agreeableness_High",),
    "radical": ("Agreeableness_Low", "Neuroticism_High"),
}


def triad_params(p, **kw):
    base = dict(evolution_enabled=True, leader_enabled=True, npc_state_enabled=True, obj_enabled=True, strategy_enabled=True,
                inheritance_enabled=True, relations_enabled=True, knowledge_enabled=True, wars_enabled=True, evo_rule_order=())
    q = replace(clean(p), **{**base, **kw})
    return replace(q, archetype_assault_threshold={"Хищники": 1.1, "Контролёры": 1.6})   # clean обнуляет карту порогов, а война читает её (spec 08b)


def triad(p, leaders=("hawk", "radical"), goal_m=3, vassal=False, n=(66, 50, 35), dos=(8.0, 30.0, 20.0)):
    """leaders = (лидер Метрополии: "negotiator" | "hawk", лидер Тропы: "negotiator" | "radical"). Без случайности.
    Возвращает (мир, профили). Размеры, объекты и запасы — [предл] (spec 17 п. 5)."""
    q = triad_params(p)
    if p.tri_bug_ignore_goal:
        goal_m = 0
    if p.tri_bug_same_leaders:
        leaders = ("hawk", "radical")
    if vassal:
        q = replace(q, obj_vassal_pairs=((M, F),))
        if p.tri_bug_vassal_h:
            q = replace(q, rel_level_cuts=(0.5, 2.0, 4.0, 6.0))   # R143: флаг заодно сдвигает уровни отношений
    ss = [Site("Метро-1", 40, 90, 4, owner=M, region="Центр"), Site("Узел", 20, 60, 2, owner=M, region="Центр"),
          Site("Тропа-1", 15, 35, 2, owner=F, region="Центр"), Site("Колония-1", 20, 60, 2, owner=K, region="Колония")]
    fs = {M: S.faction(q, M, "Контролёры", n[0], dos[0], 60), K: S.faction(q, K, "Хранители", n[1], dos[1], 20), F: S.faction(q, F, "Контролёры", n[2], dos[2], 15)}
    fs[K].home = "Колония"
    fs[M].home = fs[F].home = "Центр"
    fs[K].doctrine = 2
    w = World(fs, ss, q)
    lm = "negotiator_m" if leaders[0] == "negotiator" else leaders[0]
    lf = "negotiator_f" if leaders[1] == "negotiator" else leaders[1]
    for fid, kind in ((M, lm), (K, "colony"), (F, lf)):
        S.give_named(w, fid)
        w.factions[fid].named[0]["traits"] = LEADERS[kind]
    if p.tri_bug_colony_lever:
        w.forced_assaults = {10: [(F, "Колония-1")]}
    w.known_at_start = {M: ("Тропа-1",), F: ("Узел", "Метро-1")}
    sets = [lambda w: w.set_objective(M, goal_m, "Тропа-1", F) if goal_m else None,
            lambda w: w.set_objective(K, 2, None, None),
            lambda w: w.set_objective(F, 5, "Узел", M)]
    w.scheduled.setdefault(1, [])[0:0] = sets
    for fx in w.factions.values():
        w.publish_dos(fx, phase=0)
    profiles = {M: dict(archetype="Контролёры", doctrine=0, objective=goal_m, leader=leaders[0]), K: dict(archetype="Хранители", doctrine=2, objective=2, leader="colony"),
                F: dict(archetype="Контролёры", doctrine=0, objective=5, leader=leaders[1])}
    return w, profiles
