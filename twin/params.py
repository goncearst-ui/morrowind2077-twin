"""Все числа модели в одном месте.

Метки в комментариях:
  [док NN]  — значение из документа модуля NN
  [предл]   — предложение, утверждено Станом 2026-10-25 как заглушка до калибровки
Меняется число — меняется только здесь.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Params:
    # --- 03 ростер ---
    steadfast_weights: tuple = (100, 50, 0)       # Steady, Ordinary, Skittish [предл]
    drain_order: str = "skittish_first"            # или "steady_first"; решение 03 S5 НЕ принято
    desertion_order: str = "skittish_first"        # [предл], согласовано с 01

    # --- 04 шок ---
    shock_decay_per_tick: float = 8.0              # [предл]
    shock_event_cap: float = 25.0                  # [док 04]
    desertion_shock_weight: float = 0.5            # [док 04], переключатель 0 / 0.5

    # --- 06 экономика ---
    per_head_cost: float = 3.0                     # Ставка: 3 порции в сутки, решение Стана 2026-10-25 (intent 03a); в 06 записано 8
    archetype_cost_mult: dict = field(default_factory=lambda: {
        "Хранители": 0.8, "Хищники": 1.15, "Контролёры": 1.0, "Дрейфующие": 1.0})  # [док 06]
    worker_yield: float = 4.0                      # доход за работника сверх MinCrew, до потолка объекта [предл], утверждено 2026-10-25 (spec 03a)
    crew_cap: dict = field(default_factory=lambda: {
        "Перевал": 40, "Насосная": 15, "Жила": 20})            # потолок работников на объекте [предл], утверждено 2026-10-25 (spec 03a; «Жила» — spec 03b)
    hunger_threshold: float = 10.0                 # [док 06]
    desertion_cost: float = 30.0                   # [док 06]
    morale_hunger_k: float = 0.3                   # [док 06]
    hunger_recovery: float = 5.0                   # [предл]
    desertion_cap_per_tick: int | None = 2         # [док 06]; None = без потолка (обратная проверка R2)
    surrender_dos: float = 5.0                     # [предл]
    trophy_rate: float = 0.4                       # [док 06]
    trophy_armory_rate: float = 0.2                # 0.4 × 0.5 [док 06]

    # --- 06 S3 регион и налёт (поставка 01) ---
    region_start: float = 60.0                     # [предл]
    region_max: float = 100.0                      # [док 06] шкала 0–100
    region_recovery: float = 1.5                   # [док 06]
    toll_drag: float = 0.005                       # решение Стана 2026-10-25 (отчёт 01, №2); в 06 записано 0.05 — противоречит тексту 06
    raid_yield: float = 4.0                        # [док 06]
    raid_cost: float = 8.0                         # [док 06]
    raid_cooldown: int = 5                         # [док 06] «~5 суток»
    share_rate: dict = field(default_factory=lambda: {
        "Хищники": 0.35, "Контролёры": 0.10, "Хранители": 0.0, "Дрейфующие": 0.0})  # [док 06]
    depot_loss_rate: float = 0.30                  # DepotLossRate: часть запаса, уничтоженная при ударе по складу [док 06]
    depot_armory_rate: float = 0.25                # DepotArmoryRate [док 06]
    raiding_archetypes: tuple = ("Хищники",)       # [док 06]
    raids_enabled: bool = True

    # --- 13 территория ---
    assault_dos: float = 10.0                      # временная замена оси R [предл]
    archetype_assault_threshold: dict = field(default_factory=lambda: {
        "Хищники": 1.1, "Контролёры": 1.6})       # [док 13]; остальные не штурмуют
    assault_armory_min: float = 25.0               # [док 13]
    assault_cooldown: int = 5                      # [предл]
    defense_factor: float = 1.3                    # [док 13]
    strike_group_max: int = 8                      # [док 13]
    defense_reinforcement: int = 0                 # [предл]
    assault_loss_cap: float = 0.25                 # [док 13]
    old_loss_formula: bool = False                 # True = «половина всей фракции» (обратная проверка R1)

    # --- 05 решения при голоде (spec 05) ---
    decisions_enabled: bool = True                 # False = обратная проверка R5
    decision_morale_threshold: float = 55.0        # [предл], решение Стана 2026-10-25 (вместо 40 из intent 05)
    expel_cap_per_tick: int = 3                    # [предл]
    expel_shock_weight: float = 0.5                # [док 04], как у дезертирства
    forced_yield: float = 2.0                      # порций в сутки с принуждённого [предл]
    forced_morale_cost: float = 0.5                # мораль в тик за принуждённого [предл]
    peaceful_decide: tuple = ("Хищники", "Контролёры")  # кто решает; Хранители и Дрейфующие — ничего (spec 05); R6 расширяет

    # --- 06 каналы дохода (spec 06): все числа [предл], получены в пробе, не из документов ---
    smuggling_enabled: bool = True
    smuggling_archetypes: tuple = ("Дрейфующие", "Хищники")   # решение Стана 2026-10-25; Хранители и Контролёры не контрабандируют
    smuggling_yield: float = 6.0                   # порций с человека в тик [предл]
    smuggling_cap_people: int = 20                 # занятых в канале не больше [предл]
    market_cap: float = 60.0                       # потолок внешнего рынка на фракцию в тик [предл]; без него деньги из воздуха
    heat_per_income: float = 0.1                   # [предл]
    heat_decay: float = 4.0                        # [предл]
    heat_threshold: float = 60.0                   # срыв при достижении [предл]
    heat_after_bust: float = 20.0                  # [предл]
    bust_detain_share: float = 0.25                # доля занятых, уходящих в «задержаны» [предл]
    bust_pause: int = 5                            # тиков простоя после срыва [предл]
    fees_enabled: bool = True
    fee_archetypes: tuple = ("Хищники",)           # решение Стана: у Контролёров уже есть пошлина
    fee_rate: float = 1.5                          # с свободного человека в тик [предл]
    fee_region_share: float = 0.3                  # не больше доли Достатка региона [предл]
    fee_drag: float = 0.02                         # регион беднеет на долю собранного [предл]
    prisoner_sale_enabled: bool = True
    sale_archetypes: tuple = ("Хищники",)
    sale_share: float = 0.5                        # доля потерь проигравшего, уходящая в «проданы» вместо «погибли» [предл]
    prisoner_price: float = 20.0                   # запас за проданного [предл]

    # --- метрики ---
    critical_manpower: int = 4                     # MinCrew перевала [предл]
