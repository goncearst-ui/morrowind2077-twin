"""Двойник v0: состояние, фазы тика, штурм.

Без случайности. Без людей поштучно: только счётчики вёдер (03).
Каждое изменение пишется в журнал (11 S2d): tick, phase, module, target, old, new, reason_code.
"""
from dataclasses import dataclass, field
from math import ceil, floor

from .params import Params
from . import evolution as evo

BUCKETS_ALIVE = ("steady", "ordinary", "skittish")
BUCKETS_OUT = ("dead", "deserted", "expelled", "detained", "sold", "captured", "held")  # куда уходят люди; сумма с живыми = старт (§1)
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
    kind: int = 0                  # 0 объект на планете, 1 станция [док 15, TF_Asset<N>_Type] (spec 15)


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
    doctrine: int = 0               # TF_Doctrine 0–2, константа фракции (spec 21c, док 07)
    named: list = field(default_factory=list)   # именные: dict(name, role, profile, alive) (spec 21b); пусто = вожака нет в модели
    leader: str | None = None       # имя действующего вожака (spec 21b)
    rank: int = 0                   # ярусы (spec 04): рядовые, ветераны, офицеры; сумма = Manpower
    vet: int = 0
    off: int = 0
    paid: dict = field(default_factory=lambda: {"rank": 0.0, "vet": 0.0, "off": 0.0})       # накопленная выплата по ярусу, вне пула
    last_paid: dict = field(default_factory=lambda: {"rank": 0, "vet": 0, "off": 0})        # тик последней выплаты по ярусу
    underpaid: dict = field(default_factory=lambda: {"rank": False, "vet": False, "off": False})
    reorg_queue: list = field(default_factory=list)  # тики срабатывания отложенных реорганизаций
    arc_hard: dict = field(default_factory=dict)   # закалённые внутри трейт-ведра: {"steady": n, "ordinary": n} (spec 18)
    arc_brk: dict = field(default_factory=dict)    # сломленные: {"skittish": n}
    ctl: float | None = None        # ось C, TF_Control (21a); None = ещё не задана
    objective: int = 0              # цель лидера 0–5 (spec 16a): 0 ВЫЖИВАНИЕ … 5 ОСВОБОЖДЕНИЕ
    obj_stage: int = 0              # этап 0–3: число выполненных KR
    obj_ctr: dict = field(default_factory=dict)      # счётчики длительности по номеру KR (с 1)
    obj_stage_tick: int = 0         # тик установки цели или последнего роста этапа (возраст = тик − это)
    obj_target: str | None = None   # имя объекта цели (задаёт сценарий)
    obj_rival: str | None = None    # соперник (задаёт сценарий)
    obj_rival_start: int = 0        # Manpower соперника при установке цели
    obj_rival_depot: str | None = None   # депо соперника при установке цели (для OBJ_TARGET_LEFT)
    obj_start: dict = field(default_factory=dict)    # свои числа при установке: mp, ctl
    held: int = 0                   # ведро «в плену у игрока» (spec 19): люди учтены, не воюют и не едят
    vendetta: int = 0               # осталось суток вендетты (spec 16c)
    vendetta_culprit: str | None = None   # виновник: фракция или "player"
    strategy_txt: str = "1/0/1"      # последний записанный вектор стратегии (spec 16b), нейтральный по умолчанию
    obj_met: list = field(default_factory=list)      # производный кэш: какие KR выполнены на прошлом шаге (нужен для причины KR_<n>)
    ax_r: float = 0.0               # ось R (21a), публикуемая производная
    ax_p: float = 0.0               # ось P (21a)
    pending: str | None = None      # уклад, к которому идёт смена (зеркало TF_PendingArch, 21a)
    pending_ticks: int = 0
    cooldown: int = 0
    changes: int = 0                # число смен уклада (метрики 21a)
    tshock: float = 0.0             # территориальный шок (21a-2): потерянные объекты, затухает как личный

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
    i: float = 0.0                                 # добавка игрока (подкуп, spec 21d), затухает
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
    prisoners: dict = field(default_factory=dict)        # id -> запись пленного (spec 19)
    prison_seq: int = 0
    traps: dict = field(default_factory=dict)            # объект -> фракция, которой готовят засаду (spec 19)
    rumors: list = field(default_factory=list)           # слухи в пути: dict(site, owner, born, due, key) (spec 08c)
    motive: set = field(default_factory=set)             # пары (фракция, объект) с мотивом (spec 08c)
    know_cursor: int = 0
    know_started: bool = False
    rumor_seq: dict = field(default_factory=dict)
    wars: dict = field(default_factory=dict)             # (зачинщик, цель) -> запись войны (spec 08b)
    war_acc: dict = field(default_factory=dict)          # (зачинщик, цель) -> счётчик решимости
    truce: dict = field(default_factory=dict)            # (A, B) по алфавиту -> тик конца перемирия
    last_war_tick: int = -10**9
    raid_last: dict = field(default_factory=dict)        # (налётчик, объект) -> тик последнего налёта (spec 20)
    evo_cursor: int = 0                                  # сколько событий из events уже учтено осями C и M (spec 21a)
    rule_hits: dict = field(default_factory=dict)        # правило -> сколько раз оно сработало первым у живой фракции (spec 21a)
    player_script: dict = field(default_factory=dict)    # tick -> [(действие, фракция, имя)]; вход сценария вместо игрока (spec 21b)
    succ_queue: list = field(default_factory=list)       # фракции, у которых вожак погиб и преемственность ещё не применена (spec 21b)
    player_funds: float = 0.0                            # деньги игрока в единицах запаса (spec 21d)
    player_rep: dict = field(default_factory=dict)       # фракция -> репутация игрока; нет записи = rep_default (spec 21d, заглушка 02)
    bribe_last: dict = field(default_factory=dict)       # фракция -> тик последнего подкупа
    persuade_last: dict = field(default_factory=dict)    # фракция -> тик последнего успешного убеждения
    share_pub: dict = field(default_factory=dict)        # (регион, фракция) -> последняя опубликованная доля (spec 13a)
    share_prev_owner: dict = field(default_factory=dict) # имя объекта -> владелец на конец прошлого тика (R71)
    envoys: dict = field(default_factory=dict)           # фракция -> представитель в хабе (spec 03d)
    hub_board: dict = field(default_factory=dict)        # ключ -> тик публикации (spec 03d)
    hub_pending: list = field(default_factory=list)      # события, ждущие публикации
    hub_cursor: int = 0
    rep_rumors: list = field(default_factory=list)       # слухи о действиях игрока в пути (spec 02)
    region_rep: dict = field(default_factory=dict)       # регион -> региональная репутация игрока (spec 02)
    hegemon: str | None = None                           # хозяин планеты: имя фракции или "Contested"; None = ещё не считали (spec 14)
    hegemon_tick: int = 0                                # тик последней смены статуса
    hegemon_last_cand: str | None = None                 # последний кандидат (только для R81)
    log_sum: dict = field(default_factory=dict)          # сводный журнал (spec 23a): (начало окна, модуль, класс цели, причина, планета) -> [число, сумма разностей, число нечисловых]

    @property
    def prosperity(self) -> float:
        return self.regions["common"]

    def registry(self):
        """Spec 15: список (индекс, имя, тип, владелец) в порядке World.sites; индекс = позиция, не меняется при добавлении в конец."""
        ss = sorted(self.sites, key=lambda s: s.name) if self.p.registry_sort else self.sites
        return [(i, s.name, s.kind, s.owner) for i, s in enumerate(ss)]

    def __post_init__(self):
        if self.p.asset_cap is not None and not self.p.asset_cap_ignored and len(self.sites) > self.p.asset_cap:
            raise ValueError(f"активов {len(self.sites)} больше потолка {self.p.asset_cap} (spec 15)")
        for s in self.sites:
            if s.kind == 1 and s.region == "common":
                s.region = self.p.station_region   # станция по умолчанию в регионе «orbit» (spec 15 §1.4)
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
        row = (self.tick, phase, module, target,
               round(old, 4) if isinstance(old, float) else old,
               round(new, 4) if isinstance(new, float) else new, reason)
        if self.p.log_two_level_enabled and not self.is_detail(target, reason):
            self._sum_row(row)
            return
        self.log.append(row)

    # ---------- 23a: два уровня журнала (spec 23) ----------
    def is_detail(self, target, reason):
        """Подробный уровень: любые именные, спорные причины и цели [предл, spec 23 §1.23a]. Всё остальное идёт в сводный."""
        p = self.p
        if p.lg_bug_named_summary:
            named = False                                       # R150: именные не защищены
        else:
            named = ".named." in target
        return (named or reason in p.disputed_reasons or reason.startswith(p.disputed_prefixes)
                or target.endswith(p.disputed_target_suffixes) or "hegemon" in target)

    def target_class(self, target):
        """Цель без имён конкретных фракций, объектов и регионов: «Метрополия.supply» -> «F.supply»."""
        parts = target.split(".")
        head = parts[0]
        if head in self.factions:
            parts[0] = "F"
        elif ">" in head:
            parts[0] = "pair"
        elif head in ("site", "region") and len(parts) > 1:
            parts[1] = "X"
        elif head in self.regions:
            parts[0] = "R"
        return ".".join(parts)

    def planet_of(self, target):
        """Планета, к которой относится запись; до 23c одна неявная планета."""
        return "main"

    def _sum_row(self, row):
        if self.p.lg_bug_drop_sum:
            return                                              # R151: запись теряется
        tick, _ph, module, target, old, new, reason = row
        w0 = tick - tick % self.p.log_sum_window
        key = (w0, module, self.target_class(target), reason, self.planet_of(target))
        e = self.log_sum.setdefault(key, [0, 0, 0])
        e[0] += 1
        num = (isinstance(old, (int, float)) and isinstance(new, (int, float)) and not isinstance(old, bool) and not isinstance(new, bool))
        if num:
            e[1] = round(e[1] + (new - old), 4) if (isinstance(new - old, float) or isinstance(e[1], float)) else e[1] + (new - old)
        else:
            e[2] += 1
        if self.p.lg_bug_affects_world and self.factions:
            f = next(iter(self.factions.values()))
            f.morale = f.morale + 0.01                          # R152: журнал меняет мир

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

    # ---------- 13a: доля фракции в регионе (производная, без памяти) ----------
    def shares(self, owners: dict | None = None) -> dict:
        """{регион: {фракция: доля}}. Доля = объектов региона у фракции ÷ всех объектов региона; бесхозные считаются в знаменателе (spec 13a §1.1)."""
        out = {}
        for r in sorted({s.region for s in self.sites}):
            ss = [s for s in self.sites if s.region == r]
            own = [(owners.get(s.name, s.owner) if owners is not None else s.owner) for s in ss]
            den = sum(1 for o in own if o is not None) if self.p.share_denominator_owned_only else len(ss)
            out[r] = {f: own.count(f) / den for f in self.factions if own.count(f)}
        return out

    def dominant(self, region: str, owners: dict | None = None):
        """Хозяин региона: фракция с долей строго больше порога (spec 13a §1.3)."""
        t = self.p.dominant_threshold
        for f, v in self.shares(owners).get(region, {}).items():
            if v > t + 1e-12 or (self.p.dominant_ge and v >= t - 1e-12):
                return f
        return None

    def _publish_shares(self):
        p = self.p
        owners = self.share_prev_owner if (p.share_lag and self.share_prev_owner) else None
        cur = self.shares(owners)
        regions = sorted({r for r, _ in self.share_pub} | set(cur))
        for r in regions:
            for f in sorted(self.factions):
                new = cur.get(r, {}).get(f, 0.0)
                old = self.share_pub.get((r, f), 0.0)
                if p.share_inertia:
                    new = old + (new - old) * p.share_inertia
                if abs(new - old) > 1e-12:
                    self.share_pub[(r, f)] = new
                    self.rec(8, "13", f"region.{r}.share.{f}", old, new, "SHARE")
        self.share_prev_owner = {s.name: s.owner for s in self.sites}

    # ---------- 18: личная арка (spec 18) ----------
    def _comp(self, f: Faction):
        return (f.steady, f.ordinary, f.skittish)

    def _arc_set(self, f: Faction, hard: dict, brk: dict, reason: str):
        old_h, old_b = sum(f.arc_hard.values()), sum(f.arc_brk.values())
        f.arc_hard, f.arc_brk = hard, brk
        self.rec(7, "18", f"{f.name}.arc.hard", old_h, sum(hard.values()), reason)
        self.rec(7, "18", f"{f.name}.arc.brk", old_b, sum(brk.values()), reason)
        self._arc_ratio(f, reason if reason != "ARC_PROMOTE" else "ARC_RATIO")

    def _arc_ratio(self, f: Faction, reason="ARC_RATIO"):
        mp = max(1, f.manpower)
        vr, br = (sum(f.arc_hard.values())) / mp, sum(f.arc_brk.values()) / mp
        for tgt, v in (("vet_ratio", vr), ("brk_ratio", br)):
            old = getattr(f, "_pub_" + tgt, 0.0)
            if abs(old - v) > 1e-12:
                self.rec(7, "18", f"{f.name}.{tgt}", old, v, "ARC_RATIO")
                setattr(f, "_pub_" + tgt, v)

    def _arc_after(self, f: Faction, before):
        """После разрешения штурма: тяжёлые ярусы → вёдра арки; именные (при npc_state_enabled) → ApplyArc."""
        from .arc import promote, clamp
        p = self.p
        after = self._comp(f)
        hard, brk, heavy = promote(before, after, f.arc_hard, f.arc_brk, p)
        hard, brk = clamp(after, hard, brk, p.arc_clamp)
        if hard != f.arc_hard or brk != f.arc_brk:
            self._arc_set(f, hard, brk, "ARC_PROMOTE")
        else:
            self._arc_ratio(f)
        if heavy and p.npc_state_enabled:
            from .npc import bucket_of
            self._npc_init()
            for n in f.named:
                if not n["alive"] or n.get("arc"):
                    continue
                b = bucket_of(n["traits"])
                if b == "steady" and "steady" in heavy:
                    n["traits"] = tuple(t for t in n["traits"] if t != "Neuroticism_High") + tuple(t for t in ("Neuroticism_Low", "TF_Hardened") if t not in n["traits"])
                    n["arc"], n["arc_tick"], n["arc_orig"] = "hardened", self.tick, n.get("arc_orig") or ()
                elif b == "skittish" and "skittish" in heavy:
                    n["traits"] = tuple(t for t in n["traits"] if t != "Neuroticism_Low") + tuple(t for t in ("Neuroticism_High", "TF_Broken") if t not in n["traits"])
                    n["arc"], n["arc_tick"], n["arc_orig"] = "broken", self.tick, ()
                else:
                    continue
                self.rec(7, "18", f"{f.name}.named.{n['name']}.arc", "-", n["arc"], "ARC_APPLY")

    def _arc_step(self):
        """Конец тика: клэмп вёдер к размеру трейт-вёдер (потери вне штурма), публикация долей; откат только для R108."""
        from .arc import clamp
        p = self.p
        for f in self.factions.values():
            hard, brk = clamp(self._comp(f), f.arc_hard, f.arc_brk, p.arc_clamp)
            if hard != f.arc_hard or brk != f.arc_brk:
                self._arc_set(f, hard, brk, "ARC_CLAMP")
            else:
                self._arc_ratio(f)
            if p.arc_revert_ticks:
                for n in f.named:
                    if n.get("arc") and self.tick - n["arc_tick"] >= p.arc_revert_ticks:
                        n["traits"] = tuple(t for t in n["traits"] if t not in ("TF_Hardened", "TF_Broken"))
                        self.rec(8, "18", f"{f.name}.named.{n['name']}.arc", n["arc"], "-", "ARC_REVERT")
                        n["arc"] = None

    # ---------- 03d: представители в хабе (spec 03d) ----------
    def _envoy_name(self, fname: str) -> str:
        return f"{fname}:представитель"

    def _envoy_init(self):
        for n, f in self.factions.items():
            if n not in self.envoys:
                self.envoys[n] = dict(name=self._envoy_name(n), role="представитель", profile="Дипломат", region=self.p.hub_region, alive=True)
                self.rec(1, "03d", f"{n}.envoy", 0, 1, "ENVOY_INIT")
                if self.p.envoy_counts_manpower:
                    self.setf(f, "ordinary", f.ordinary + 1, 1, "03d", "ENVOY_INIT")
                    f.rank += 1

    def _kill_envoy(self, fname: str) -> bool:
        e = self.envoys.get(fname)
        if e is None or not e["alive"]:
            return False
        e["alive"] = False
        self.rec(7, "03d", f"{fname}.envoy", 1, 0, "ENVOY_KILLED")
        self.events.append(dict(kind="envoy_killed", tick=self.tick, faction=fname))
        return True

    def _hub_step(self):
        """Фаза 8: события фракций попадают на доску через hub_rumor_delay тиков, если представитель жив на момент публикации."""
        p = self.p
        parts = {"leader_killed": ("faction",), "officer_killed": ("faction",), "assault": ("attacker", "defender"), "depot_strike": ("faction",),
                 "war_declared": ("initiator", "victim"), "war_end": ("initiator", "victim"), "hegemon_change": ("old", "new")}
        for e in self.events[self.hub_cursor:]:
            for key in parts.get(e["kind"], ()):
                fn = e.get(key)
                if fn in self.factions:
                    self.hub_pending.append(dict(faction=fn, kind=e["kind"], tick=e["tick"], due=e["tick"] + p.hub_rumor_delay))
        self.hub_cursor = len(self.events)
        for r in [x for x in self.hub_pending if x["due"] <= self.tick]:
            self.hub_pending.remove(r)
            if self.envoys[r["faction"]]["alive"] or p.hub_board_when_dead:
                k = f"{r['faction']}.{r['kind']}.{r['tick']}"
                self.hub_board[k] = self.tick
                self.rec(8, "03d", f"hub.board.{k}", 0, 1, "HUB_RUMOR")

    def _frame(self, victim: str, accused: str, opts: dict):
        p = self.p
        if victim not in self.factions or accused not in self.factions:
            return self._fail("frame", "NO_FACTION", faction=victim)
        if victim == accused:
            return self._fail("frame", "SAME", faction=victim)
        if not self.envoys[victim]["alive"]:
            return self._fail("frame", "NO_ENVOY", faction=victim)
        self._kill_envoy(victim)
        masked = opts.get("masked", True) or p.frame_ignores_mask
        if masked:
            r = self._register(victim, accused)
            cap = 1e9 if p.frame_cap_separate else p.incite_cap
            dh = min(p.frame_h, cap - r.i)
            if dh > 1e-9:
                old = r.i
                r.i += dh
                self.rec(7, "08", f"rel.{victim}>{accused}.i", old, r.i, "PLAYER_FRAME")
            self.events.append(dict(kind="frame", tick=self.tick, faction=victim, accused=accused))
        else:
            self.events.append(dict(kind="frame_exposed", tick=self.tick, faction=victim, accused=accused))
        if p.reputation_enabled:
            self._rep_kill(victim, self._envoy_name(victim), {"masked": opts.get("masked", True), "witnesses": opts.get("witnesses", 1)})

    # ---------- 02: репутация и узнаваемость (spec 02) ----------
    def _rep_kill(self, fname: str, name: str, opts: dict):
        """Убийство именного игроком при reputation_enabled: слух вместо мгновенного штрафа (§1.2)."""
        p = self.p
        w = opts.get("witnesses", 1)
        if w < 1:
            return
        ident = (not opts.get("masked", False)) or p.rep_masked_identifies
        self.rep_rumors.append(dict(faction=fname, born=self.tick, due=self.tick + p.rep_rumor_delay, identified=ident, witnesses=w))
        self.rec(7, "02", f"rep.rumor.{fname}.{self.tick}", 0, 1, "RUMOR_NEW")

    def _silence(self, fname: str):
        live = [r for r in self.rep_rumors if r["faction"] == fname]
        if not live:
            return self._fail("silence", "NO_RUMOR", faction=fname)
        r = max(live, key=lambda x: x["born"])
        r["witnesses"] = 0 if self.p.rep_ignore_witnesses else r["witnesses"] - 1
        if r["witnesses"] <= 0 and self.p.rep_silence_cancels:
            self.rep_rumors.remove(r)
            self.rec(7, "02", f"rep.rumor.{fname}.{r['born']}", 1, 0, "RUMOR_CANCELLED")
            self.events.append(dict(kind="rep_cancelled", tick=self.tick, faction=fname))

    def _rep_step(self):
        """Фаза 8: доставка слухов по сроку; восстановление региональной репутации."""
        p = self.p
        for r in [x for x in self.rep_rumors if x["due"] <= self.tick]:
            self.rep_rumors.remove(r)
            f = self.factions[r["faction"]]
            if r["identified"]:
                old = self.player_rep.get(f.name, p.rep_default)
                new = max(0.0, old - p.rep_kill_loss)
                self.player_rep[f.name] = new
                self.rec(8, "02", f"player.rep.{f.name}", old, new, "RUMOR_DELIVERED")
                ro = self.region_rep.get(f.home, p.region_rep_default)
                rn = max(0.0, ro - p.rep_region_loss)
                self.region_rep[f.home] = rn
                self.rec(8, "02", f"rep.region.{f.home}", ro, rn, "RUMOR_DELIVERED")
                self.rec(8, "02", f"rep.rumor.{f.name}.{r['born']}", 1, 0, "RUMOR_DELIVERED")
                self.events.append(dict(kind="rep_identified", tick=self.tick, faction=f.name))
            else:
                self.rec(8, "02", f"rep.rumor.{f.name}.{r['born']}", 1, 0, "RUMOR_UNIDENTIFIED")
                self.events.append(dict(kind="rep_unidentified", tick=self.tick, faction=f.name))
        if self.tick % p.region_rep_recover_every == 0 and not p.rep_recover_off:
            for reg in sorted(self.region_rep):
                v = self.region_rep[reg]
                if v < p.region_rep_default:
                    nv = min(p.region_rep_default, v + p.region_rep_recover)
                    self.region_rep[reg] = nv
                    self.rec(8, "02", f"rep.region.{reg}", v, nv, "REGION_REP")

    # ---------- 01: личное состояние именных (spec 01) ----------
    def _npc_init(self):
        p = self.p
        for f in self.factions.values():
            for n in f.named:
                if "fear" not in n:
                    n.update(traits=tuple(n.get("traits", ())), fear=0.0, loyalty=p.npc_loyalty_start, debt=0.0,
                             share=100 * p.share_rate[f.archetype], share_dropped=False, share_before=None, pkg=None)

    def _npc_pkg(self, f: Faction, n: dict) -> str:
        from .npc import package_for
        role = "Role_Leader" if n["role"] == "вожак" else "Role_Soldier"
        return package_for(f.archetype, role, n["traits"], n["fear"], n["loyalty"], n["share_dropped"], False,
                           self.p.npc_avoid_fear, self.p.npc_disaffected_loyalty)

    def _npc_decay(self):
        """Фаза 1: страх затухает."""
        self._npc_init()
        for f in self.factions.values():
            for n in f.named:
                if n["alive"] and n["fear"] > 0:
                    new = max(0.0, n["fear"] - self.p.npc_fear_decay)
                    self.rec(1, "01", f"{f.name}.named.{n['name']}.fear", n["fear"], new, "FEAR_DECAY")
                    n["fear"] = new

    def _npc_packages(self):
        """Конец тика: пакет каждого живого именного пишется при изменении."""
        for f in self.factions.values():
            for n in f.named:
                if n["alive"]:
                    new = self._npc_pkg(f, n)
                    if new != n["pkg"]:
                        self.rec(8, "01", f"{f.name}.named.{n['name']}.package", n["pkg"] if n["pkg"] is not None else "-", new, "PACKAGE")
                        n["pkg"] = new

    def _npc_share_update(self, f: Faction, old_arch: str):
        """Смена уклада: доля именных становится 100 × ставка нового уклада; падение бьёт по верности (spec 01 §1.5в)."""
        p = self.p
        self._npc_init()
        for n in f.named:
            if not n["alive"]:
                continue
            new_share = 100 * p.share_rate[f.archetype]
            drop = n["share"] - new_share
            self.rec(6, "01", f"{f.name}.named.{n['name']}.share", n["share"], new_share, "ARCH_CHANGE")
            if drop >= p.npc_share_drop_min:
                n["share_before"] = n["share"] if n["share_before"] is None else n["share_before"]
                new_l = max(0.0, n["loyalty"] - p.npc_loyalty_share_k * drop)
                self.rec(6, "01", f"{f.name}.named.{n['name']}.loyalty", n["loyalty"], new_l, "SHARE_DROP")
                n["loyalty"] = new_l
                if not n["share_dropped"]:
                    n["share_dropped"] = True
                    self.rec(6, "01", f"{f.name}.named.{n['name']}.share_dropped", 0, 1, "SHARE_DROP")
            elif n["share_dropped"] and n["share_before"] is not None and new_share >= n["share_before"]:
                n["share_dropped"], n["share_before"] = False, None
                self.rec(6, "01", f"{f.name}.named.{n['name']}.share_dropped", 1, 0, "SHARE_RESTORED")
            n["share"] = new_share

    def _threaten(self, fname: str, name: str):
        f = self.factions[fname]
        self._npc_init()
        n = next((x for x in f.named if x["name"] == name and x["alive"]), None)
        if n is None:
            return self._fail("threaten", "NO_TARGET", faction=fname)
        new = min(100.0, n["fear"] + self.p.npc_fear_step)
        self.rec(7, "01", f"{fname}.named.{name}.fear", n["fear"], new, "THREAT")
        n["fear"] = new

    # ---------- 14: хозяин планеты (spec 14) ----------
    def _hegemon_candidate(self) -> str:
        counts = {}
        for _, _, _, owner in self.registry():
            if owner is not None or self.p.hegemon_count_unowned:
                counts[owner] = counts.get(owner, 0) + 1
        if not counts:
            return "Contested"
        order = sorted(counts.items(), key=lambda kv: (-kv[1], str(kv[0])))
        second = order[1][1] if len(order) > 1 else 0
        top = order[0]
        if top[1] - second >= self.p.hegemon_margin and (top[1] > second or self.p.hegemon_margin == 0):
            return top[0] if top[0] is not None else "Contested"
        return "Contested"

    def _hegemon_step(self):
        p, cand = self.p, self._hegemon_candidate()
        old, apply = self.hegemon, False
        if old is None:
            apply = True
        elif p.hegemon_stateless:
            apply = cand != old
        elif cand != old and self.tick - self.hegemon_tick >= p.hegemon_cooldown:
            apply = not (p.hegemon_drop_deferred and cand == self.hegemon_last_cand)
        self.hegemon_last_cand = cand
        if apply and cand != old:
            self.hegemon, self.hegemon_tick = cand, self.tick
            self.rec(8, "14", "planet.hegemon", old if old is not None else "-", cand, "HEGEMON")
            self.events.append(dict(tick=self.tick, kind="hegemon_change", old=old, new=cand))

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
            inc = s.yield_ + self.p.worker_yield * extra
            if s.kind == 1:
                inc *= self.p.station_income_mult
            if self.p.region_share_enabled and self.p.share_income_k and not self.p.share_income_ignored:
                k = self.p.share_income_k
                inc *= 1 - k + k * self.shares().get(s.region, {}).get(f.name, 0.0)   # spec 13a §1.4
            out.append((s, extra, inc))
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
        if self.tick == 1:
            for fx in self.factions.values():
                if len(fx.named) > self.p.named_max:
                    raise ValueError(f"у фракции {fx.name} именных {len(fx.named)} больше named_max {self.p.named_max} (spec 23b)")
        if self.p.raid_discipline_enabled and not self.p.knowledge_enabled:
            raise ValueError("raid_discipline_enabled требует knowledge_enabled (нужен мотив из 08c)")
        if self.p.war_steers_attacks and not self.p.wars_enabled:
            raise ValueError("war_steers_attacks требует wars_enabled (нужна цель войны из 08b)")
        if self.p.leader_enabled and not self.p.evolution_enabled:
            raise ValueError("leader_enabled требует evolution_enabled (нужны правила 1–2 стека 07)")
        for fn in self.scheduled.get(self.tick, []):
            fn(self)
        fs = list(self.factions.values())
        if self.p.interrogation_enabled and not self.p.npc_state_enabled:
            raise ValueError("interrogation_enabled требует npc_state_enabled (spec 19)")
        # фаза 1 — затухание шока, восстановление региона
        if self.p.inheritance_enabled:
            if not (self.p.obj_enabled and self.p.strategy_enabled):
                raise ValueError("inheritance_enabled требует obj_enabled и strategy_enabled (spec 16c)")
            self._vendetta_tick()
        if self.p.reputation_enabled and not self.p.player_levers_enabled:
            raise ValueError("reputation_enabled требует player_levers_enabled (spec 02)")
        if self.p.envoys_enabled:
            if not (self.p.reputation_enabled and self.p.player_levers_enabled and self.p.leader_enabled):
                raise ValueError("envoys_enabled требует reputation_enabled, player_levers_enabled и leader_enabled (spec 03d)")
            self._envoy_init()
            if self.p.envoy_autokill_tick and self.tick == self.p.envoy_autokill_tick:
                self._kill_envoy(sorted(self.factions)[0])
        if self.p.npc_state_enabled:
            if not self.p.leader_enabled:
                raise ValueError("npc_state_enabled требует leader_enabled (нужны именные, spec 01)")
            self._npc_decay()
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
        # фазы 4–6 — модуль 07 (spec 21a): оси, стек правил, смена уклада
        if self.p.evolution_enabled:
            self.evolution_step()
        # фаза 7 — решения
        if self.p.evolution_enabled and sum(1 for f in self.factions.values() if f.doctrine) > self.p.doctrine_max_factions:
            raise ValueError("доктрина != 0 разрешена не более чем одной фракции (док 07)")
        if self.p.strategy_enabled:
            if not (self.p.obj_enabled and self.p.npc_state_enabled):
                raise ValueError("strategy_enabled требует obj_enabled и npc_state_enabled (spec 16b)")
            self._strategy_step()
        for act in self.player_script.get(self.tick, []):
            self.player_action(act)
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
        # фаза 8 — доли фракций в регионах (spec 13a): производная, ничего не меняет в других модулях
        if self.p.region_share_enabled:
            self._publish_shares()
        # фаза 8 — хозяин планеты (spec 14): хранимый статус с запасом и паузой смены
        if self.p.planet_hegemon_enabled:
            self._hegemon_step()
        if self.p.reputation_enabled:
            self._rep_step()
        if self.p.envoys_enabled:
            self._hub_step()
        if self.p.arc_enabled:
            self._arc_step()
        if self.p.npc_state_enabled:
            self._npc_packages()
        if self.p.obj_enabled:
            if not self.p.leader_enabled:
                raise ValueError("obj_enabled требует leader_enabled (spec 16a)")
            self.objective_step()

    # ---------- 06 S3: налёт на регион ----------
    def raid(self, f: Faction):
        p = self.p
        if not p.raids_enabled or f.archetype not in p.raiding_archetypes or f.manpower == 0:
            return
        if self.tick - f.last_raid < p.raid_cooldown:
            return
        if p.object_raids_enabled and f.last_assault != self.tick:
            goal = self._steer_goal(f)   # spec 08d: сначала цель войны
            if goal is not None and self._raid_skip(f, goal) is None and self.visible_power(f) / max(1e-9, self.visible_power(self.factions[goal.owner]) * p.defense_factor) > p.raid_object_threshold:
                self._war_attack(f, goal, "raid")
                self.raid_object(f, goal, forced=False)
                return
            targets = [s for s in self.sites if s.owner not in (None, f.name) and self.factions[s.owner].manpower > 0]
            for s in sorted(targets, key=lambda s: (-s.yield_, s.name)):
                d = self.factions[s.owner]
                if self._raid_skip(f, s) is not None:
                    continue
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

    def _raid_skip(self, f: Faction, s: Site):
        """Spec 20: причина, по которой автономный налёт f на объект s не идёт (NO_MOTIVE / PAUSE / PLUNDERED), иначе None.
        Каждый пропуск пишется событием raid_skipped."""
        p = self.p
        if not p.raid_discipline_enabled:
            return None
        why = None
        if (f.name, s.name) not in self.motive:
            why = "NO_MOTIVE"
        elif self.tick - self.raid_last.get((f.name, s.name), -10**9) < p.raid_pause:
            why = "PAUSE"
        else:
            d = self.factions[s.owner]
            weight = sum(x.yield_ for x in self.owned(d))
            stock = d.supply * (s.yield_ / weight) if weight > 0 else 0.0
            if stock < p.raid_min_loot_share * p.strike_group_max * p.carry_unit:
                why = "PLUNDERED"
        if why:
            self.events.append(dict(kind="raid_skipped", tick=self.tick, attacker=f.name, site=s.name, reason=why))
        return why

    def raid_object(self, a: Faction, s: Site, forced: bool):
        """Spec 03c: налёт на объект. Бой как в штурме, но объект не захватывается; выбывшие частью ранены;
        ёмкость и мораль группы решают, что несут; брошенные раненые попадают в плен по укладу обороны."""
        p = self.p
        d = self.factions[s.owner]
        if a.manpower == 0 or d is a:
            return
        self.raid_last[(a.name, s.name)] = self.tick   # spec 20: любой налёт, и принудительный, запускает паузу
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
        if p.evolution_enabled and p.predators_keep_without_site and f.archetype == "Хищники" and not self.owned(f):
            return   # spec 21a-4: без объектов не изгоняют, держатся на контрабанде
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
        base = n * (0.5 + f.armory / 100) * (0.6 + 0.8 * f.steadfast(self.p) / 100)
        if self.p.arc_enabled and (f.arc_hard or f.arc_brk):
            from .arc import factor
            k = factor(f.arc_hard, f.arc_brk, f.manpower, self.p)
            if k != 1.0:
                base *= k   # ФакторАрки (spec 18 §1.5)
        return base

    def decide_assault(self, f: Faction):
        p = self.p
        thr = p.archetype_assault_threshold.get(f.archetype)
        if thr is None or f.manpower == 0:
            return
        if f.days_supply >= p.assault_dos or f.armory < p.assault_armory_min:
            return
        if self.tick - f.last_assault < p.assault_cooldown:
            return
        if p.strategy_enabled:   # spec 16b: порог = max(thr_min, порог × thr_mult)
            tm, tmin, _ = self._strategy(f)
            thr = max(0.0 if p.strategy_bug_no_min else tmin, thr if p.strategy_bug_no_mult else thr * tm)
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
        if p.interrogation_enabled and self.traps.get(s.name) == a.name:   # spec 19 п. 5: засада по названной площадке
            self.rec(7, "19", f"trap.{s.name}", a.name, None, "INTERROGATE_TRAP")
            del self.traps[s.name]
            self.kill_many(a, 0 if p.int_bug_no_trap_cost else p.trap_losses, 7, "INTERROGATE_TRAP")
        atk, dfn = self.power(a), self.power(d) * p.defense_factor
        attacker_wins = atk > dfn
        win, lose = (a, d) if attacker_wins else (d, a)
        # Трактовка v0: в 13 «÷ СоотношениеСил» записано для победы атакующего;
        # для победы обороны берём соотношение победитель/проигравший (всегда ≥ 1).
        ratio = max(atk, dfn) / max(1e-9, min(atk, dfn))
        part = {a.name: min(a.manpower, p.strike_group_max),
                d.name: self.crew(d, s) + p.defense_reinforcement}
        mp_before = {a.name: a.manpower, d.name: d.manpower}
        comp0 = {a.name: self._comp(a), d.name: self._comp(d)}
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
        if p.arc_enabled:
            for fx in (win, lose):
                self._arc_after(fx, comp0[fx.name])
        seat = d.depot == s.name   # spec 21b: вожак сидит на складе
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
            if self.p.leader_enabled and (self.p.leader_kill_seat or self.p.leader_kill_any_site) and (seat or self.p.leader_kill_any_site):
                self.kill_named(d, self.leader_name(d), "LEADER_SEAT", 7, culprit=a.name)
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
        return self.base_h(a, b) + (r.g + r.b + r.i if r else 0.0)

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
        if p.player_levers_enabled and self.tick % p.incite_decay_every == 0:
            for (victim, offender), r in self.rel.items():
                if r.i > 0:
                    old = r.i
                    r.i = max(0.0, r.i - p.incite_decay)
                    self.rec(8, "08", f"rel.{victim}>{offender}.i", old, r.i, "INCITE_DECAY")
        self.rel_cursor = len(self.events)
        for (victim, offender), r in self.rel.items():
            h = self.base_h(victim, offender) + r.g + r.b + r.i
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
        if self.p.leader_enabled and loser and ((reason == "WAR_END_BROKEN" and self.p.leader_kill_broken) or self.p.leader_kill_any_war_end):
            self.kill_named(self.factions[loser], self.leader_name(self.factions[loser]), "LEADER_BROKEN", 8, culprit=winner)
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
                    if p.strategy_enabled and not p.strategy_bug_no_acc:   # spec 16b: прибавка × war_acc_mult зачинщика
                        add *= self._strategy(fa)[2]
                    if p.inheritance_enabled and fa.vendetta > 0 and fa.vendetta_culprit == b:   # spec 16c п. 5а
                        add *= p.vendetta_w
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

    # ---------- 21a: модуль 07, оси и стек правил ----------
    # ---------- 21b: именные, вожак, преемник (docs 05, 07) ----------
    def leader_name(self, f: Faction):
        return f.leader

    def player_action(self, act):
        """Действие игрока из сценария (двойнику игрок нужен как вход).
        kill (фракция, имя); bribe (A, B, сумма); tip (A, объект); persuade (T, O). Отказ — событие player_failed с кодом, состояние не меняется."""
        if isinstance(act, dict):
            from . import interrogation as I
            return I.act(self, act)
        kind = act[0]
        if kind == "kill":
            _, fname, name, *rest = act
            if rest and not self.p.reputation_enabled:
                raise ValueError("параметры убийства (маска, свидетели) требуют reputation_enabled (spec 02)")
            if self.p.envoys_enabled and name == self._envoy_name(fname):   # убийство представителя: инцидент через 02 (spec 03d §1.3)
                if self._kill_envoy(fname):
                    self._rep_kill(fname, name, rest[0] if rest else {})
                else:
                    self.events.append(dict(kind="player_skipped", tick=self.tick, faction=fname, name=name))
                return
            opts = rest[0] if rest else {}
            known = opts.get("witnesses", 1) >= 1 and ((not opts.get("masked", False)) or self.p.rep_masked_identifies)   # spec 16c п. 1: опознание по 02
            if not self.kill_named(self.factions[fname], name, "LEADER_PLAYER", 7, culprit="player" if known else None):
                self.events.append(dict(kind="player_skipped", tick=self.tick, faction=fname, name=name))
            elif self.p.reputation_enabled:
                self._rep_kill(fname, name, rest[0] if rest else {})
            return
        if kind == "frame":
            if not self.p.envoys_enabled:
                raise ValueError("действие frame требует envoys_enabled (spec 03d)")
            return self._frame(*act[1:])
        if kind == "silence":
            if not self.p.reputation_enabled:
                raise ValueError("действие silence требует reputation_enabled (spec 02)")
            return self._silence(*act[1:])
        p = self.p
        if kind == "threaten":
            if not p.npc_state_enabled:
                raise ValueError("действие threaten требует npc_state_enabled (spec 01)")
            return self._threaten(*act[1:])
        if not p.player_levers_enabled:
            raise ValueError("действия bribe/tip/persuade требуют player_levers_enabled (spec 21d)")
        if not p.leader_enabled:
            raise ValueError("player_levers_enabled требует leader_enabled")
        if kind == "bribe":
            self._bribe(*act[1:])
        elif kind == "tip":
            self._tip(*act[1:])
        elif kind == "persuade":
            self._persuade(*act[1:])
        else:
            raise ValueError(f"неизвестное действие игрока: {kind}")

    def _fail(self, action: str, code: str, **kw):
        self.events.append(dict(kind="player_failed", tick=self.tick, action=action, code=code, **kw))

    def _leader_profile(self, f: Faction):
        return next((n["profile"] for n in f.named if n["name"] == f.leader), None)

    def _bribe(self, a: str, b: str, amount: float):
        p = self.p
        if not p.relations_enabled:
            raise ValueError("bribe требует relations_enabled")
        f = self.factions[a]
        if f.leader is None:
            return self._fail("bribe", "NO_LEADER", faction=a)
        last = self.bribe_last.get(a)
        if last is not None and self.tick - last < p.bribe_cooldown:
            return self._fail("bribe", "COOLDOWN", faction=a)
        if self.player_funds < amount:
            return self._fail("bribe", "NO_FUNDS", faction=a)
        price = p.bribe_price_h * p.bribe_profile_mult.get(self._leader_profile(f), 1.0)
        if p.reputation_enabled:
            rr = self.region_rep.get(f.home, p.region_rep_default)
            price *= 1 + p.bribe_rep_price_k * max(0.0, 50 - rr) / 100
        ln = None
        if p.npc_state_enabled:
            self._npc_init()
            ln = next((x for x in f.named if x["name"] == f.leader), None)
            if ln is not None and ln["loyalty"] < p.npc_disaffected_loyalty and ln["share_dropped"]:
                price *= p.npc_bribe_disaffected_mult
        r = self._register(a, b)
        dh = min(amount / price, p.incite_cap - r.i)
        if dh <= 1e-9:
            return self._fail("bribe", "CAP", faction=a)
        cost = dh * price
        self.rec(7, "pl", "player.funds", self.player_funds, self.player_funds - cost, "PLAYER_BRIBE")
        self.player_funds -= cost
        old = r.i
        r.i += dh
        self.rec(7, "08", f"rel.{a}>{b}.i", old, r.i, "PLAYER_BRIBE")
        self.bribe_last[a] = self.tick
        if ln is not None:
            self.rec(7, "01", f"{a}.named.{ln['name']}.debt", ln["debt"], ln["debt"] + cost, "BRIBE_DEBT")
            ln["debt"] += cost
        self.events.append(dict(kind="player_bribe", tick=self.tick, faction=a, target=b, dh=dh, cost=cost))
        if p.bribe_gives_knowledge:
            for s in self.sites:
                if s.owner == b:
                    self._know_set(a, s.name, b, "PLAYER_TIP")

    def _tip(self, a: str, site: str):
        if not self.p.knowledge_enabled:
            raise ValueError("tip требует knowledge_enabled")
        f = self.factions[a]
        if f.leader is None:
            return self._fail("tip", "NO_LEADER", faction=a)
        s = next((x for x in self.sites if x.name == site), None)
        if s is None or s.owner is None or s.owner == a:
            return self._fail("tip", "UNKNOWN", faction=a, site=site)
        self._know_set(a, site, s.owner, "PLAYER_TIP")

    def _persuade(self, t: str, o: str):
        p = self.p
        if not p.wars_enabled:
            raise ValueError("persuade требует wars_enabled")
        f = self.factions[t]
        last = self.persuade_last.get(t)
        if last is not None and self.tick - last < p.persuade_cooldown:
            return self._fail("persuade", "COOLDOWN", faction=t)
        key = (t, o) if (t, o) in self.wars else (o, t) if (o, t) in self.wars else None
        if key is None:
            return self._fail("persuade", "NO_WAR", faction=t)
        if f.leader is None:
            return self._fail("persuade", "NO_LEADER", faction=t)
        if f.shock < p.persuade_min_shock:
            return self._fail("persuade", "NO_SHOCK", faction=t)
        waived = False
        if p.npc_state_enabled:
            self._npc_init()
            ln = next((x for x in f.named if x["name"] == f.leader), None)
            waived = ln is not None and ln["debt"] >= p.npc_persuade_debt_waive
        if self.player_rep.get(t, p.rep_default) < p.persuade_min_rep and not waived:
            return self._fail("persuade", "LOW_REP", faction=t)
        if p.persuade_block_archnemesis and self.rel_h(t, o) >= p.rel_level_cuts[3]:
            return self._fail("persuade", "ARCHNEMESIS", faction=t)
        if p.inheritance_enabled and f.vendetta > 0 and f.vendetta_culprit == "player" and not p.inh_bug_persuade_ignores:
            return self._fail("persuade", "VENDETTA", faction=t)   # spec 16c п. 5б: после ARCHNEMESIS
        self._war_end(key, "WAR_END_PLAYER")
        self.persuade_last[t] = self.tick
        self.events.append(dict(kind="player_truce", tick=self.tick, faction=t, other=o))

    def kill_named(self, f: Faction, name, reason: str, phase: int, culprit=None) -> bool:
        """Убить именного. Вожак: событие leader_killed (читает фаза 4 следующего тика). Офицер: ярус офицеров -1. Возвращает False, если цели нет или она мертва."""
        n = next((x for x in f.named if x["name"] == name), None) if name else None
        if n is None or not n["alive"]:
            return False
        n["alive"] = False
        self.rec(phase, "05", f"{f.name}.named.{name}", 1, 0, reason)
        if self.p.player_levers_enabled and reason == "LEADER_PLAYER" and not self.p.reputation_enabled:
            old = self.player_rep.get(f.name, self.p.rep_default)
            new_rep = max(0.0, old - self.p.rep_kill_loss)
            self.player_rep[f.name] = new_rep
            self.rec(phase, "pl", f"player.rep.{f.name}", old, new_rep, "PLAYER_KILL")
        if n["role"] == "вожак":
            self.rec(phase, "05", f"{f.name}.leader", name, None, reason)
            f.leader = None
            self.events.append(dict(kind="leader_killed", tick=self.tick, faction=f.name, name=name, reason=reason, culprit=culprit))
        elif n["role"] == "офицер":
            self.kill_tier(f, 1, "off", phase, "KILL_NAMED")
            self.events.append(dict(kind="officer_killed", tick=self.tick, faction=f.name, name=name, reason=reason))
        return True

    def _leader_lost(self, f: Faction):
        """Чтение события гибели вожака: C и M падают, при отсутствии объектов преемники гибнут, преемственность в очередь."""
        p = self.p
        self.setf(f, "ctl", max(0.0, f.ctl - p.evo_c_leader_loss), 4, "05", "LEADER_LOST")
        self.setf(f, "morale", max(0.0, f.morale - p.evo_m_leader_loss), 4, "05", "LEADER_LOST")
        if p.leader_wipe_kills_successors and not self.owned(f):
            for n in f.named:
                if n["role"] == "преемник" and n["alive"]:
                    n["alive"] = False
                    self.rec(4, "05", f"{f.name}.named.{n['name']}", 1, 0, "BASE_WIPED")
        if f.name not in self.succ_queue:
            self.succ_queue.append(f.name)

    # ---------- 16a: цель лидера, KR, этап, жизненный цикл ----------
    def set_objective(self, fname, obj, target=None, rival=None):
        """Установка цели сценарием (в игре — авторинг). ValueError: выключатель, потолки."""
        from . import objective as O
        p = self.p
        if not p.obj_enabled:
            raise ValueError("obj_enabled = False: цель не задаётся (spec 16a)")
        f = self.factions[fname]
        if obj not in O.NAMES:
            raise ValueError(f"неизвестная цель {obj}")
        krs = p.obj_kr.get(obj, ())
        if sum(1 for k in krs if O.duration_kr(k)) > p.obj_max_duration_kr:
            raise ValueError(f"цель {obj}: KR с длительностью больше {p.obj_max_duration_kr} на фракцию (spec 16a)")
        others = sum(1 for g in self.factions.values() if g is not f and O.is_active(g, g.objective))
        if O.is_active(f, obj) and others + 1 > p.obj_max_active and not p.obj_bug_no_cap:
            raise ValueError(f"активных целей не больше {p.obj_max_active} на мир (spec 16a)")
        f.obj_target, f.obj_rival = target, rival
        r = self.factions.get(rival) if rival else None
        f.obj_rival_start = r.manpower if r else 0
        f.obj_rival_depot = r.depot if r else None
        f.obj_start = dict(mp=f.manpower, ctl=f.ctl if f.ctl is not None else p.evo_c_rest[f.archetype])
        self._obj_reset(f, obj, "OBJ_SET", 7)

    def _vendetta_tick(self):
        """Начало тика: вендетта убывает на 1 до нуля (spec 16c п. 4). Выставленная на тике T держит 20 на тике T и 0 на T + 20."""
        for f in self.factions.values():
            if f.vendetta > 0:
                if self.p.inh_bug_vendetta_extend and f.vendetta == 10:
                    self.rec(1, "16", f"{f.name}.vendetta", 10, self.p.vendetta_max, "VENDETTA_SET")   # R127: продление
                    f.vendetta = self.p.vendetta_max
                    continue
                self.rec(1, "16", f"{f.name}.vendetta", f.vendetta, f.vendetta - 1, "VENDETTA_TICK")
                f.vendetta -= 1
                if f.vendetta == 0:
                    f.vendetta_culprit = None

    def _inherit(self, f: Faction, succ: dict):
        """Spec 16c: исход цели по (профиль преемника, причина смерти вожака); потолок активных целей важнее; вендетта."""
        from . import objective as O
        p = self.p
        ev = next((e for e in reversed(self.events) if e["kind"] == "leader_killed" and e["faction"] == f.name), None)
        culprit = ev.get("culprit") if ev else None
        known = culprit is not None or p.inh_bug_ignore_cause
        prof = succ["profile"]
        if p.inh_bug_swap_profiles and prof == "Идеолог":
            prof = "Радикальный"
        rule = p.inheritance_table.get(prof, p.inheritance_table["Основатель"])["known" if known else "unknown"]
        pred = f.objective
        keep = False
        if rule[0] == "change":
            new = rule[1]
        elif rule[0] == "continue_active_else":
            keep, new = (True, pred) if O.is_active(f, pred) else (False, rule[1])
        else:   # continue_ideal_else
            keep, new = (True, pred) if pred in (2, 5) else (False, rule[1])
        reason = "OBJ_CONTINUE" if keep else "OBJ_CHANGE"
        others = sum(1 for g in self.factions.values() if g is not f and O.is_active(g, g.objective))
        if O.is_active(f, new) and others + 1 > p.obj_max_active and not p.inh_bug_no_cap:
            keep, new, reason = False, 0, "CAP_ACTIVE_OBJ"
        if keep:
            for k in sorted(f.obj_ctr):
                self.rec(6, "16", f"{f.name}.obj_ctr.{k}", f.obj_ctr[k], 0, reason)
            f.obj_ctr = {}
            krs = p.obj_kr.get(pred, ())
            met = [(not O.duration_kr(kr)) and O.cond(self, f, kr) for kr in krs]
            self.rec(6, "16", f"{f.name}.obj_stage", f.obj_stage, sum(met), reason)
            f.obj_stage, f.obj_met, f.obj_stage_tick = sum(met), met, self.tick
            self.events.append(dict(kind="objective_continued", tick=self.tick, faction=f.name, objective=pred))
        else:
            self._obj_reset(f, new, reason, 6)
        if known and prof in p.vendetta_profiles and p.vendetta_trait in succ.get("traits", ()):
            self.rec(6, "16", f"{f.name}.vendetta", f.vendetta, p.vendetta_max, "VENDETTA_SET")
            f.vendetta, f.vendetta_culprit = p.vendetta_max, culprit or "player"

    def _strategy(self, f: Faction):
        """Spec 16b: вектор (thr_mult, thr_min, war_acc_mult) = строка таблицы (цель × трейты вожака); не хранится, считается по текущим данным."""
        from . import objective as O
        ld = next((n for n in f.named if n["name"] == f.leader and n["alive"]), None) if f.leader else None
        traits = tuple(ld.get("traits", ())) if ld else ()
        return O.strategy_vector(self.p.strategy_table, f.objective, traits, f.doctrine, self.p.strategy_bug_ignore_traits)

    def _strategy_step(self):
        """Начало фазы 7: вектор пишется в журнал, только когда изменился (смена цели, вожака, трейтов)."""
        for f in self.factions.values():
            v = self._strategy(f)
            txt = "/".join(f"{x:g}" for x in v)
            if txt != f.strategy_txt:
                if not self.p.strategy_bug_no_log:
                    self.rec(7, "16", f"{f.name}.strategy", f.strategy_txt, txt, "STRATEGY")
                f.strategy_txt = txt

    def _obj_reset(self, f: Faction, new_obj, reason, phase):
        """Смена цели: этап и счётчики в ноль, возраст с этого тика. Строки журнала только при изменении."""
        self.rec(phase, "16", f"{f.name}.objective", f.objective, new_obj, reason)
        f.objective = new_obj
        self.rec(phase, "16", f"{f.name}.obj_stage", f.obj_stage, 0, reason)
        f.obj_stage = 0
        for k in sorted(f.obj_ctr):
            self.rec(phase, "16", f"{f.name}.obj_ctr.{k}", f.obj_ctr[k], 0, reason)
        f.obj_ctr = {}
        f.obj_met = []
        f.obj_stage_tick = self.tick

    def objective_step(self):
        """Конец тика (фаза 8, после штурмов и налётов этого тика — иначе IN2 «этап растёт на тике захвата» не выполнить): пересчёт KR, счётчиков, этапа; достигнута / протухла (spec 16a п. 4–5). Решения следующего тика (16b) видят этап этого."""
        from . import objective as O
        p = self.p
        for f in self.factions.values():
            if f.objective == 0:
                continue
            krs = p.obj_kr[f.objective]
            met = []
            for i, kr in enumerate(krs, 1):
                c = O.cond(self, f, kr)
                if O.duration_kr(kr):
                    old = f.obj_ctr.get(i, 0)
                    new = old + 1 if c else (old if p.obj_bug_ctr_keep else 0)
                    if new != old:
                        f.obj_ctr[i] = new
                        self.rec(8, "16", f"{f.name}.obj_ctr.{i}", old, new, "OBJ_CTR")
                    met.append(new >= kr[-1])
                else:
                    met.append(c)
            stage = sum(met)
            prev = f.obj_met or [False] * len(met)
            if stage != f.obj_stage:
                n = next(i for i, (a, b) in enumerate(zip(prev, met), 1) if a != b)
                old = f.obj_stage
                f.obj_stage = stage
                self.rec(8, "16", f"{f.name}.obj_stage", old, stage, f"KR_{n}")
                if stage > old:
                    f.obj_stage_tick = self.tick
            elif p.obj_bug_stage_every_tick:
                self.log.append((self.tick, 8, "16", f"{f.name}.obj_stage", stage, stage, "KR_0"))
            f.obj_met = met
            if krs and stage == len(krs):
                nxt = p.obj_next[f.objective]
                self.events.append(dict(kind="objective_done", tick=self.tick, faction=f.name, old=f.objective, new=nxt))
                self._obj_reset(f, nxt, "OBJ_DONE", 8)
                continue
            if not p.obj_bug_no_stale and self.tick - f.obj_stage_tick + 1 >= p.obj_stale_ticks:
                r = self.factions.get(f.obj_rival) if f.obj_rival else None
                left = r is not None and r.depot != f.obj_rival_depot and not p.obj_bug_no_target_left
                reason = "OBJ_TARGET_LEFT" if left else "OBJ_STALE"
                self.events.append(dict(kind="objective_stale", tick=self.tick, faction=f.name, old=f.objective, reason=reason))
                self._obj_reset(f, 0, reason, 8)

    def _apply_succession(self, f: Faction) -> bool:
        """ApplySuccession (фаза 6): правило 1 или 2, мимо выдержки и паузы. True = стек для фракции в этот тик не вычисляется."""
        p = self.p
        if f.cooldown > 0 and not p.succession_ignores_cooldown:
            return False   # обратная проверка R50: пауза не пробита, преемственность ждёт
        self.succ_queue.remove(f.name)
        succ = next((n for n in f.named if n["role"] == "преемник" and n["alive"]), None)
        if succ is None:
            cand, rule = "Дрейфующие", 1
        else:
            succ["role"] = "вожак"
            f.leader = succ["name"]
            self.rec(6, "05", f"{f.name}.leader", None, succ["name"], "RULE_2")
            cand, rule = p.succession_arch[succ["profile"]], 2
        if p.obj_enabled and f.objective != 0 and (succ is None or not p.inheritance_enabled):   # spec 16a п. 5б: цель вожака не переходит к преемнику; с 16c — по таблице ниже
            if succ is None:
                if not p.obj_bug_no_collapse_morale:
                    self.setf(f, "morale", max(0.0, f.morale - p.obj_collapse_morale), 6, "16", "OBJ_COLLAPSE")
                self._obj_reset(f, 0, "OBJ_COLLAPSE", 6)
            else:
                self._obj_reset(f, 0, "OBJ_SUCCESSOR", 6)
        self.rule_hits[rule] = self.rule_hits.get(rule, 0) + 1
        keep = (f.pending, f.pending_ticks)
        if p.succession_resets_pending:
            self._pending(f, None, 0)
        if cand != f.archetype:
            self._switch(f, cand, rule)   # _switch сам сбрасывает pending
            if not p.succession_resets_pending:
                self._pending(f, *keep)   # только обратная проверка R51: ожидание не сброшено (видно в журнале)
        if p.obj_enabled and p.inheritance_enabled and succ is not None:
            self._inherit(f, succ)   # spec 16c: после смены уклада
        return True

    def _evo_axes(self, f: Faction):
        """Фаза 4: оси R, P (производные) и C, M (события тика читаются на следующем тике, как в 08a)."""
        p = self.p
        if f.ctl is None:
            f.ctl = p.evo_c_rest[f.archetype]
            self.rec(4, "07", f"{f.name}.C", None, f.ctl, "AXIS_INIT")
        r, pp = evo.axis_r(p, f.days_supply, f.manpower), evo.axis_p(p, f.shock, f.tshock)
        self.setf(f, "ax_r", r, 4, "07", "AXIS")
        self.setf(f, "ax_p", pp, 4, "07", "AXIS")

    def _evo_events(self):
        """События с прошлого чтения: победа поднимает C и M, дезертирство опускает C."""
        p = self.p
        new = self.events[self.evo_cursor:]
        self.evo_cursor = len(self.events)
        for e in new:
            if e["kind"] == "assault" and e["attacker_wins"]:
                f = self.factions[e["attacker"]]
                self.setf(f, "ctl", min(100.0, f.ctl + p.evo_c_win), 4, "07", "C_WIN")
                self.setf(f, "morale", min(p.evo_m_max, f.morale + p.evo_m_win), 4, "07", "M_WIN")
            elif e["kind"] == "war_end" and e.get("winner"):
                f = self.factions[e["winner"]]
                self.setf(f, "ctl", min(100.0, f.ctl + p.evo_c_win), 4, "07", "C_WIN")
            elif e["kind"] == "leader_killed" and p.leader_enabled:
                self._leader_lost(self.factions[e["faction"]])
            elif e["kind"] == "desertion":
                f = self.factions[e["faction"]]
                self.setf(f, "ctl", max(0.0, f.ctl - p.evo_c_desertion * e["n"]), 4, "07", "C_DESERTION")
            if e["kind"] == "assault" and e["attacker_wins"]:
                f = self.factions[e["defender"]]
                self.setf(f, "tshock", f.tshock + p.evo_t_site, 4, "04", "TERRITORIAL")
            elif e["kind"] == "surrender":
                f = self.factions[e["faction"]]
                self.setf(f, "tshock", f.tshock + p.evo_t_site, 4, "04", "TERRITORIAL")

    def evolution_step(self):
        p = self.p
        fs = list(self.factions.values())
        for f in fs:
            if f.ctl is None:
                self._evo_axes(f)   # первичная инициализация C до чтения событий
        for f in fs:
            self.setf(f, "tshock", max(0.0, f.tshock - p.shock_decay_per_tick), 4, "04", "DECAY_T")
        self._evo_events()
        for f in fs:
            if f.manpower == 0:
                continue
            rest = p.evo_c_rest[f.archetype]
            if f.ctl > rest:
                self.setf(f, "ctl", max(rest, f.ctl - p.evo_c_relax), 4, "07", "C_RELAX")
            elif f.ctl < rest:
                self.setf(f, "ctl", min(rest, f.ctl + p.evo_c_relax), 4, "07", "C_RELAX")
            if f.days_supply >= p.hunger_threshold and p.evo_m_recover > 0 and f.morale < p.evo_m_max:
                self.setf(f, "morale", min(p.evo_m_max, f.morale + p.evo_m_recover), 4, "07", "M_RECOVER")
            self._evo_axes(f)
        # фаза 6 — ApplySuccession (spec 21b): правила 1–2 выше всех числовых, мимо выдержки и паузы
        done = set()
        for f in fs:
            if f.name in self.succ_queue:
                if f.manpower == 0:
                    self.succ_queue.remove(f.name)
                elif self._apply_succession(f):
                    done.add(f.name)
        # фаза 5 — проверка правил; фаза 6 — применение
        for f in fs:
            if f.manpower == 0:
                continue
            if f.name in done:
                continue
            if f.cooldown > 0:
                self.setf(f, "cooldown", f.cooldown - 1, 5, "07", "COOLDOWN")
                continue
            asset = bool(self.staffed(f))
            rule = evo.first_rule(p, f.ax_r, f.ax_p, f.ctl, f.morale, asset, f.archetype, bool(self.owned(f)),
                                 f.armory >= p.assault_armory_min and f.manpower >= p.strike_group_max)
            if rule is not None:
                self.rule_hits[rule] = self.rule_hits.get(rule, 0) + 1
            cand = evo.RULE_TARGET[rule] if rule is not None else None
            if cand is None or cand == f.archetype or not evo.exit_open(p, f.archetype, f.ax_r, f.ax_p, f.ctl, asset, f.morale, f.doctrine):
                self._pending(f, None, 0)
                continue
            n = f.pending_ticks + 1 if cand == f.pending else 1
            self._pending(f, cand, n)
            if n >= evo.dwell(p, rule):
                self._switch(f, cand, rule)

    def _pending(self, f: Faction, cand, n):
        self.setf(f, "pending", cand, 5, "07", "PENDING")
        self.setf(f, "pending_ticks", n, 5, "07", "PENDING")

    def _switch(self, f: Faction, cand: str, rule: int):
        p = self.p
        old = f.archetype
        self.setf(f, "archetype", cand, 6, "07", f"RULE_{rule}")
        dm = -(p.share_rate[old] - p.share_rate[cand]) * p.evo_share_shock_k
        if dm:
            self.setf(f, "morale", max(0.0, min(p.evo_m_max, f.morale + dm)), 6, "07", "SHARE_SHOCK")
        self.setf(f, "cooldown", p.evo_cooldown, 6, "07", f"RULE_{rule}")
        f.changes += 1
        self._pending(f, None, 0)
        if self.p.npc_state_enabled:
            self._npc_share_update(f, old)
        self.events.append(dict(kind="archetype_change", tick=self.tick, faction=f.name, frm=old, to=cand, rule=rule))
