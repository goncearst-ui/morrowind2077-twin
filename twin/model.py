"""Двойник v0: состояние, фазы тика, штурм.

Без случайности. Без людей поштучно: только счётчики вёдер (03).
Каждое изменение пишется в журнал (11 S2d): tick, phase, module, target, old, new, reason_code.
"""
from dataclasses import dataclass, field
from math import floor

from .params import Params

BUCKETS_ALIVE = ("steady", "ordinary", "skittish")


@dataclass
class Site:
    name: str
    base_cost: float
    yield_: float
    min_crew: int
    owner: str | None = None
    income_disabled: bool = False  # сценарий «потеря узла»


@dataclass
class Faction:
    name: str
    archetype: str
    steady: int
    ordinary: int
    skittish: int
    supply: float
    armory: float
    morale: float = 60.0           # [предл] стартовое
    hunger_debt: float = 0.0
    shock: float = 0.0
    dead: int = 0
    deserted: int = 0
    days_supply: float = 0.0       # публикуемая производная (фаза 4)
    last_assault: int = -10**6
    last_raid: int = -10**6

    @property
    def manpower(self) -> int:
        return self.steady + self.ordinary + self.skittish

    def steadfast(self, p: Params) -> float:
        if self.manpower == 0:
            return 0.0
        w = p.steadfast_weights
        return (w[0] * self.steady + w[1] * self.ordinary + w[2] * self.skittish) / self.manpower


@dataclass
class World:
    factions: dict
    sites: list
    p: Params
    tick: int = 0
    log: list = field(default_factory=list)
    events: list = field(default_factory=list)   # события для метрик (штурмы, дезертирство, сдача)
    forced_assaults: dict = field(default_factory=dict)  # tick -> [(attacker, site_name)]
    scheduled: dict = field(default_factory=dict)        # tick -> [callable(world)]
    prosperity: float | None = None                      # TF_RegionProsperity (06), один регион

    def __post_init__(self):
        if self.prosperity is None:
            self.prosperity = self.p.region_start

    def set_region(self, value, phase, reason):
        old = self.prosperity
        self.prosperity = max(0.0, min(self.p.region_max, value))
        self.rec(phase, "06", "region.prosperity", old, self.prosperity, reason)

    # ---------- журнал ----------
    def rec(self, phase, module, target, old, new, reason):
        if old == new:
            return
        self.log.append((self.tick, phase, module, target,
                         round(old, 4) if isinstance(old, float) else old,
                         round(new, 4) if isinstance(new, float) else new, reason))

    def setf(self, f: Faction, attr, value, phase, module, reason):
        old = getattr(f, attr)
        setattr(f, attr, value)
        self.rec(phase, module, f"{f.name}.{attr}", old, value, reason)

    # ---------- 03: вёдра ----------
    def _move(self, f: Faction, n: int, order: str, dest: str, phase, reason) -> int:
        seq = ("skittish", "ordinary", "steady") if order == "skittish_first" else ("steady", "ordinary", "skittish")
        moved = 0
        for b in seq:
            if moved >= n:
                break
            take = min(getattr(f, b), n - moved)
            if take:
                self.setf(f, b, getattr(f, b) - take, phase, "03", reason)
                self.setf(f, dest, getattr(f, dest) + take, phase, "03", reason)
                moved += take
        return moved

    def kill_many(self, f, n, phase, reason):
        return self._move(f, n, self.p.drain_order, "dead", phase, reason)

    def remove_many(self, f, n, phase, reason):
        return self._move(f, n, self.p.desertion_order, "deserted", phase, reason)

    # ---------- 04: шок ----------
    def add_personnel_shock(self, f: Faction, lost: int, manpower_before: int, weight, phase, reason):
        if manpower_before <= 0 or lost <= 0:
            return 0.0
        raw = lost / manpower_before * 100 * weight
        inc = min(raw, self.p.shock_event_cap)
        self.setf(f, "shock", f.shock + inc, phase, "04", reason)
        return inc

    # ---------- площадки ----------
    def owned(self, f: Faction):
        return [s for s in self.sites if s.owner == f.name]

    def staffed(self, f: Faction):
        """Какие площадки укомплектованы. Трактовка v0: люди распределяются
        по площадкам в порядке убывания дохода, каждой нужно MinCrew."""
        left = f.manpower
        out = []
        for s in sorted(self.owned(f), key=lambda s: -s.yield_):
            if left >= s.min_crew:
                out.append(s)
                left -= s.min_crew
        return out

    def crew(self, f: Faction, site: Site) -> int:
        return min(f.manpower, site.min_crew + 2)

    def expense(self, f: Faction) -> float:
        base = sum(s.base_cost for s in self.owned(f))
        return (base + f.manpower * self.p.per_head_cost) * self.p.archetype_cost_mult[f.archetype]

    def publish_dos(self, f: Faction, phase=4):
        e = self.expense(f)
        dos = f.supply / e if e > 0 else 999.0
        self.setf(f, "days_supply", dos, phase, "00", "PUBLISH")

    # ---------- тик ----------
    def step(self):
        self.tick += 1
        for fn in self.scheduled.get(self.tick, []):
            fn(self)
        fs = list(self.factions.values())
        # фаза 1 — затухание шока, восстановление региона
        for f in fs:
            self.setf(f, "shock", max(0.0, f.shock - self.p.shock_decay_per_tick), 1, "04", "DECAY")
        self.set_region(self.prosperity + self.p.region_recovery, 1, "REGION_RECOVERY")
        # фаза 2 — приход и расход; пошлина беднит регион (TollDrag, 06)
        for f in fs:
            paying = [s for s in self.staffed(f) if not s.income_disabled]
            income = sum(s.yield_ for s in paying)
            for s in paying:
                self.set_region(self.prosperity - s.yield_ * self.p.toll_drag, 2, "TOLL_DRAG")
            new = max(0.0, f.supply + income - self.expense(f))
            self.setf(f, "supply", new, 2, "06", "UPKEEP")
        # фаза 3 — голод и дезертирство (читает DaysOfSupply прошлого тика)
        for f in fs:
            self.hunger(f)
        # фаза 4 — производные
        for f in fs:
            self.publish_dos(f)
        # фаза 7 — решения
        for f in fs:
            self.surrender(f)
        for atk_name, site_name in self.forced_assaults.get(self.tick, []):
            self.assault(self.factions[atk_name], self.site(site_name), forced=True)
        for f in fs:
            self.decide_assault(f)
        for f in fs:
            self.raid(f)

    # ---------- 06 S3: налёт на регион ----------
    def raid(self, f: Faction):
        p = self.p
        if not p.raids_enabled or f.archetype not in p.raiding_archetypes or f.manpower == 0:
            return
        if self.tick - f.last_raid < p.raid_cooldown:
            return
        f.last_raid = self.tick
        loot = self.prosperity * p.raid_yield
        to_pool = loot * (1 - p.share_rate[f.archetype])
        self.setf(f, "supply", f.supply + to_pool, 7, "06", "RAID")
        self.set_region(self.prosperity - p.raid_cost, 7, "RAID")
        self.events.append(dict(tick=self.tick, kind="raid", faction=f.name, loot=loot,
                                to_pool=to_pool, manpower=f.manpower))

    def site(self, name):
        return next(s for s in self.sites if s.name == name)

    # ---------- 06: голод ----------
    def hunger(self, f: Faction):
        p = self.p
        if f.manpower == 0:
            return
        if f.days_supply < p.hunger_threshold:
            gap = p.hunger_threshold - f.days_supply
            self.setf(f, "hunger_debt", f.hunger_debt + gap, 3, "06", "HUNGER")
            self.setf(f, "morale", max(0.0, f.morale - p.morale_hunger_k * gap), 3, "06", "HUNGER")
        else:
            self.setf(f, "hunger_debt", max(0.0, f.hunger_debt - p.hunger_recovery), 3, "06", "RECOVER")
        before = f.manpower
        left = 0
        while f.hunger_debt >= p.desertion_cost and f.manpower > 0:
            if p.desertion_cap_per_tick is not None and left >= p.desertion_cap_per_tick:
                break
            left += self.remove_many(f, 1, 3, "DESERTION")
            self.setf(f, "hunger_debt", f.hunger_debt - p.desertion_cost, 3, "06", "DESERTION")
        if left:
            self.add_personnel_shock(f, left, before, p.desertion_shock_weight, 3, "DESERTION")
            self.events.append(dict(tick=self.tick, kind="desertion", faction=f.name, n=left))

    # ---------- 06 S5: сдача актива ----------
    def surrender(self, f: Faction):
        if f.manpower == 0 or f.days_supply >= self.p.surrender_dos:
            return
        owned = self.owned(f)
        free = [s for s in self.sites if s.owner is None]
        if not owned or not free:
            return
        dear = max(owned, key=lambda s: s.base_cost)
        cheap = min(free, key=lambda s: s.base_cost)
        if cheap.base_cost >= dear.base_cost:
            return
        dear.owner, cheap.owner = None, f.name
        self.rec(7, "06", f"site.{dear.name}.owner", f.name, None, "SURRENDER")
        self.rec(7, "06", f"site.{cheap.name}.owner", None, f.name, "SURRENDER")
        self.events.append(dict(tick=self.tick, kind="surrender", faction=f.name,
                                frm=dear.name, to=cheap.name, manpower=f.manpower))

    # ---------- 13: решение о штурме ----------
    def visible_power(self, f: Faction) -> float:
        # атакующий не видит стойкость противника (13)
        return f.manpower * (0.5 + f.armory / 100)

    def power(self, f: Faction) -> float:
        return f.manpower * (0.5 + f.armory / 100) * (0.6 + 0.8 * f.steadfast(self.p) / 100)

    def decide_assault(self, f: Faction):
        p = self.p
        thr = p.archetype_assault_threshold.get(f.archetype)
        if thr is None or f.manpower == 0:
            return
        if f.days_supply >= p.assault_dos or f.armory < p.assault_armory_min:
            return
        if self.tick - f.last_assault < p.assault_cooldown:
            return
        targets = [s for s in self.sites if s.owner not in (None, f.name)]
        for s in sorted(targets, key=lambda s: (-s.yield_, s.name)):
            d = self.factions[s.owner]
            ratio = self.visible_power(f) / max(1e-9, self.visible_power(d) * p.defense_factor)
            if ratio > thr:
                self.assault(f, s, forced=False)
                return

    # ---------- 13: разрешение штурма ----------
    def assault(self, a: Faction, s: Site, forced: bool):
        p = self.p
        d = self.factions[s.owner]
        a.last_assault = self.tick
        atk, dfn = self.power(a), self.power(d) * p.defense_factor
        attacker_wins = atk > dfn
        win, lose = (a, d) if attacker_wins else (d, a)
        # Трактовка v0: в 13 «÷ СоотношениеСил» записано для победы атакующего;
        # для победы обороны берём соотношение победитель/проигравший (всегда ≥ 1).
        ratio = max(atk, dfn) / max(1e-9, min(atk, dfn))
        part = {a.name: min(a.manpower, p.strike_group_max),
                d.name: self.crew(d, s) + p.defense_reinforcement}
        mp_before = {a.name: a.manpower, d.name: d.manpower}
        if p.old_loss_formula:
            loser_loss = floor(0.5 * lose.manpower)
            winner_loss = floor(0.5 * lose.manpower / ratio)
        else:
            loser_loss = floor(min(0.5 * part[lose.name], p.assault_loss_cap * lose.manpower))
            # Трактовка v0: победитель не теряет больше, чем участвовало с его стороны.
            winner_loss = min(floor(loser_loss / ratio), part[win.name])
        kl = self.kill_many(lose, loser_loss, 7, "ASSAULT")
        kw = self.kill_many(win, winner_loss, 7, "ASSAULT")
        sh = {}
        for f, k in ((lose, kl), (win, kw)):
            sh[f.name] = self.add_personnel_shock(f, k, mp_before[f.name], 1.0, 7, "ASSAULT")
        # трофей (06)
        moved_supply = lose.supply * p.trophy_rate
        self.setf(lose, "supply", lose.supply - moved_supply, 7, "06", "TROPHY")
        self.setf(win, "supply", win.supply + moved_supply, 7, "06", "TROPHY")
        self.setf(win, "armory", min(100.0, win.armory + lose.armory * p.trophy_armory_rate), 7, "06", "TROPHY")
        if attacker_wins:
            s.owner = a.name
            self.rec(7, "13", f"site.{s.name}.owner", d.name, a.name, "ASSAULT")
        self.events.append(dict(
            tick=self.tick, kind="assault", forced=forced, attacker=a.name, defender=d.name,
            site=s.name, attacker_wins=attacker_wins, ratio=ratio,
            losses={lose.name: kl, win.name: kw}, manpower_before=mp_before, shock_inc=sh,
            supply_moved=moved_supply))
