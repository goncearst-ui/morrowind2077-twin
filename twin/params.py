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
        "Хранители": 0.8, "Хищники": 1.15, "Контролёры": 1.0, "Дрейфующие": 1.0,
        "Культисты": 1.2, "Regime": 1.0})  # [док 06]; Культисты и Regime — [предл], spec 21c
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
        "Хищники": 0.35, "Контролёры": 0.10, "Хранители": 0.0, "Дрейфующие": 0.0,
        "Культисты": 0.0, "Regime": 0.10})  # [док 06]; Культисты и Regime — [предл], spec 21c
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
        "Хранители": (0, 0, 2), "Хищники": (2, 1, 0), "Контролёры": (1, 1, 1), "Дрейфующие": (0, 0, 0),
        "Культисты": (0, 2, 0), "Regime": (1, 2, 1)})   # [док 08; концепт 16.2] для Культистов и Regime
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
        "Хранители": 50.0, "Хищники": 40.0, "Контролёры": 65.0, "Дрейфующие": 20.0,
        "Культисты": 30.0, "Regime": 80.0})   # старт и «покой» оси C по укладу [предл]
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
    evo_dwell: dict = field(default_factory=lambda: {3: 5, 4: 5, 5: 3, 6: 1, 7: 5, 8: 5, 9: 5})   # выдержка, тиков: [док 07], для правила 6 [предл]
    evo_dwell_scale: float = 1.0                   # 0 = выдержки нет (обратная проверка R41)
    evo_cooldown: int = 7                          # [док 07]
    evo_hysteresis: bool = True                    # False = условия выхода не проверяются (обратная проверка R39)
    evo_exit_pred_r: float = 45.0                  # [док 07] выход из Хищников: R > 45 или P < 35
    evo_exit_pred_p: float = 35.0
    evo_exit_guard_r: float = 55.0                 # [предл] выход из Хранителей: R < 55 или P > 50
    evo_exit_guard_p: float = 50.0
    evo_exit_ctrl_c: float = 50.0                  # [предл] выход из Контролёров: нет актива или C < 50
    evo_drifter_needs_site: bool = True            # правило 7 для Дрейфующих только при наличии объекта [решение Стана 2026-10-27, вариант (а); правка docs/07 нужна]
    evo_rule5_needs_force: bool = True             # вход в Хищники требует сил для налёта: Armory не ниже assault_armory_min [док 13] и людей не меньше strike_group_max [док 13] [решение Стана 2026-10-27, вариант (б); числа предл]
    predators_keep_without_site: bool = True       # Хищники без объектов не изгоняют людей, держатся на контрабанде; только при evolution_enabled [решение Стана 2026-10-27, spec 21a-4; правка 05]
    evo_t_site: float = 25.0                       # tshock за потерянный объект (= shock_event_cap) [предл; решение Стана: территориальный шок вводим]
    evo_share_shock_k: float = 60.0                # [док 06] ShareShockK

    # --- 21c: правила 4 и 9, доктрина (docs 07; spec 21c); в evo_rule_order по умолчанию не включены ---
    evo_rule4_m: float = 30.0                      # [док 07] Культисты: M < 30 и P > 70
    evo_rule4_p: float = 70.0
    evo_rule9_c: float = 75.0                      # [док 07] Regime: C > 75, P > 50, M >= 25
    evo_rule9_p: float = 50.0
    evo_rule9_m: float = 25.0
    evo_exit_cult_m: float = 40.0                  # [предл] выход из Культистов: M > 40 или P < 55
    evo_exit_cult_p: float = 55.0
    evo_exit_regime_c: float = 65.0                # [предл] выход из Regime: C < 65 или P < 40 или M < 25
    evo_exit_regime_p: float = 40.0
    doctrine_gap_mult: float = 2.0                 # доктрина 1: зазор вход–выход вдвое больше [док 07 «двойной запас»]
    doctrine_max_factions: int = 1                 # [док 07] не более одной фракции с доктриной != 0
    doctrine2_freezes: bool = True                 # доктрина 2: выход по осям отключён [док 07]

    # --- 21b: именные, вожак, преемник (docs 05, 07, 01) ---
    leader_enabled: bool = False                   # False = журнал как до 21b; требует evolution_enabled [предл]
    evo_c_leader_loss: float = 30.0                # C падает при гибели вожака [док 05 «Control падает»; число предл]
    evo_m_leader_loss: float = 10.0                # M падает при гибели вожака [док 05; число предл]
    succession_arch: dict = field(default_factory=lambda: {"Осторожный": "Хранители", "Радикальный": "Хищники", "Идеолог": "Культисты"})   # профиль преемника -> уклад [док 05]; Идеолог — 21c
    leader_kill_seat: bool = False                 # штурм склада убивает вожака защитника; по умолчанию вожак «заперт», как в enRAGE [предл]
    leader_kill_broken: bool = False               # конец войны «сломлены» убивает вожака проигравшего [предл]
    named_max: int = 10                            # именных на фракцию [док 01, 03: 5–10]
    leader_wipe_kills_successors: bool = True      # нет объектов после гибели вожака: преемники погибают («зачистка базы») [док 05 риски]
    succession_ignores_cooldown: bool = True       # ApplySuccession пробивает паузу [док 07, 05]
    succession_resets_pending: bool = True         # и сбрасывает pending [док 07 S5]
    leader_kill_any_war_end: bool = False          # только для обратной проверки R53: убивать при любом конце войны
    leader_kill_any_site: bool = False             # только для обратной проверки R54: убивать при штурме любого объекта, не только склада

    # --- 21d: рычаги игрока (docs 08, 01; spec 21d) ---
    player_levers_enabled: bool = False            # False = журнал как до 21d; действия bribe/tip/persuade дают ошибку [предл]
    bribe_price_h: float = 100.0                   # цена +1 к H в единицах запаса, до множителя профиля [предл]
    bribe_profile_mult: dict = field(default_factory=lambda: {"Основатель": 1.0, "Радикальный": 0.5, "Осторожный": 2.0, "Идеолог": 3.0})   # [предл]
    incite_cap: float = 6.0                        # потолок добавки пары (A→B) [предл; док 08: разжигание +5]
    incite_decay: float = 1.0                      # затухание добавки [док 08: −1 / 10 суток]
    incite_decay_every: int = 10
    bribe_cooldown: int = 10                       # тиков между подкупами одного вожака [предл]
    bribe_gives_knowledge: bool = False            # только для обратной проверки R62: подкуп сам даёт знание
    persuade_min_shock: float = 25.0               # шок клана для труа [док 08: «высокий шок у них»; число предл]
    persuade_min_rep: float = 40.0                 # репутация игрока для труа [док 08: «достаточная»; число предл]
    persuade_cooldown: int = 10                    # [док 08: cooldown; число предл]
    persuade_block_archnemesis: bool = True        # H ≥ rel_level_cuts[3]: труа недоступна [док 08]
    rep_default: float = 50.0                      # репутация игрока по умолчанию (заглушка, 02) [предл]
    rep_kill_loss: float = 30.0                    # убийство именного игроком [предл]

    # --- 13a: доля фракции в регионе (spec 13a) ---
    region_share_enabled: bool = False             # False = долей нет, журнал как до 13a [предл]
    share_income_k: float = 0.0                    # доход объекта × (1 − k + k × доля владельца в регионе); 0 = не влияет [предл; пример 0.3]
    dominant_threshold: float = 0.5                # хозяин региона — доля строго больше порога [предл]
    share_denominator_owned_only: bool = False     # только для обратной проверки R70: бесхозные не считаются в знаменателе
    share_lag: bool = False                        # только для R71: доли по владению прошлого тика
    share_income_ignored: bool = False             # только для R72: k не применяется к доходу
    dominant_ge: bool = False                      # только для R73: хозяин при доле ≥ порога
    share_inertia: float = 0.0                     # только для R74: доля ползёт к цели на эту долю разрыва за тик

    # --- 15: реестр активов (spec 15) ---
    asset_cap: int | None = None                   # потолок числа активов; None = нет [док 15: 4 на старте для игры; в двойнике параметр]
    station_region: str = "orbit"                  # регион станции по умолчанию [предл]
    asset_cap_ignored: bool = False                # только для R77: потолок не проверяется
    registry_sort: bool = False                    # только для R76: индекс по сортировке имён, не по порядку списка
    station_income_mult: float = 1.0               # только для R75: станция со своей логикой дохода

    # --- 14: хозяин планеты (spec 14) ---
    planet_hegemon_enabled: bool = False           # False = статуса нет, журнал как до 14 [предл]
    hegemon_margin: int = 1                        # запас по числу активов [док 14]
    hegemon_cooldown: int = 7                      # тиков между сменами статуса [док 14: ~5–7]
    hegemon_drop_deferred: bool = False            # только для R81: запрос смены в cooldown теряется
    hegemon_stateless: bool = False                # только для R82: статус без памяти, каждый тик заново
    hegemon_count_unowned: bool = False            # только для R83: бесхозные активы считаются «фракцией»

    # --- 01: личное состояние именных (spec 01) ---
    npc_state_enabled: bool = False                # False = личных чисел нет, журнал как до 01 [предл]
    npc_loyalty_start: float = 60.0                # [предл]
    npc_fear_step: float = 30.0                    # угроза игрока [предл]
    npc_fear_decay: float = 2.0                    # в тик [предл]
    npc_avoid_fear: float = 70.0                   # порог Avoid_Package [док 01: «порог»; число предл]
    npc_share_drop_min: float = 10.0               # падение доли, которое бьёт по верности [предл]
    npc_loyalty_share_k: float = 2.0               # верность −= k × падение доли [предл]
    npc_disaffected_loyalty: float = 30.0          # [предл]
    npc_bribe_disaffected_mult: float = 0.5        # скидка подкупа недовольного [док 01; число предл]
    npc_persuade_debt_waive: float = 200.0         # долг, снимающий проверку LOW_REP [предл]
    npc_swap34: bool = False                       # только для R84: строки 3 и 4 таблицы ярлыков поменяны
    npc_steady_for_skittish: bool = False          # только для R85: ведро Skittish не выводится из Neuroticism_High

    # --- 02: репутация и узнаваемость (spec 02) ---
    reputation_enabled: bool = False               # False = штраф при убийстве сразу, как в 21d [предл]
    rep_rumor_delay: int = 2                       # тиков до доставки слуха о действии игрока [док 02: 24–72 игровых часа; число предл]
    rep_region_loss: float = 20.0                  # региональная репутация при опознании [предл]
    region_rep_default: float = 50.0               # [предл]
    region_rep_recover: float = 1.0                # шаг восстановления [док 02: естественное восстановление; число предл]
    region_rep_recover_every: int = 10
    bribe_rep_price_k: float = 1.0                 # подкуп дороже при падении региональной репутации [предл]
    rep_masked_identifies: bool = False            # только для R92: маска не меняет опознание
    rep_silence_cancels: bool = True               # только для R93: silence не отменяет слух
    rep_ignore_witnesses: bool = False             # только для R94: число свидетелей игнорируется (silence отменяет сразу)
    rep_recover_off: bool = False                  # только для R95: региональная репутация не восстанавливается

    # --- 03d: общий регион и представители (spec 03d) ---
    envoys_enabled: bool = False                   # False = представителей и доски нет [предл]
    hub_rumor_delay: int = 3                       # тиков от события до доски [предл]
    frame_h: float = 5.0                           # подстава: +5 к H [док 08: разжигание войны]
    hub_region: str = "hub"                        # регион хаба без экономики и объектов [предл]
    hub_board_when_dead: bool = False              # только для R98: доска пишет и при мёртвом представителе
    envoy_counts_manpower: bool = False            # только для R99: представитель входит в Manpower
    frame_ignores_mask: bool = False               # только для R100: подстава всегда в маске (раскрытия нет)
    frame_cap_separate: bool = False               # только для R101: потолок H подставы отдельный от подкупа
    envoy_autokill_tick: int = 0                   # только для R102: автономное убийство представителя A на этом тике

    # --- 18: личная арка (spec 18) ---
    arc_enabled: bool = False                      # False = арки нет, power() прежняя [предл]
    arc_severe_loss: float = 0.30                  # потери яруса за штурм, при которых событие тяжёлое [док 18]
    arc_harden_steady: float = 0.15                # доля Steady → закалённые [док 18; гипотеза]
    arc_harden_ordinary: float = 0.05              # [док 18; гипотеза]
    arc_break_skittish: float = 0.20               # доля Skittish → сломленные [док 18; гипотеза]
    arc_vet_w: float = 0.3                         # вес закалённых в ФакторАрки [док 13, 18]
    arc_brk_w: float = 0.3                         # вес сломленных [док 13, 18]
    arc_count_marked: bool = False                 # только для R105: помеченные снова считаются выжившими
    arc_clamp: bool = True                         # только для R106: клэмп арки до размера ведра
    arc_revert_ticks: int = 0                      # только для R108: откат keyword'ов именных через N тиков

    # --- 09 хроника двойника (spec 09) ---
    chronicle_people_drop: float = 0.20            # [предл] T2: падение Manpower за окно
    chronicle_window: int = 10                     # [предл] окно T2, тиков
    chronicle_candidates: bool = False             # [предл] кандидатные типы после G6
    chronicle_bug_no_trace: bool = False           # только для R109: строка T3 без следа
    chronicle_bug_mutate: bool = False             # только для R110: render() дописывает в журнал
    chronicle_bug_numbers: bool = False            # только для R111: T1 печатает только числа
    chronicle_bug_dup: bool = False                # только для R112: T1 по записи журнала (дубли)
    chronicle_bug_unnorm: bool = False             # только для R113: слагаемые крепости не нормированы

    # --- 16a цель лидера, KR, этап, жизненный цикл (spec 16a) ---
    obj_enabled: bool = False                      # требует leader_enabled и evolution_enabled
    obj_max_active: int = 2                        # [док 16] активных целей на мир
    obj_max_duration_kr: int = 2                   # [док 16] KR с длительностью на фракцию
    obj_stale_ticks: int = 200                     # [док 16/17] N×10, N = 20
    obj_collapse_morale: float = 15.0              # [предл] удар по морали при коллапсе
    obj_next: dict = field(default_factory=lambda: {1: 3, 3: 0, 5: 0, 4: 0, 2: 0, 0: 0})   # [предл] что после достигнутой цели
    obj_kr: dict = field(default_factory=lambda: {   # [док 16, 17; числа предл] наборы KR по целям; вид KR — см. twin/objective.py
        1: (("owns",), ("hold", "ctl", ">", 60.0, 20), ("rival_below", 0.5)),
        2: (("prosperity_at_least", 70.0), ("hold", "ctl", ">=", 60.0, 20)),
        3: (("hold", "ctl", ">=", 70.0, 20), ("rival_arch", ("Дрейфующие",)), ("manpower_ratio_at_least", 0.8)),
        4: (("owns",), ("supply_at_least", 20.0)),
        5: (("owns",), ("rival_supply_low", 15.0, 20), ("mp_up_c_not_up",)),
    })
    obj_vassal_pairs: tuple = ()                   # [предл] пары (A, B) с флагом вассальной труа; до модуля 17 задаёт сценарий
    obj_bug_ctr_keep: bool = False                 # только для R114: счётчик не сбрасывается при просадке
    obj_bug_stage_every_tick: bool = False         # только для R115: этап пишется каждый тик
    obj_bug_no_stale: bool = False                 # только для R116: протухание выключено
    obj_bug_no_cap: bool = False                   # только для R117: потолок активных целей снят
    obj_bug_no_collapse_morale: bool = False       # только для R118: мораль коллапса 0
    obj_bug_no_target_left: bool = False           # только для R119: причина TARGET_LEFT не различается

    # --- 16b стратегия: таблица (цель × трейт вожака) → множители порогов (spec 16b) ---
    strategy_enabled: bool = False                 # требует obj_enabled и npc_state_enabled
    strategy_table: tuple = (                      # (цель, трейт или None, thr_mult, thr_min, war_acc_mult); порядок = приоритет [док 16, 17; числа предл]
        (1, "Neuroticism_High", 0.85, 0.0, 1.0),
        (1, "Openness_High", 1.2, 0.0, 0.5),
        (1, "Conscientiousness_High", 1.0, 1.5, 1.0),
        (3, "Agreeableness_Low", 0.85, 0.0, 1.5),
        (3, "Openness_High", 1.2, 0.0, 0.5),
        (4, None, 2.0, 0.0, 1.0),
        (5, "Agreeableness_High", 1.0, 0.0, 0.5),
        (5, "Agreeableness_Low", 0.85, 0.0, 1.5),
    )
    strategy_bug_no_mult: bool = False             # только для R120: thr_mult не применяется
    strategy_bug_no_min: bool = False              # только для R121: thr_min не применяется
    strategy_bug_no_acc: bool = False              # только для R122: war_acc_mult не применяется
    strategy_bug_ignore_traits: bool = False       # только для R123: таблица игнорирует трейты
    strategy_bug_no_log: bool = False              # только для R124: вектор не пишется в журнал

    # --- 16c наследование цели и вендетта (spec 16c) ---
    inheritance_enabled: bool = False              # требует obj_enabled и strategy_enabled
    vendetta_max: int = 20                         # [док 16] срок вендетты, суток
    vendetta_w: float = 1.5                        # [док 16] множитель накопителя войны против виновника
    vendetta_profiles: tuple = ("Радикальный",)    # [док 16] профили, дающие вендетту при известном виновнике
    vendetta_trait: str = "Agreeableness_Low"      # [док 16] трейт преемника для вендетты
    inheritance_table: dict = field(default_factory=lambda: {   # [док 16] профиль → {известный / неизвестный виновник: правило}
        "Осторожный": {"known": ("change", 0), "unknown": ("change", 0)},
        "Основатель": {"known": ("change", 0), "unknown": ("change", 0)},   # [предл] как Осторожный
        "Радикальный": {"known": ("continue_active_else", 3), "unknown": ("change", 3)},
        "Идеолог": {"known": ("continue_ideal_else", 2), "unknown": ("continue_ideal_else", 2)},
    })
    inh_bug_ignore_cause: bool = False             # только для R125: причина смерти игнорируется (всегда «известен»)
    inh_bug_no_cap: bool = False                   # только для R126: потолок активных целей не проверяется при наследовании
    inh_bug_vendetta_extend: bool = False          # только для R127: вендетта продлевается
    inh_bug_persuade_ignores: bool = False         # только для R128: убеждение не читает вендетту
    inh_bug_swap_profiles: bool = False            # только для R129: Идеолог ведёт себя как Радикальный

    # --- 17 триада (spec 17): только тестовые поломки, механики нет ---
    tri_bug_colony_lever: bool = False             # только для R141: Тропа штурмует Колонию (колония втянута в рычаг)
    tri_bug_ignore_goal: bool = False              # только для R142: цель Метрополии игнорируется (всегда 0)
    tri_bug_vassal_h: bool = False                 # только для R143: флаг вассальной труа меняет уровни отношений
    tri_bug_same_leaders: bool = False             # только для R144: лидеры совпадают по трейтам

    # --- 19 допрос (spec 19; двойник, Creation Kit не описывает) ---
    interrogation_enabled: bool = False            # требует npc_state_enabled
    talk_threshold: float = 60.0                   # [док 19] страх, с которого пленный вообще говорит
    step_pressure: float = 10.0                    # [предл] страх за единицу давления
    morale_k: float = 0.2                          # [предл] страх за каждое очко потери морали фракции
    trap_losses: int = 3                           # [док 19] потери нападающего на ловушке
    max_traps: int = 3                             # [док 19] ловушек на мир
    purge_shock: float = 1.0                       # [предл] шок подозрения при возвращении ненапуганного
    lie_fear_cap: float = 80.0                     # [предл] Вспыльчивый лжёт при страхе ниже, говорит правду с этого значения
    stubborn_morale: float = 20.0                  # [док 19] Упёртый говорит, если мораль фракции ниже
    interrogation_base: dict = field(default_factory=lambda: {   # [док 19] база страха по ярлыку темперамента
        "Пугливый": 50.0, "Вспыльчивый": 20.0, "Бродяга": 30.0, "Хладнокровный": 10.0, "Упёртый": 0.0, "": 30.0})
    interrogation_bucket_label: dict = field(default_factory=lambda: {   # [предл] ведро → ярлык
        "skittish": "Пугливый", "ordinary": "", "steady": "Упёртый"})
    int_bug_no_trap_cost: bool = False             # только для R130: ловушка не стоит бойцов
    int_bug_lie_knowledge: bool = False            # только для R131: ложь ставит знание
    int_bug_stubborn_talks: bool = False           # только для R132: Упёртый говорит при высокой морали
    int_bug_uncounted: bool = False                # только для R133: пленный не учитывается в сумме людей
    int_bug_repeat: bool = False                   # только для R134: повторный допрос проходит
    int_bug_scared_returns: bool = False           # только для R135: напуганный отпущенный возвращается

    # --- 10 стенд сверки озвучки (spec 10): выключателя нет, модуль только читает мир ---
    voice_template_version: str = "v1"             # [предл] версия шаблона промпта
    voice_bug_facts: bool = False                  # только для R136: facts подменяет архетип
    voice_bug_verify_pass: bool = False            # только для R137: verify всегда пропускает
    voice_bug_leak_depot: bool = False             # только для R138: facts раскрывает чужой склад без знания
    voice_bug_inject_write: bool = False           # только для R139: проверке LL8 подсовывается исходник с вызовом записи
    voice_bug_inject_import: bool = False          # только для R140: проверке LL9 подсовывается исходник с импортом случайных чисел

    # --- метрики ---
    critical_manpower: int = 4                     # MinCrew перевала [предл]

    # --- 22 мир «всё включено» (spec 22): только для обратных проверок R145–R149 ---
    ig_bug_people: bool = False                    # только для R145: тайный прирост людей
    ig_bug_nolog: bool = False                     # только для R146: поле меняется без строки журнала
    ig_bug_table_skip: bool = False                # только для R147: таблица флагов пропускает один флаг
    ig_bug_random: bool = False                    # только для R148: вызов случайности в прогоне
    ig_bug_nocap: bool = False                     # только для R149: потолок активных целей снят

    # --- 23a журнал в два уровня (spec 23; двойник, Creation Kit не описывает) ---
    log_two_level_enabled: bool = False            # False = плоский журнал, как до 23a [решение Стана 2026-10-28: два уровня]
    log_sum_window: int = 10                       # окно сводного уровня, тиков [предл]
    disputed_reasons: tuple = (                    # [предл] причины «спорных событий»: подробный уровень
        "ASSAULT", "RAID", "RAID_OBJECT", "TROPHY", "CAPTURE", "RELEASE", "RELEASED_SUSPECT", "INTERROGATE", "INTERROGATE_TRAP",
        "KILL_NAMED", "LEADER_LOST", "LEADER_PLAYER", "NO_LEADER", "ARCH_CHANGE", "WAR_DECLARED", "TRUCE", "TRUCE_END", "REPARATIONS",
        "HEGEMON", "DEPOT_STRIKE", "DEPOT_MOVE", "SURRENDER", "ABANDON", "BRIBE_DEBT", "TERRITORIAL", "STRATEGY", "PRISONER_SALE", "ENVOY_INIT")
    disputed_prefixes: tuple = ("RULE_", "KR_", "WAR_END_", "PLAYER_", "VENDETTA", "OBJ_")   # [предл] семейства причин спорных событий
    disputed_target_suffixes: tuple = (".leader", ".archetype", ".owner", ".objective", ".obj_stage")   # [предл] цели, чья смена всегда спорная
    lg_bug_named_summary: bool = False             # только для R150: строки именных уходят в сводный уровень
    lg_bug_drop_sum: bool = False                  # только для R151: сводная запись теряется
    lg_bug_affects_world: bool = False             # только для R152: сводная запись меняет состояние мира

    # --- 23b именные до сотен (spec 23): named_max выше (по умолчанию 10, [док 01, 03]); список именных twin/data/named_roster.json ---
    nn_bug_promote: bool = False                   # только для R153: в мир на тике 100 добавляется именной «из ведра»
    nn_bug_roster_cap: bool = False                # только для R154: генератор списка игнорирует запрошенную численность выше 10
