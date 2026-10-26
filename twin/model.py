"""Двойник v0: состояние, фазы тика, штурм.

Без случайности. Без людей поштучно: только счётчики вёдер (03).
Каждое изменение пишется в журнал (11 S2d): tick, phase, module, target, old, new, reason_code.
"""
from dataclasses import dataclass, field
from math import ceil, floor

from .params import Params

BUCKETS_ALIVE = ("steady", "ordinary", "skittish")
BUCKETS_OUT = ("dead", "deserted", "expelled", "detained", "sold", "captured")  # куда уходят люди; сумма с живыми = старт (§1)
TIERS = ("rank", "vet", "off")  # ярусы 04: рядовые, ветераны, офицеры; порядок везде один
CACHE = "cache"  # тайник: ничейное место, куда уходит склад фракции без объектов (spec 03b)


@dataclass
class Site:
    name: str
    base_cost: float
    yield_: float
    min_crew: int
    owner: str | None = None
    income_disabled: bool = False  # сценарий «потеря узла»
    region: str = "common"         # регион, где стоит объект (spec 03b)


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
    workers: dict = field(default_factory=dict)  # объект -> работников сверх MinCrew (spec 03a)
    home: str = "common"            # родной регион: налёты бьют по нему (spec 03b)
    depot: str | None = None        # адрес пула: имя объекта или CACHE (spec 03b)
    expelled: int = 0               # ведро «изгнаны» (spec 05); никто их не принимает
    forced_mode: bool = False       # режим принудительного самообеспечения (spec 05)
    detained: int = 0               # ведро «задержаны» — срывы контрабанды (spec 06)
    sold: int = 0                   # ведро «проданы» — торговля пленными, вне мира (spec 06)
    heat: float = 0.0               # внимание властей к контрабанде (spec 06)
    bust_until: int = 0             # до какого тика канал стоит после срыва
    wounded: int = 0                # ведро «раненые» (spec 03c): едят, не воюют, не входят в Manpower
    wounded_queue: list = field(default_factory=list)   # [тик возврата, ведро, число]
    captured: int = 0               # брошенные раненые, попавшие в плен (выбыли из фракции)
    absorbed: int = 0               # принятые пленные других фракций (прибавка к старту для сохранения людей)
    rank: int = 0                   # ярусы (spec 04): рядовые, ветераны, офицеры; сумма = Manpower
    vet: int = 0
    off: int = 0
    paid: dict = field(default_factory=lambda: {"rank": 0.0, "vet": 0.0, "off": 0.0})       # накопленная выплата по ярусу, вне пула
    last_paid: dict = field(default_factory=lambda: {"rank": 0, "vet": 0, "off": 0})        # тик последней выплаты по ярусу
    underpaid: dict = field(default_factory=lambda: {"rank": False, "vet": False, "off": False})
    reorg_queue: list = field(default_factory=list)  # тики срабатывания отложенных реорганизаций

    @property
    def manpower(self) -> int:
        return self.steady + self.ordinary + self.skittish

    def steadfast(self, p: Params) -> float:
        if self.manpower == 0:
            return 0.0
        w = p.steadfast_weights
        return (w[0] * self.steady + w[1] * self.ordinary + w[2] * self.skittish) / self.manpower


LEVELS = ("Ally", "Neutral", "Neutral+tension", "Enemy", "Archnemesis")  # уровни 08 [док 08]


@dataclass
class Relation:
    """Обида пострадавшего к обидчику (spec 08a): запись пары (victim -> offender)."""
    base: float                                    # база на момент регистрации (для журнала)
    g_target: float = 0.0                          # цель затухающей части
    g: float = 0.0                                 # текущая затухающая часть
    b: float = 0.0                                 # «предательство», не затухает
    taken: list = field(default_factory=list)      # объекты, которые обидчик взял штурмом у пострадавшего
    h: float = 0.0                                 # последний записанный H
    level: str = ""                                # последний записанный уровень


@dataclass
class World:
    factions: dict
    sites: list
    p: Params
    tick: int = 0
    log: list = field(default_factory=list)
    events: list = field(default_factory=list)   # события для метрик (штурмы, дезертирство, сдача)
    forced_assaults: dict = field(default_factory=dict)  # tick -> [(attacker, site_name)]
    forced_raids: dict = field(default_factory=dict)     # tick -> [(attacker, site_name)] принудительные налёты на объект (spec 03c)
    scheduled: dict = field(default_factory=dict)        # tick -> [callable(world)]
    regions: dict = field(default_factory=dict)          # имя региона -> Достаток (06); "common" — один регион на всех
    rel: dict = field(default_factory=dict)              # (пострадавший, обидчик) -> Relation (spec 08a)
    rel_cursor: int = 0                                  # сколько событий из events уже учтено фазой 8
    known_at_start: dict = field(default_factory=dict)   # фракция -> (объекты, чьего владельца она знает со старта) (spec 08c)
    know: dict = field(default_factory=dict)             # (фракция, объект) -> владелец по её сведениям (spec 08c)
    rumors: list = field(default_factory=list)           # слухи в пути: dict(site, owner, born, due, key) (spec 08c)
    motive: set = field(default_factory=set)             # пары (фракция, объект) с мотивом (spec 08c)
    know_cursor: int = 0
    know_started: bool = False
    rumor_seq: dict = field(default_factory=dict)
    wars: dict = field(default_factory=dict)             # (зачинщик, цель) -> запись войны (spec 08b)
    war_acc: dict = field(default_factory=dict)          # (зачинщик, цель) -> счётчик решимости
    truce: dict = field(default_factory=dict)            # (A, B) по алфавиту -> тик конца перемирия
    last_war_tick: int = -10**9

    @property
    def prosperity(self) -> float:
        return self.regions["common"]

    def __post_init__(self):
        if not self.regions:
            self.regions = {"common": self.p.region_start}
        for name in [f.home for f in self.factions.values()] + [s.region for s in self.sites]:
            self.regions.setdefault(name, self.p.region_start)
        for f in self.factions.values():
            if f.depot is None:
                f.depot = self.best_depot(f)
            if self.p.tiers_enabled:
                self.init_tiers(f)

    def set_region(self, name, value, phase, reason):
        old = self.regions[name]
        self.regions[name] = max(0.0, min(self.p.region_max, value))
        target = "region.prosperity" if name == "common" else f"region.{name}.prosperity"
        self.rec(phase, "06", target, old, self.regions[name], reason)

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

    # ---------- 04: ярусы (spec 04) ----------
    def init_tiers(self, f: Faction):
        sh = self.p.tier_start_share
        m = f.manpower
        f.off = floor(sh[2] * m + 1e-9)
        f.vet = floor(sh[1] * m + 1e-9)
        f.rank = m - f.off - f.vet

    @staticmethod
    def take_tiers(comp, n, prefer=()):
        """Кого забирает выбытие n человек из состава comp = [рядовые, ветераны, офицеры].
        Сначала ярусы из prefer (недоплаченные), остаток пропорционально: офицеры floor(n × off / всего),
        ветераны floor(n × vet / всего), остаток — рядовые, не хватает — ветераны, затем офицеры. Без случайности."""
        n = min(n, sum(comp))
        rem = [0, 0, 0]
        left = n
        for i in prefer:
            x = min(comp[i] - rem[i], left)
            rem[i] += x
            left -= x
        if left > 0:
            avail = [comp[i] - rem[i] for i in range(3)]
            tot = sum(avail)
            o = min(floor(left * avail[2] / tot), avail[2])
            v = min(floor(left * avail[1] / tot), avail[1])
            rem[2] += o
            rem[1] += v
            left -= o + v
            for i, cap in ((0, avail[0]), (1, avail[1] - v), (2, avail[2] - o)):
                x = min(left, cap)
                rem[i] += x
                left -= x
        return tuple(rem)

    def tier_remove(self, f: Faction, n: int, phase, prefer=(), forced=None):
        """Живые выбыли (бакеты уже изменены): убрать n человек из ярусов; офицеры или ветераны убыли — отложенная реорганизация."""
        if not self.p.tiers_enabled or n <= 0:
            return (0, 0, 0)
        comp = [f.rank, f.vet, f.off]
        rem = tuple(forced) if forced is not None else self.take_tiers(comp, n, prefer)
        for t, r in zip(TIERS, rem):
            if r:
                self.setf(f, t, getattr(f, t) - r, phase, "03", "TIER")
        if rem[1] or rem[2]:
            self.schedule_reorg(f, phase)
        return rem

    def tier_add(self, f: Faction, tt, phase):
        if not self.p.tiers_enabled:
            return
        for t, x in zip(TIERS, tt):
            if x:
                self.setf(f, t, getattr(f, t) + x, phase, "03", "TIER")

    def schedule_reorg(self, f: Faction, phase):
        p = self.p
        target_off = floor(p.tier_start_share[2] * f.manpower + 1e-9)
        urgent = target_off > 0 and f.off < p.reorg_urgent_fill * target_off
        old = len(f.reorg_queue)
        f.reorg_queue.append(self.tick + (p.reorg_ticks_urgent if urgent else p.reorg_ticks))
        self.rec(phase, "03", f"{f.name}.reorg_pending", old, len(f.reorg_queue), "REORG")

    def reorganize(self, f: Faction):
        """Фаза 1: сработавшие события реорганизации заполняют вакансии каскадом; понижений нет."""
        if not self.p.tiers_enabled:
            return
        due = [d for d in f.reorg_queue if d <= self.tick]
        if not due:
            return
        old = len(f.reorg_queue)
        f.reorg_queue = [d for d in f.reorg_queue if d > self.tick]
        self.rec(1, "03", f"{f.name}.reorg_pending", old, len(f.reorg_queue), "REORG")
        sh = self.p.tier_start_share
        t_off = floor(sh[2] * f.manpower + 1e-9)
        t_vet = floor(sh[1] * f.manpower + 1e-9)
        mv = min(max(0, t_off - f.off), f.vet)
        if mv:
            self.setf(f, "vet", f.vet - mv, 1, "03", "REORG")
            self.setf(f, "off", f.off + mv, 1, "03", "REORG")
        mv = min(max(0, t_vet - f.vet), f.rank)
        if mv:
            self.setf(f, "rank", f.rank - mv, 1, "03", "REORG")
            self.setf(f, "vet", f.vet + mv, 1, "03", "REORG")

    def kill_tier(self, f: Faction, k: int, tier: str = "off", phase=7, reason="KILL_TIER"):
        """Сценарный вызов: убить k человек заданного яруса (удар по руководству; модуль 05 его позже вызовет)."""
        n = min(k, getattr(f, tier)) if self.p.tiers_enabled else min(k, f.manpower)
        forced = tuple(n if t == tier else 0 for t in TIERS) if self.p.tiers_enabled else None
        return self._move(f, n, self.p.drain_order, "dead", phase, reason, tiers=forced)

    def tier_fighters(self, f: Faction):
        """Бойцы по ярусам: принуждённые (05) берутся из рядовых, затем ветеранов, затем офицеров."""
        comp = [f.rank, f.vet, f.off]
        k = self.forced_count(f) if f.forced_mode else 0
        for i in range(3):
            x = min(k, comp[i])
            comp[i] -= x
            k -= x
        return comp

    def pay_tiers(self, f: Faction, amount: float, phase):
        """Выплата доли добычи по ярусам с весом на человека; из пула она уже ушла (ShareRate, 06)."""
        p = self.p
        if not p.tiers_enabled or amount <= 0 or f.manpower == 0:
            return
        comp = [f.rank, f.vet, f.off]
        w = [p.tier_pay_weight[i] * comp[i] for i in range(3)]
        tot = sum(w)
        for i, t in enumerate(TIERS):
            if comp[i] > 0:
                old = f.paid[t]
                f.paid[t] = old + amount * w[i] / tot
                self.rec(phase, "06", f"{f.name}.paid.{t}", old, f.paid[t], "PAY")
            old = f.last_paid[t]
            f.last_paid[t] = self.tick
            self.rec(phase, "06", f"{f.name}.last_paid.{t}", old, self.tick, "PAY")

    def underpay(self, f: Faction):
        """Фаза 3: ярус недоплачен, если выплат не было дольше его терпения; мораль падает по доле недоплаченных."""
        p = self.p
        if not p.tiers_enabled or f.archetype not in p.raiding_archetypes or p.share_rate[f.archetype] <= 0:
            return
        comp = [f.rank, f.vet, f.off]
        under = 0
        for i, t in enumerate(TIERS):
            state = comp[i] > 0 and self.tick - f.last_paid[t] > p.underpay_ticks[i]
            if state != f.underpaid[t]:
                self.rec(3, "06", f"{f.name}.underpaid.{t}", int(f.underpaid[t]), int(state), "UNDERPAY")
                f.underpaid[t] = state
            if state:
                under += comp[i]
        if under and f.manpower:
            self.setf(f, "morale", max(0.0, f.morale - p.underpay_morale * under / f.manpower), 3, "06", "UNDERPAY")

    def gear_step(self, f: Faction, tier: str) -> str:
        """Ступень снаряжения яруса по TF_Armory (расчётный вывод, в игру не подключается)."""
        i = TIERS.index(tier)
        if f.armory >= self.p.gear_good[i]:
            return "Good"
        return "Worn" if f.armory >= self.p.gear_worn[i] else "Rags"

    # ---------- 03: вёдра ----------
    def _move(self, f: Faction, n: int, order: str, dest: str, phase, reason, prefer_underpaid=False, tiers=None) -> int:
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
        if moved:
            prefer = [i for i, t in enumerate(TIERS) if f.underpaid[t]] if prefer_underpaid else ()
            self.tier_remove(f, moved, phase, prefer=prefer, forced=tiers)
        return moved

    def kill_many(self, f, n, phase, reason):
        return self._move(f, n, self.p.drain_order, "dead", phase, reason)

    def wound_many(self, f: Faction, n: int, phase, reason) -> int:
        """Выбывшие в раненые: порядок как у слива вёдер; запись в очередь выздоровления (spec 03c)."""
        seq = ("skittish", "ordinary", "steady") if self.p.drain_order == "skittish_first" else ("steady", "ordinary", "skittish")
        moved = 0
        new = []
        for b in seq:
            if moved >= n:
                break
            take = min(getattr(f, b), n - moved)
            if take:
                self.setf(f, b, getattr(f, b) - take, phase, "03", reason)
                e = [self.tick + self.p.recovery_ticks, b, take, None]   # 4-й элемент: ярусы раненых (spec 04)
                f.wounded_queue.append(e)
                new.append(e)
                self.setf(f, "wounded", f.wounded + take, phase, "03", reason)
                moved += take
        if moved and self.p.tiers_enabled:
            left = list(self.tier_remove(f, moved, phase))
            for e in new:
                need, tt = e[2], [0, 0, 0]
                for i in range(3):
                    x = min(need, left[i])
                    tt[i], left[i], need = x, left[i] - x, need - x
                e[3] = tuple(tt)
        return moved

    def recover(self, f: Faction):
        for e in [e for e in f.wounded_queue if e[0] <= self.tick]:
            f.wounded_queue.remove(e)
            self.setf(f, e[1], getattr(f, e[1]) + e[2], 1, "03", "RECOVERY")
            self.setf(f, "wounded", f.wounded - e[2], 1, "03", "RECOVERY")
            if e[3] is not None:
                self.tier_add(f, e[3], 1)

    def drop_wounded(self, f: Faction, n: int, newest: bool, dest: str | None, phase, reason) -> int:
        """Вывести n раненых из очереди (новейших — брошенные, старейших — изгнанные) в ведро dest."""
        left = n
        while left > 0 and f.wounded_queue:
            e = f.wounded_queue[-1] if newest else f.wounded_queue[0]
            take = min(left, e[2])
            if e[3] is not None:
                gone = self.take_tiers(list(e[3]), take)
                e[3] = tuple(a - b for a, b in zip(e[3], gone))
            e[2] -= take
            left -= take
            if e[2] == 0:
                f.wounded_queue.remove(e)
            self.setf(f, "wounded", f.wounded - take, phase, "03", reason)
            if dest:
                self.setf(f, dest, getattr(f, dest) + take, phase, "03", reason)
        return n - left

    def remove_many(self, f, n, phase, reason):
        return self._move(f, n, self.p.desertion_order, "deserted", phase, reason, prefer_underpaid=True)

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

    def staffed(self, f: Faction, exclude: str | None = None):
        """Какие площадки укомплектованы. Трактовка v0: люди распределяются
        по площадкам в порядке убывания дохода, каждой нужно MinCrew.
        exclude — объект, которого уже нет у фракции (расчёт переезда склада)."""
        left = f.manpower
        out = []
        for s in sorted([s for s in self.owned(f) if s.name != exclude], key=lambda s: -s.yield_):
            if left >= s.min_crew:
                out.append(s)
                left -= s.min_crew
        return out

    # ---------- 06: склад (spec 03b) ----------
    def best_depot(self, f: Faction, exclude: str | None = None) -> str:
        """Склад — на укомплектованном объекте с наибольшим доходом, при равенстве по имени;
        нет такого — в тайник (трактовка 06 «ближайшая укомплектованная»: расстояний в двойнике нет)."""
        st = sorted(self.staffed(f, exclude), key=lambda s: (-s.yield_, s.name))
        return st[0].name if st else CACHE

    def move_depot(self, f: Faction, reason: str, exclude: str | None = None):
        new = self.best_depot(f, exclude)
        old = f.depot
        if new != old:
            f.depot = new
            self.rec(7, "06", f"{f.name}.depot", old, new, "DEPOT_MOVE")
            self.events.append(dict(tick=self.tick, kind="depot_move", faction=f.name, frm=old, to=new, why=reason))

    def depot_strike(self, f: Faction, site: Site):
        p = self.p
        before = (f.supply, f.armory)
        self.setf(f, "supply", f.supply * (1 - p.depot_loss_rate), 7, "06", "DEPOT_STRIKE")
        self.setf(f, "armory", f.armory * (1 - p.depot_armory_rate), 7, "06", "DEPOT_STRIKE")
        self.events.append(dict(tick=self.tick, kind="depot_strike", faction=f.name, site=site.name,
                                supply_before=before[0], armory_before=before[1]))
        self.move_depot(f, "DEPOT_STRIKE", exclude=site.name)

    def work_plan(self, f: Faction):
        """Spec 03a: сначала каждому укомплектованному объекту MinCrew, остаток —
        по объектам в порядке убывания базового дохода до потолка p.crew_cap.
        Возвращает (объект, работников сверх MinCrew, доход объекта)."""
        st = self.staffed(f)
        left = f.manpower - sum(s.min_crew for s in st)
        out = []
        for s in st:
            cap = self.p.crew_cap.get(s.name, s.min_crew)
            extra = max(0, min(left, cap - s.min_crew))
            left -= extra
            out.append((s, extra, s.yield_ + self.p.worker_yield * extra))
        return out

    def forced_count(self, f: Faction) -> int:
        """Принуждённые (spec 05): люди сверх суммарного потолка экипажа укомплектованных объектов."""
        cap = sum(self.p.crew_cap.get(s.name, s.min_crew) for s in self.staffed(f))
        return max(0, f.manpower - cap)

    def fighters(self, f: Faction) -> int:
        return f.manpower - (self.forced_count(f) if f.forced_mode else 0)

    def crew(self, f: Faction, site: Site) -> int:
        return min(f.manpower, site.min_crew + 2)

    def expense(self, f: Faction) -> float:
        base = sum(s.base_cost for s in self.owned(f))
        return (base + (f.manpower + f.wounded) * self.p.per_head_cost) * self.p.archetype_cost_mult[f.archetype]

    def publish_dos(self, f: Faction, phase=4):
        e = self.expense(f)
        dos = f.supply / e if e > 0 else 999.0
        self.setf(f, "days_supply", dos, phase, "00", "PUBLISH")

    # ---------- тик ----------
    def step(self):
        self.tick += 1
        if self.p.war_steers_attacks and not self.p.wars_enabled:
            raise ValueError("war_steers_attacks требует wars_enabled (нужна цель войны из 08b)")
        for fn in self.scheduled.get(self.tick, []):
            fn(self)
        fs = list(self.factions.values())
        # фаза 1 — затухание шока, восстановление региона
        for f in fs:
            self.setf(f, "shock", max(0.0, f.shock - self.p.shock_decay_per_tick), 1, "04", "DECAY")
        for f in fs:
            self.recover(f)
        for f in fs:
            self.reorganize(f)
        for name in list(self.regions):
            self.set_region(name, self.regions[name] + self.p.region_recovery, 1, "REGION_RECOVERY")
        # фаза 2 — приход и расход; пошлина беднит регион (TollDrag, 06)
        for f in fs:
            plan = self.work_plan(f)
            for s, extra, _ in plan:
                old = f.workers.get(s.name, 0)
                f.workers[s.name] = extra
                self.rec(2, "06", f"{f.name}.workers.{s.name}", old, extra, "WORKERS")
            for name in [n for n in f.workers if n not in {s.name for s, _, _ in plan}]:
                self.rec(2, "06", f"{f.name}.workers.{name}", f.workers.pop(name), 0, "WORKERS")
            paying = [(s, inc) for s, _, inc in plan if not s.income_disabled]
            income = sum(inc for _, inc in paying)
            for s, inc in paying:
                self.set_region(s.region, self.regions[s.region] - inc * self.p.toll_drag, 2, "TOLL_DRAG")
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
        for atk_name, site_name in self.forced_raids.get(self.tick, []):
            self.raid_object(self.factions[atk_name], self.site(site_name), forced=True)
        for f in fs:
            self.decide_assault(f)
        for f in fs:
            self.raid(f)
        # фаза 8 — отношения и обида (spec 08a): только читает события тика, ничего не меняет в других модулях
        if self.p.relations_enabled:
            self.relations_step()
        # фаза 8 — знание и мотив (spec 08c): только читает, в состояние других модулей не пишет
        if self.p.knowledge_enabled:
            self.knowledge_step()
        # фаза 8 — война как состояние пары (spec 08b): читает 08a и 08c, пишет в чужие модули только цену (06)
        if self.p.wars_enabled:
            self.war_step()

    # ---------- 06 S3: налёт на регион ----------
    def raid(self, f: Faction):
        p = self.p
        if not p.raids_enabled or f.archetype not in p.raiding_archetypes or f.manpower == 0:
            return
        if self.tick - f.last_raid < p.raid_cooldown:
            return
        if p.object_raids_enabled and f.last_assault != self.tick:
            goal = self._steer_goal(f)   # spec 08d: сначала цель войны
            if goal is not None and self.visible_power(f) / max(1e-9, self.visible_power(self.factions[goal.owner]) * p.defense_factor) > p.raid_object_threshold:
                self._war_attack(f, goal, "raid")
                self.raid_object(f, goal, forced=False)
                return
            targets = [s for s in self.sites if s.owner not in (None, f.name) and self.factions[s.owner].manpower > 0]
            for s in sorted(targets, key=lambda s: (-s.yield_, s.name)):
                d = self.factions[s.owner]
                if self.visible_power(f) / max(1e-9, self.visible_power(d) * p.defense_factor) > p.raid_object_threshold:
                    self.raid_object(f, s, forced=False)
                    return
        f.last_raid = self.tick
        loot = self.regions[f.home] * p.raid_yield
        to_pool = loot * (1 - p.share_rate[f.archetype])
        self.setf(f, "supply", f.supply + to_pool, 7, "06", "RAID")
        self.pay_tiers(f, loot * p.share_rate[f.archetype], 7)
        self.set_region(f.home, self.regions[f.home] - p.raid_cost, 7, "RAID")
        # spec 07: группа налёта на регион — витрина; на добычу не влияет
        self.events.append(dict(tick=self.tick, kind="raid", faction=f.name, loot=loot,
                                to_pool=to_pool, manpower=f.manpower, party=min(f.manpower, p.strike_group_max)))

    def raid_object(self, a: Faction, s: Site, forced: bool):
        """Spec 03c: налёт на объект. Бой как в штурме, но объект не захватывается; выбывшие частью ранены;
        ёмкость и мораль группы решают, что несут; брошенные раненые попадают в плен по укладу обороны."""
        p = self.p
        d = self.factions[s.owner]
        if a.manpower == 0 or d is a:
            return
        a.last_raid = self.tick
        atk, dfn = self.power(a), self.power(d) * p.defense_factor
        attacker_wins = atk > dfn
        win, lose = (a, d) if attacker_wins else (d, a)
        ratio = max(atk, dfn) / max(1e-9, min(atk, dfn))
        raiders = min(a.manpower, p.strike_group_max)
        part = {a.name: raiders, d.name: self.crew(d, s) + p.defense_reinforcement}
        mp_before = {a.name: a.manpower, d.name: d.manpower}
        if p.old_loss_formula:
            loser_loss = floor(0.5 * lose.manpower)
            winner_loss = floor(0.5 * lose.manpower / ratio)
        else:
            loser_loss = floor(min(0.5 * part[lose.name], p.assault_loss_cap * lose.manpower))
            winner_loss = min(floor(loser_loss / ratio), part[win.name])
        cas = {lose.name: loser_loss, win.name: winner_loss}
        wnd = {}
        for f in (lose, win):
            w = floor(cas[f.name] * p.wounded_share)
            self.kill_many(f, cas[f.name] - w, 7, "RAID_OBJECT")
            wnd[f.name] = self.wound_many(f, w, 7, "RAID_OBJECT")
            self.add_personnel_shock(f, cas[f.name], mp_before[f.name], 1.0, 7, "RAID_OBJECT")
        healthy = max(0, raiders - cas[a.name])
        w_a = wnd[a.name]
        capacity = healthy * p.carry_unit
        w_cost = p.wounded_load * p.carry_unit
        morale_high = a.morale >= p.carry_morale_threshold
        weight = sum(x.yield_ for x in self.owned(d))
        stock = d.supply * (s.yield_ / weight) if weight > 0 else 0.0
        loot, carried = 0.0, 0
        if attacker_wins:
            if morale_high:
                carried = min(w_a, int(capacity // w_cost))
                loot = min(stock, capacity - carried * w_cost)
            else:
                loot = min(stock, capacity)
                carried = min(w_a, int((capacity - loot) // w_cost))
        abandoned = w_a - carried
        if loot > 0:
            self.setf(d, "supply", d.supply - loot, 7, "06", "RAID_OBJECT")
            self.setf(a, "supply", a.supply + loot * (1 - p.share_rate[a.archetype]), 7, "06", "RAID_OBJECT")
            self.pay_tiers(a, loot * p.share_rate[a.archetype], 7)
        fate = None
        if abandoned:
            self.drop_wounded(a, abandoned, True, None, 7, "ABANDON")
            defenders_left = part[d.name] - cas[d.name]
            if defenders_left > 0 and d.manpower > 0 and d.archetype in ("Хранители", "Контролёры"):
                fate = "absorbed"
                self.setf(a, "captured", a.captured + abandoned, 7, "03", "CAPTURE")
                self.setf(d, "skittish", d.skittish + abandoned, 7, "03", "CAPTURE")
                self.tier_add(d, (abandoned, 0, 0), 7)   # принятые пленные приходят рядовыми (spec 04)
                self.setf(d, "absorbed", d.absorbed + abandoned, 7, "03", "CAPTURE")
            elif defenders_left > 0 and d.manpower > 0 and d.archetype == "Хищники":
                fate = "sold"
                self.setf(a, "sold", a.sold + abandoned, 7, "03", "PRISONER_SALE")
                self.setf(d, "supply", d.supply + p.prisoner_price * abandoned, 7, "06", "PRISONER_SALE")
            else:
                fate = "dead"
                self.setf(a, "dead", a.dead + abandoned, 7, "03", "ABANDON")
            self.setf(a, "morale", max(0.0, a.morale - p.abandon_morale_cost * abandoned), 7, "06", "ABANDON")
        self.events.append(dict(
            tick=self.tick, kind="raid_object", forced=forced, attacker=a.name, defender=d.name, site=s.name,
            attacker_wins=attacker_wins, raiders=raiders, healthy=healthy, wounded=w_a, carried=carried,
            abandoned=abandoned, fate=fate, loot=loot, stock=stock, capacity=capacity, morale_high=morale_high,
            casualties=dict(cas), wounded_by=dict(wnd)))

    def site(self, name):
        return next(s for s in self.sites if s.name == name)

    # ---------- 06: голод ----------
    def free_people(self, f: Faction) -> int:
        """Люди не на объектах: могут работать в каналах (spec 06)."""
        caps = sum(self.p.crew_cap.get(s.name, s.min_crew) for s in self.staffed(f))
        return f.manpower - min(f.manpower, caps)

    def channels(self, f: Faction):
        """Spec 06: контрабанда (внешний рынок, Heat), поборы с родного региона."""
        p = self.p
        fr = self.free_people(f)
        if p.smuggling_enabled:
            if f.archetype in p.smuggling_archetypes and not self.staffed(f) \
                    and self.tick >= f.bust_until and fr >= 3:
                n = min(fr, p.smuggling_cap_people)
                inc = min(p.smuggling_yield * n, p.market_cap)
                self.setf(f, "supply", f.supply + inc, 3, "06", "SMUGGLING")
                self.setf(f, "heat", round(f.heat + p.heat_per_income * inc, 6), 3, "06", "SMUGGLING")   # округление: порог и журнал видят одно число
            self.setf(f, "heat", round(max(0.0, f.heat - p.heat_decay), 6), 3, "06", "HEAT_DECAY")
            if f.heat >= p.heat_threshold:
                n = min(fr, p.smuggling_cap_people)
                d = ceil(n * p.bust_detain_share)
                moved = self._move(f, d, p.desertion_order, "detained", 3, "BUST")
                self.setf(f, "heat", p.heat_after_bust, 3, "06", "BUST")
                self.setf(f, "bust_until", self.tick + p.bust_pause, 3, "06", "BUST")
                self.events.append(dict(tick=self.tick, kind="bust", faction=f.name, n=moved))
        if p.fees_enabled and f.archetype in p.fee_archetypes and fr >= 3:
            inc = min(p.fee_rate * fr, self.regions[f.home] * p.fee_region_share)
            self.setf(f, "supply", f.supply + inc, 3, "06", "PROTECTION_FEE")
            self.set_region(f.home, self.regions[f.home] - inc * p.fee_drag, 3, "FEE_DRAG")

    def expected_income(self, f: Faction) -> float:
        """Ожидаемый приход в сутки: доход объектов с экипажем (03a) + налёт в среднем за кулдаун (06 S3)."""
        p = self.p
        inc = sum(i for s, _, i in self.work_plan(f) if not s.income_disabled)
        if p.raids_enabled and f.archetype in p.raiding_archetypes:
            inc += self.regions[f.home] * p.raid_yield * (1 - p.share_rate[f.archetype]) / p.raid_cooldown
        return inc

    def decide(self, f: Faction):
        """Spec 05: решение при голоде. Условие: запас ниже порога и мораль ниже порога решения."""
        p = self.p
        if not p.decisions_enabled or f.manpower == 0:
            return
        if f.forced_mode and f.days_supply >= p.hunger_threshold:
            self.setf(f, "forced_mode", False, 3, "05", "FORCED_LABOR")
        if f.archetype not in p.peaceful_decide:
            return
        if not (f.days_supply < p.hunger_threshold and f.morale < p.decision_morale_threshold):
            return
        if f.archetype == "Контролёры":
            if not f.forced_mode:
                self.setf(f, "forced_mode", True, 3, "05", "FORCED_LABOR")
            return
        # Хищники и прочие «изгоняющие» (R6): изгонять, пока расход не впишется в ожидаемый приход
        before, n = f.manpower + f.wounded, 0
        while n < p.expel_cap_per_tick and (f.manpower > 0 or f.wounded > 0) and self.expense(f) > self.expected_income(f):
            if f.wounded > 0:   # раненые изгоняются первыми (spec 05, 03c)
                n += self.drop_wounded(f, 1, False, "expelled", 3, "EXPEL")
            else:
                n += self._move(f, 1, p.desertion_order, "expelled", 3, "EXPEL", prefer_underpaid=True)
        if n:
            self.add_personnel_shock(f, n, before, p.expel_shock_weight, 3, "EXPEL")
            self.events.append(dict(tick=self.tick, kind="expel", faction=f.name, n=n))

    def hunger(self, f: Faction):
        p = self.p
        if f.manpower == 0:
            return
        self.underpay(f)
        self.channels(f)
        self.decide(f)
        if f.forced_mode:
            k = self.forced_count(f)
            if k:
                self.setf(f, "supply", f.supply + p.forced_yield * k, 3, "05", "FORCED_LABOR")
                self.setf(f, "morale", max(0.0, f.morale - p.forced_morale_cost * k), 3, "05", "FORCED_LABOR")
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
        if f.depot == dear.name:
            self.move_depot(f, "SURRENDER")
        self.rec(7, "06", f"site.{dear.name}.owner", f.name, None, "SURRENDER")
        self.rec(7, "06", f"site.{cheap.name}.owner", None, f.name, "SURRENDER")
        self.events.append(dict(tick=self.tick, kind="surrender", faction=f.name,
                                frm=dear.name, to=cheap.name, manpower=f.manpower))

    # ---------- 13: решение о штурме ----------
    def visible_power(self, f: Faction) -> float:
        # атакующий не видит стойкость противника (13)
        return self.fighters(f) * (0.5 + f.armory / 100)

    def power(self, f: Faction) -> float:
        # spec 04: бойцы взвешены по ярусам (среднее по 70/20/10 равно 1.0); без ярусов — прежнее число бойцов
        if self.p.tiers_enabled:
            n = sum(wt * c for wt, c in zip(self.p.tier_power_weight, self.tier_fighters(f)))
        else:
            n = self.fighters(f)
        return n * (0.5 + f.armory / 100) * (0.6 + 0.8 * f.steadfast(self.p) / 100)

    def decide_assault(self, f: Faction):
        p = self.p
        thr = p.archetype_assault_threshold.get(f.archetype)
        if thr is None or f.manpower == 0:
            return
        if f.days_supply >= p.assault_dos or f.armory < p.assault_armory_min:
            return
        if self.tick - f.last_assault < p.assault_cooldown:
            return
        goal = self._steer_goal(f)   # spec 08d: сначала цель войны
        if goal is not None:
            d = self.factions[goal.owner]
            if self.visible_power(f) / max(1e-9, self.visible_power(d) * p.defense_factor) > thr:
                self._war_attack(f, goal, "assault")
                self.assault(f, goal, forced=False)
                return
        targets = [s for s in self.sites if s.owner not in (None, f.name)]
        for s in sorted(targets, key=lambda s: (-s.yield_, s.name)):
            d = self.factions[s.owner]
            ratio = self.visible_power(f) / max(1e-9, self.visible_power(d) * p.defense_factor)
            if ratio > thr:
                self.assault(f, s, forced=False)
                return

    def _steer_goal(self, f: Faction):
        """Spec 08d: цель действующей войны, где f — зачинщик, если объект ещё у защитника; иначе None."""
        if not (self.p.wars_enabled and self.p.war_steers_attacks):
            return None
        for (a, b), w in sorted(self.wars.items()):
            if a == f.name:
                s = self.site(w["goal"])
                if s.owner == b and self.factions[b].manpower > 0:
                    return s
        return None

    def _war_attack(self, f: Faction, s: Site, kind: str):
        self.events.append(dict(kind="war_attack", tick=self.tick, initiator=f.name, victim=s.owner, site=s.name, attack=kind))

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
        ns = floor(loser_loss * p.sale_share) if (p.prisoner_sale_enabled and win.archetype in p.sale_archetypes) else 0
        kl = self.kill_many(lose, loser_loss - ns, 7, "ASSAULT")
        ks = self._move(lose, ns, p.drain_order, "sold", 7, "PRISONER_SALE") if ns else 0
        if ks:
            self.setf(win, "supply", win.supply + p.prisoner_price * ks, 7, "06", "PRISONER_SALE")
        kl += ks   # потери проигравшего для шока и метрик — все выбывшие в бою
        kw = self.kill_many(win, winner_loss, 7, "ASSAULT")
        sh = {}
        for f, k in ((lose, kl), (win, kw)):
            sh[f.name] = self.add_personnel_shock(f, k, mp_before[f.name], 1.0, 7, "ASSAULT")
        # удар по складу (06): только при победе атакующего и только если на объекте стоял склад; до трофея
        if attacker_wins and d.depot == s.name:
            self.depot_strike(d, s)
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

    # ---------- 08a: отношения и обида ----------
    def base_h(self, a: str, b: str) -> float:
        """База H(A→B): слой 1 из 08 по осям архетипов. Слой 2 («конкуренция») в двойнике не реализован (spec 08a §6)."""
        p = self.p
        ea, ia, la = p.rel_axes[self.factions[a].archetype]
        lb = p.rel_axes[self.factions[b].archetype][2]
        w_exp, w_ins, w_leg, w_ill = p.rel_weights
        h = w_exp * ea + w_ins * ia
        if lb > 0:
            h += w_leg * la
        elif la >= 1:
            h += w_ill
        return h

    def level_of(self, h: float) -> str:
        """Уровень по H: границы полуинтервалами [док 08]."""
        c1, c2, c3, c4 = self.p.rel_level_cuts
        if h < c1:
            return LEVELS[0]
        if h < c2:
            return LEVELS[1]
        if h < c3:
            return LEVELS[2]
        if h < c4:
            return LEVELS[3]
        return LEVELS[4]

    def rel_h(self, a: str, b: str) -> float:
        """H(A→B) = база + g + b; для пары без записи обиды нет."""
        r = self.rel.get((a, b))
        return self.base_h(a, b) + (r.g + r.b if r else 0.0)

    def _register(self, victim: str, offender: str) -> Relation:
        """Пара регистрируется при первом событии между фракциями [док 08]."""
        r = self.rel.get((victim, offender))
        if r is None:
            base = self.base_h(victim, offender)
            r = self.rel[(victim, offender)] = Relation(base=base, h=base, level=self.level_of(base))
            self.rec(8, "08", f"rel.{victim}>{offender}.registered", 0, 1, "REL")
        return r

    def betray(self, betrayer: str, victim: str):
        """Сценарный вход: A нарушила труа с B. b(B→A) += betrayal сразу, мимо потолка и лимита толчка, не затухает.
        Труа в двойнике нет, вызов только из сценариев."""
        if not self.p.relations_enabled:
            return
        r = self._register(victim, betrayer)
        old = r.b
        r.b += self.p.betrayal
        self.rec(8, "08", f"rel.{victim}>{betrayer}.b", old, r.b, "GRUDGE")

    def relations_step(self):
        """Фаза 8. Порядок: события тика → потолок → захват → лимит толчка → затухание → пересчёт H и уровней."""
        p = self.p
        new_events = self.events[self.rel_cursor:]
        self.rel_cursor = len(self.events)
        for e in new_events:
            if e.get("kind") not in ("raid_object", "assault"):
                continue
            victim, offender = e["defender"], e["attacker"]
            if victim == offender or victim not in self.factions or offender not in self.factions:
                continue
            r = self._register(victim, offender)
            old = r.g_target
            r.g_target = min(p.grudge_cap, r.g_target + p.grudge_event)
            self.rec(8, "08", f"rel.{victim}>{offender}.g_target", old, r.g_target, "GRUDGE")
            if e["kind"] == "assault" and e["attacker_wins"] and e["site"] not in r.taken:
                r.taken.append(e["site"])
        for (victim, offender), r in self.rel.items():
            old = r.g
            if r.g < r.g_target:
                r.g = min(r.g_target, r.g + p.grudge_push)
            elif r.g > r.g_target:
                r.g = max(r.g_target, r.g - p.grudge_push)
            self.rec(8, "08", f"rel.{victim}>{offender}.g", old, r.g, "GRUDGE")
        if self.tick % p.grudge_decay_every == 0:
            for (victim, offender), r in self.rel.items():
                if r.g_target <= 0:
                    continue
                r.taken = [s for s in r.taken if self.site(s).owner == offender]
                alive = p.grudge_pause and bool(r.taken)
                self.events.append(dict(kind="grudge_decay", tick=self.tick, victim=victim, offender=offender, applied=not alive))
                if not alive:
                    old = r.g_target
                    r.g_target = max(0.0, r.g_target - p.grudge_decay_step)
                    self.rec(8, "08", f"rel.{victim}>{offender}.g_target", old, r.g_target, "GRUDGE")
        self.rel_cursor = len(self.events)
        for (victim, offender), r in self.rel.items():
            h = self.base_h(victim, offender) + r.g + r.b
            lvl = self.level_of(h)
            self.rec(8, "08", f"rel.{victim}>{offender}.H", r.h, h, "REL")
            self.rec(8, "08", f"rel.{victim}>{offender}.level", r.level, lvl, "REL")
            r.h, r.level = h, lvl

    # ---------- 08c: знание и мотив ----------
    def _know_set(self, f: str, site: str, owner, reason: str):
        """Записная книжка фракции: владелец объекта по её сведениям; None — записи нет."""
        old = self.know.get((f, site))
        if old == owner:
            return
        if owner is None:
            del self.know[(f, site)]
        else:
            self.know[(f, site)] = owner
        self.rec(8, "08c", f"know.{f}>{site}", old, owner, reason)

    def knowledge_step(self):
        """Фаза 8, после relations_step. Порядок: события тика → слепое нападение → участники узнают → слух рождается →
        гаснут устаревшие записи → слухи, дошедшие до срока → пересчёт мотива (spec 08c §1)."""
        p = self.p
        if not self.know_started:
            self.know_started = True
            for f, names in self.known_at_start.items():
                for sname in names:
                    s = self.site(sname)
                    if s.owner not in (None, f):
                        self._know_set(f, sname, s.owner, "KNOW_START")
        new_events = self.events[self.know_cursor:]
        know0 = dict(self.know)   # состояние на начало обработки тика: по нему считается «слепое» нападение
        for e in new_events:
            if e.get("kind") not in ("raid_object", "assault"):
                continue
            a, d, sname = e["attacker"], e["defender"], e["site"]
            owner_after = a if (e["kind"] == "assault" and e["attacker_wins"]) else d
            if know0.get((a, sname)) != d:
                self.events.append(dict(kind="blind_attack", tick=self.tick, attacker=a, defender=d, site=sname, forced=e["forced"]))
            for f in (a, d):
                if f != owner_after:
                    self._know_set(f, sname, owner_after, "KNOW_DIRECT")
            born = self.tick
            n = self.rumor_seq.get((sname, born), 0)
            self.rumor_seq[(sname, born)] = n + 1
            key = f"rumor.{sname}.{born}" + (f".{n}" if n else "")
            self.rumors.append(dict(site=sname, owner=owner_after, born=born, due=born + p.rumor_delay, key=key))
            self.rec(8, "08c", key, 0, 1, "RUMOR_NEW")
        if p.knowledge_expires_on_owner_change:
            for (f, sname), val in sorted(self.know.items()):
                if self.site(sname).owner != val:
                    self._know_set(f, sname, None, "KNOW_LOST")
        due = [r for r in self.rumors if r["due"] <= self.tick]
        self.rumors = [r for r in self.rumors if r["due"] > self.tick]
        for r in due:
            cur = self.site(r["site"]).owner
            if p.rumor_drop_stale and cur != r["owner"]:
                self.rec(8, "08c", r["key"], 1, 0, "RUMOR_STALE")
                continue
            for f in self.factions:
                if f != cur and f != r["owner"]:
                    self._know_set(f, r["site"], r["owner"], "KNOW_RUMOR")
            self.rec(8, "08c", r["key"], 1, 0, "RUMOR_DELIVERED")
        now = set()
        for f, fac in self.factions.items():
            if fac.manpower == 0 or not fac.days_supply < p.hunger_threshold:
                continue
            for s in self.sites:
                if s.owner in (None, f) or self.factions[s.owner].manpower == 0 or s.yield_ <= 0:
                    continue
                if self.know.get((f, s.name)) == s.owner:
                    now.add((f, s.name))
        for f, sname in sorted(now - self.motive):
            self.rec(8, "08c", f"motive.{f}>{sname}", 0, 1, "MOTIVE")
        for f, sname in sorted(self.motive - now):
            self.rec(8, "08c", f"motive.{f}>{sname}", 1, 0, "MOTIVE")
        self.motive = now
        self.know_cursor = len(self.events)

    # ---------- 08b: война как состояние пары ----------
    def _war_count(self, name: str) -> int:
        return sum(1 for (a, b) in self.wars if name in (a, b))

    def _war_goal(self, a: str, b: str):
        """Цель войны: объект b с наибольшим доходом среди подходящих (мотив a при war_needs_motive), при равенстве по имени."""
        cand = [s for s in self.sites if s.owner == b and s.yield_ > 0
                and (not self.p.war_needs_motive or (a, s.name) in self.motive)]
        cand.sort(key=lambda s: (-s.yield_, s.name))
        return cand[0] if cand else None

    def _war_end(self, key, reason: str):
        a, b = key
        self.rec(8, "08b", f"war.{a}>{b}.state", 1, 0, reason)
        # spec 08e: проигравший по причине конца отдаёт победителю долю своего запаса; срок и «цель ушла» — без проигравшего
        loser = {"WAR_END_GOAL": b, "WAR_END_BROKEN": b, "WAR_END_EXHAUSTED": a}.get(reason)
        winner = (a if loser == b else b) if loser else None
        amount = 0.0
        if loser and self.p.war_reparation_share > 0:
            fl, fw = self.factions[loser], self.factions[winner]
            amount = self.p.war_reparation_share * fl.supply
            if amount > 0:
                self.setf(fl, "supply", fl.supply - amount, 8, "06", "REPARATIONS")
                self.setf(fw, "supply", fw.supply + amount, 8, "06", "REPARATIONS")
        self.events.append(dict(kind="war_end", tick=self.tick, initiator=a, victim=b, reason=reason, goal=self.wars[key]["goal"],
                                winner=winner, loser=loser, reparations=amount))
        del self.wars[key]
        pair = tuple(sorted(key))
        until = self.tick + self.p.war_truce
        self.truce[pair] = until
        self.rec(8, "08b", f"truce.{pair[0]}-{pair[1]}", 0, until, "TRUCE")

    def war_step(self):
        """Фаза 8, после knowledge_step. Порядок: перемирия → конец войн → цена → накопление и объявления (spec 08b §1)."""
        p = self.p
        if not self.p.relations_enabled:
            raise ValueError("wars_enabled требует relations_enabled (нужен H из 08a)")
        if p.war_needs_motive and not p.knowledge_enabled:
            raise ValueError("war_needs_motive требует knowledge_enabled (нужен мотив из 08c)")
        for pair, until in sorted(self.truce.items()):
            if until <= self.tick:
                self.rec(8, "08b", f"truce.{pair[0]}-{pair[1]}", until, 0, "TRUCE_END")
                del self.truce[pair]
        for key in sorted(self.wars):
            a, b = key
            w = self.wars[key]
            fa, fb = self.factions[a], self.factions[b]
            owner = self.site(w["goal"]).owner
            days = self.tick - w["start"]
            if owner == a:
                self._war_end(key, "WAR_END_GOAL")
            elif owner != b:
                self._war_end(key, "WAR_END_GOAL_LOST")
            elif days >= p.war_grace and fb.manpower <= p.war_broken_share * w["mp0"][b]:
                self._war_end(key, "WAR_END_BROKEN")
            elif days >= p.war_grace and fa.manpower <= p.war_exhausted_share * w["mp0"][a]:
                self._war_end(key, "WAR_END_EXHAUSTED")
            elif days >= p.war_max_days:
                self._war_end(key, "WAR_END_TIMEOUT")
        for key in sorted(self.wars):
            if self.wars[key]["start"] == self.tick:
                continue
            for name in key:
                f = self.factions[name]
                pay = min(p.war_cost * (self.expense(f) if p.war_cost_share_of_expense else 1.0), f.supply)
                if pay > 0:
                    self.setf(f, "supply", f.supply - pay, 8, "06", "WAR_COST")
        for a in sorted(self.factions):
            for b in sorted(self.factions):
                if a == b:
                    continue
                fa, fb = self.factions[a], self.factions[b]
                pair = tuple(sorted((a, b)))
                if fa.manpower == 0 or fb.manpower == 0 or fa.archetype not in p.archetype_assault_threshold:
                    continue
                if fa.armory < p.assault_armory_min or fa.days_supply < p.war_min_dos:
                    continue
                if (a, b) in self.wars or (b, a) in self.wars or pair in self.truce:
                    continue
                h = self.rel_h(a, b)
                if h < p.rel_level_cuts[2]:
                    continue
                goal = self._war_goal(a, b)
                if goal is None:
                    continue
                acc = self.war_acc.get((a, b), 0.0)
                if acc < 100.0:
                    add = min(p.war_chance_cap, p.war_chance_base + p.war_chance_slope * (h - p.rel_level_cuts[2]))
                    self.war_acc[(a, b)] = acc + add
                    self.rec(8, "08b", f"war.{a}>{b}.acc", acc, acc + add, "WAR_ACC")
                    acc += add
                if acc < 100.0:
                    continue
                if self.tick - self.last_war_tick < p.war_world_gap:
                    continue
                if self._war_count(a) >= p.war_max_per_faction or self._war_count(b) >= p.war_max_per_faction:
                    continue
                self.war_acc[(a, b)] = acc - 100.0
                self.rec(8, "08b", f"war.{a}>{b}.acc", acc, acc - 100.0, "WAR_ACC")
                self.wars[(a, b)] = dict(start=self.tick, goal=goal.name, mp0={a: fa.manpower, b: fb.manpower})
                self.last_war_tick = self.tick
                self.rec(8, "08b", f"war.{a}>{b}.goal", None, goal.name, "WAR_DECLARED")
                self.rec(8, "08b", f"war.{a}>{b}.state", 0, 1, "WAR_DECLARED")
                self.events.append(dict(kind="war_declared", tick=self.tick, initiator=a, victim=b, goal=goal.name))
