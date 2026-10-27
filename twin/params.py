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

    # --- 03c налёт на объект, раненые (spec 03c): все числа [предл] ---
    object_raids_enabled: bool = True              # автономный выбор налёта на объект; принудительные налёты сценария работают всегда
    wounded_share: float = 0.5                     # доля выбывших, ставших ранеными (остальные гибнут)
    recovery_ticks: int = 15                       # срок выздоровления; в SS2 3–30 суток случайно, у нас без случайности
    carry_unit: float = 30.0                       # запаса на здорового налётчика
    wounded_load: float = 2.0                      # единиц ёмкости на раненого товарища
    carry_morale_threshold: float = 40.0           # мораль группы: ≥ несём раненых первыми, < сначала добыча
    abandon_morale_cost: float = 5.0               # мораль за каждого брошенного
    raid_object_threshold: float = 1.0             # видимая сила / (сила обороны × ФакторОбороны) для выбора цели

    # --- 04 оплата по ярусу (spec 04); порядок во всех кортежах: (рядовые, ветераны, офицеры) ---
    tiers_enabled: bool = True                     # False = журнал как до 04 (регрессия строка в строку)
    tier_start_share: tuple = (0.7, 0.2, 0.1)      # состав на старте [решение Стана 2026-10-26]
    tier_power_weight: tuple = (0.8, 1.2, 2.0)     # вес силы яруса, среднее по 70/20/10 равно 1.0 [предл]
    tier_pay_weight: tuple = (1.0, 2.0, 4.0)       # вес выплаты на человека [предл]
    underpay_ticks: tuple = (10, 15, 25)           # терпение недоплаты по ярусам, тиков [предл]
    underpay_morale: float = 0.5                   # мораль в тик × доля недоплаченных по численности [предл]
    reorg_ticks: int = 10                          # задержка реорганизации после выбытия офицера или ветерана [предл]
    reorg_ticks_urgent: int = 3                    # срочная: заполнено офицерских мест меньше reorg_urgent_fill [предл], идея enRAGE, принята 2026-10-26
    reorg_urgent_fill: float = 0.5                 # [предл]
    gear_good: tuple = (60, 45, 35)                # TF_Armory от которого ярус в ступени Good [предл]; для рядовых совпадает с 06
    gear_worn: tuple = (25, 15, 10)                # от которого Worn (иначе Rags) [предл]

    # --- 08a отношения и обида (spec 08a); порядок осей и весов: см. комментарии ---
    relations_enabled: bool = False                # False = журнал как до 08a (регрессия строка в строку) [предл]
    rel_axes: dict = field(default_factory=lambda: {   # (Exp, Ins, Leg) [док 08]
        "Хранители": (0, 0, 2), "Хищники": (2, 1, 0), "Контролёры": (1, 1, 1), "Дрейфующие": (0, 0, 0)})
    rel_weights: tuple = (2.0, 1.5, -1.0, 2.0)     # Exp, Ins, Leg(A) при Leg(B) > 0, добавка при Leg(B) = 0 и Leg(A) >= 1 [док 08]
    rel_level_cuts: tuple = (1.0, 3.0, 5.0, 7.0)   # Ally < 1 <= Neutral < 3 <= напряжение < 5 <= Enemy < 7 <= Archnemesis [док 08]
    grudge_event: float = 3.0                      # налёт на объект или штурм: обида пострадавшего к обидчику [док 08]
    grudge_cap: float = 4.0                        # потолок затухающей части [предл], пункт 5 spec 08a
    grudge_push: float = 1.0                       # лимит сдвига g за тик, вверх и вниз [предл]
    grudge_decay_step: float = 0.5                 # [док 08]
    grudge_decay_every: int = 10                   # тиков между шагами затухания, один таймер на все пары [док 08]
    betrayal: float = 6.0                          # «предательство»: сразу, мимо потолка и лимита толчка, не затухает [док 08; мимо лимита — предл]
    grudge_pause: bool = True                      # пауза затухания, пока обидчик держит захваченный объект [предл]

    # --- 08c мотив и знание (spec 08c); порог нужды — существующий hunger_threshold [док 06] ---
    knowledge_enabled: bool = False                # False = журнал как до 08c (регрессия строка в строку) [предл]
    rumor_delay: int = 7                           # тиков от события до слуха [предл]; ориентир 02: «события недельной давности у соседей»
    knowledge_expires_on_owner_change: bool = True  # знание гаснет при смене владельца [решение Стана 2026-10-26]; False — только для обратной проверки R20
    rumor_drop_stale: bool = True                  # слух, пришедший после смены владельца, отбрасывается [предл]; False — только для R22

    # --- 08b война как состояние пары (spec 08b); линия войны — rel_level_cuts[3] [док 08], порог снаряжения — assault_armory_min [док 13] ---
    wars_enabled: bool = False                     # False = журнал как до 08b (регрессия строка в строку) [предл]
    war_chance_base: float = 0.5                   # прибавка к счётчику решимости в тик на линии Enemy; было 4.0 (08b), стало 0.5 [решение Стана 08e: редкость, спрос 1]
    war_chance_slope: float = 1.0                  # плюс за каждую единицу H сверх линии; было 3.0, стало 1.0 [решение Стана 08e]
    war_chance_cap: float = 8.0                    # потолок прибавки в тик; было 15, стало 8 [решение Стана 08e]
    war_world_gap: int = 3                         # тиков между объявлениями в мире [enRAGE]
    war_max_per_faction: int = 2                   # действующих войн у фракции, считая защиту [предл]
    war_min_dos: float = 1.0                       # запас зачинщика, суток, не меньше [предл]
    war_needs_motive: bool = True                  # объявление требует мотив 08c [предл]
    war_cost: float = 0.25                         # цена войны в сутки с каждой стороны: доля расхода (war_cost_share_of_expense) или число запаса; было 5.0 числом, стало 25% расхода [решение Стана 08e: вопрос 2]
    war_cost_share_of_expense: bool = True         # True = war_cost читается как доля расхода фракции [решение Стана 08e]
    war_reparation_share: float = 0.40             # доля запаса проигравшего, переходящая победителю при конце войны; 0 = нет репараций [решение Стана 08e: вопрос 4]
    war_grace: int = 3                             # суток до проверки «сломлены» и «выдохлись» [enRAGE]
    war_broken_share: float = 0.25                 # людей у защитника от старта войны [enRAGE]
    war_exhausted_share: float = 0.40              # людей у зачинщика от старта войны [enRAGE]
    war_max_days: int = 40                         # срок войны, «сдались»; было 20, стало 40 [решение Стана 08e: вопрос 6]
    war_truce: int = 15                            # тиков запрета новой войны пары после конца; было 4 [enRAGE: 3–5], стало 15 [решение Стана 08e: вопрос 1]

    # --- 08d война направляет нападения (spec 08d) ---
    war_steers_attacks: bool = False               # False = нападения как до 08d (регрессия строка в строку) [предл]

    # --- 20 стабильный мир: дисциплина налётов (spec 20) ---
    raid_discipline_enabled: bool = False          # False = налёты как до задачи 20 (регрессия строка в строку) [предл]
    raid_pause: int = 15                           # суток, пока тот же налётчик не бьёт тот же объект [решение Стана 2026-10-27; число предл]
    raid_min_loot_share: float = 0.25              # доля ёмкости группы; ниже ожидаемой добычи налёта нет [решение Стана 2026-10-27; число предл]

    # --- 21a модуль 07: оси и стек правил смены уклада (spec 21a); ось C и подъём M — правила двойника, в документах их нет ---
    evolution_enabled: bool = True                 # по умолчанию включено [решение Стана 2026-10-27]; прежние 70 сценариев run() гонит с False (spec 21a-2 §1.4)
    evo_r_full_days: float = 30.0                  # R = 100 при запасе в столько суток [предл; в 00 «R = f(DaysOfSupply, Manpower)»]
    evo_p_scale: float = 2.5                       # P = scale × личный шок; территориального шока нет (13) [предл]; при 1.5 правило 5 в живых прогонах не срабатывало ни разу (отчёт 21a), при 2.5 срабатывает
    evo_c_rest: dict = field(default_factory=lambda: {
        "Хранители": 50.0, "Хищники": 40.0, "Контролёры": 65.0, "Дрейфующие": 20.0})   # старт и «покой» оси C по укладу [предл]
    evo_c_win: float = 10.0                        # C за победу в штурме или войне [предл, концепт §13.2]
    evo_c_desertion: float = 1.0                   # C за каждого дезертира [предл, §13.2]
    evo_c_relax: float = 1.0                       # затухание C к покойному значению в сутки [предл]
    evo_m_recover: float = 1.0                     # M в сутки при запасе не ниже порога голода [предл, §13.2 «приход ресурсов»]
    evo_m_win: float = 5.0                         # M за победный штурм [предл, §13.2 «победа»]
    evo_m_max: float = 100.0
    evo_rule_order: tuple = (3, 5, 6, 7, 8)        # [док 07] порядок стека; 1–2 (вожак) — 21b, 4 и 9 — 21c
    evo_rule3_m: float = 25.0                      # [док 07] бунт: M < 25 и C > 70
    evo_rule3_c: float = 70.0
    evo_rule5_r: float = 25.0                      # [док 07] Хищники: R < 25 и P > 60
    evo_rule5_p: float = 60.0
    evo_rule6_c: float = 60.0                      # [док 07] Контролёры: контроль актива и C > 60
    evo_rule7_r: float = 70.0                      # [док 07] Хранители: R > 70 и P < 35
    evo_rule7_p: float = 35.0
    evo_rule8_m: float = 20.0                      # [док 07] Дрейфующие: M < 20
    evo_dwell: dict = field(default_factory=lambda: {3: 5, 5: 3, 6: 1, 7: 5, 8: 5})   # выдержка, тиков: [док 07], для правила 6 [предл]
    evo_dwell_scale: float = 1.0                   # 0 = выдержки нет (обратная проверка R41)
    evo_cooldown: int = 7                          # [док 07]
    evo_hysteresis: bool = True                    # False = условия выхода не проверяются (обратная проверка R39)
    evo_exit_pred_r: float = 45.0                  # [док 07] выход из Хищников: R > 45 или P < 35
    evo_exit_pred_p: float = 35.0
    evo_exit_guard_r: float = 55.0                 # [предл] выход из Хранителей: R < 55 или P > 50
    evo_exit_guard_p: float = 50.0
    evo_exit_ctrl_c: float = 50.0                  # [предл] выход из Контролёров: нет актива или C < 50
    evo_drifter_needs_site: bool = True            # правило 7 для Дрейфующих только при наличии объекта [решение Стана 2026-10-27, вариант (а); правка docs/07 нужна]
    evo_t_site: float = 25.0                       # tshock за потерянный объект (= shock_event_cap) [предл; решение Стана: территориальный шок вводим]
    evo_share_shock_k: float = 60.0                # [док 06] ShareShockK

    # --- метрики ---
    critical_manpower: int = 4                     # MinCrew перевала [предл]
