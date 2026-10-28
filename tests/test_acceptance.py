"""Чек-лист приёмки: spec 00 §6 + spec 01 §2. Меняет только Стан (гейт protect-tests).
2026-10-25: пометка «ожидаемо красный» с DS4 снята по утверждённому plan 01, шаг 5; добавлен RG1.
2026-10-25: добавлены RG2–RG5 и обратная проверка R3 по утверждённому plan 03a, шаг 3. Пометка DS4 не менялась.
2026-10-25: добавлены OB1, RG6 и обратная проверка R4 по утверждённому plan 03b, шаг 4. OB2 добавлен после решения Стана смягчить критерий с 20 до 10 тиков (отчёт 03b).
2026-10-26: добавлены RD1–RD4 (RD3S — вариант RD3 с обороной Хищников), R9, R10; счёт людей включает раненых, захваченных и принятых — по утверждённому plan 03c, шаги 3 и 6.
2026-10-25: добавлены IC1, IC2, IC3, IC5, R7, R8 по утверждённому plan 06, шаг 5; пометка «известный дефект» с DS4 снята — DS4 стал зелёным (см. отчёт 06; указание в самой пометке).
2026-10-25: добавлены HD1–HD3, R5, R6; критерий RG4 переписан (люди ≥ 95, мораль < 55); счёт людей включает изгнанных — по утверждённому plan 05, шаг 5 (решение Стана: порог морали 55, RG4 вариант а).
2026-10-26: добавлены RP1, RP2 и обратная проверка R11 по утверждённому plan 07, шаг 3 (решения Стана: границы RP1 5–10; налёт на регион без потерь).
2026-10-26: добавлены RT1–RT4, RT2b, обратные R12–R15, регрессия «tiers_enabled = False», инвариант ярусов RT5 и проверка ступеней снаряжения по утверждённому plan 04, шаг 7 (решения Стана: ярусы 70/20/10, срочная реорганизация 3 тика).
2026-10-26: добавлены RL1–RL6, обратные R16–R18 и проверка «модуль 08 только читает» по утверждённому plan 08a, шаги 6–7 (решения Стана: обида направленная, претензии вынесены в заявку 08c, вес штурма через паузу).
2026-10-26: добавлены MK1–MK6, обратные R19–R22, регрессия «knowledge_enabled = False» против tests/baseline_pre08c.json и проверка «модуль 08c только читает» по утверждённому plan 08c, шаги 6–7 (решения Стана: знание приходит слухом, держится до смены владельца, виды ресурсов не вводятся, мотив пока только считается; копирование эталона разрешено).
2026-10-26: добавлены WR1–WR7d, обратные R23–R29, регрессия «wars_enabled = False» против tests/baseline_pre08b.json, проверки WR8 («война только цена») и WR9 (требования) по утверждённому plan 08b, шаги 6–7 (решения Стана: объявление по накопителю с мотивом, лимиты 1 в 3 суток и 2 на фракцию, цена 5 запаса в сутки; копирование эталона разрешено). В test_scenario_green добавлены RL, MK и WR.
2026-10-26: добавлены WS1–WS3, обратные R30–R31, регрессия «war_steers_attacks = False» против tests/baseline_pre08d.json и проверка WS4 (требование) по утверждённому plan 08d, шаги 4–5 (решения Стана: война направляет выбор цели штурма и налёта, безнадёжная цель — бьёт других, защитник без изменений; копирование эталона разрешено).
2026-10-26: добавлены WE1–WE3e (WE4 внутри WE3a–WE3c), обратные R32–R34 и регрессия против tests/baseline_pre08e.json (сценарии без войны с wars_enabled = False; WR и WS со старыми числами 08b, закреплёнными в обстановке) по утверждённому plan 08e, шаги 5–6 (решения Стана: накопитель 0.5 / 1.0 / 8, перемирие 15, цена 25% расхода, репарации 40% запаса проигравшего, срок 40; копирование эталона разрешено).
2026-10-27: добавлены RB1–RB5, SW1, SW2, обратные R35–R38, регрессия «raid_discipline_enabled = False» против tests/baseline_pre20.json и проверка RB6 (требование) по утверждённому plan 20, шаги 4–5 (решения Стана: налёт по нужде, пауза после налёта на ту же цель 15 суток, нет налёта на разграбленный объект; копирование эталона разрешено).
2026-10-27: добавлены EV1–EV9, EV12–EV15 (список EV_SCENARIOS), EV10 и EV11 как отдельные тесты, обратные R39–R45 и регрессия «evolution_enabled = False» против tests/baseline_pre21a.json по утверждённому plan 21a, шаги 4–5 (решения Стана: полный 07 тремя задачами, оси R, P, C формулами [предл], у Дрейфующих нет отдельного условия выхода; утверждение блоком «по рекомендации … полностью одобряю до следующего модуля»; копирование эталона и правка tests/ разрешены). Прежние проверки не менялись.
2026-10-27: добавлены EV16, EV17, критерий «X6 жива» в EV13, переписан EV7 (добавлена фракция C без объекта), обратные R46–R47 и тест значения по умолчанию по утверждённому plan 21a-2 (решения Стана: правило 7 для Дрейфующих только с объектом, территориальный шок, смена уклада включена по умолчанию; run() гонит прежние 70 сценариев с evolution_enabled = False, потому что 17 из них краснеют при включённой смене уклада). Критерии прежних сценариев не менялись.
2026-10-27: добавлены EV18 и обратная R48 по утверждённому plan 21a-3 (решение Стана: вход в Хищники по правилу 5 требует сил для налёта). Прежние проверки не менялись.
2026-10-27: добавлены EV20–EV27 (EV26, EV26b, EV26c), EV30, EV31, EV28 (журналы EV1–EV19 при выключенном вожаке против tests/baseline_pre21b.json), EV29 (люди сохраняются: общие тесты по списку EV_SCENARIOS), обратные R50–R54 по утверждённому plan 21b (Стан: «утверждаю 21b», правка tests/test_acceptance.py и новый эталон разрешены). Прежние проверки не менялись.
2026-10-27: добавлены PL1–PL11 (PL8, PL8b, PL8c), PL12 (журналы EV20–EV31 против tests/baseline_pre21d.json, ошибка действий без выключателя), обратные R55–R62 по утверждённому plan 21d (Стан: «утверждаю 21d», правка tests/test_acceptance.py и новый эталон разрешены). Прежние проверки не менялись.
2026-10-27: добавлены CR1–CR5, CR7, CR7k, CR8, CR9 (список EV_SCENARIOS), CR6 (обход стека), CR10 (две доктрины — ошибка), CR11 (журналы EV1–EV31 и PL1–PL11 при порядке по умолчанию против tests/baseline_pre21c.json), обратные R63–R68 по утверждённому plan 21c (Стан: «утверждаю 21c», правка tests/test_acceptance.py и новый эталон разрешены). Прежние проверки не менялись.
2026-10-27: добавлены EV19 и обратная R49 по утверждённому plan 21a-4 (решение Стана: Хищники без объектов не изгоняют людей, а продолжают контрабанду). Прежние проверки не менялись.
2026-10-27: общий механизм для задач очереди plans/QUEUE.md (Стан: «исполняй все с разрешением на правку tests/test_acceptance.py и на эталон»): сценарии задач 13a и далее регистрируются в twin/extra.py (EXTRA) и проходят общие тесты зелёности, детерминизма и обратных проверок; эталоны tests/baseline_pre<NN>.json сверяются общим тестом test_flags_off_matches_baseline (список BASELINES). Прежние проверки не менялись.
2026-10-27: задача 09 (хроника): сценарии HC1–HC9 (twin/x09.py) идут общими тестами EXTRA, обратные R109–R113 общим тестом REVERSE; эталон не нужен (журналы мира не меняются). Прежние проверки не менялись.
2026-10-27: задача 16a (цель лидера): сценарии IN1–IN10 (twin/x16a.py) общими тестами EXTRA, обратные R114–R119 общим тестом REVERSE, IN10 через эталон tests/baseline_pre16a.json (список BASELINES). Прежние проверки не менялись.
2026-10-27: задача 16b (стратегия): сценарии IS1–IS9 (twin/x16b.py) общими тестами EXTRA, обратные R120–R124 общим тестом REVERSE, журналы всех сценариев при strategy_enabled = False против tests/baseline_pre16b.json (список BASELINES); в IS2 добавлена вторая проверка (Хищники + Conscientiousness_High), потому что на числах spec thr_min = 1.5 ниже порога Контролёров 1.6 и обратная R121 не краснела. Прежние проверки не менялись.
2026-10-27: задача 16c (наследование и вендетта): сценарии IV1–IV10 (IV8b — накопитель; twin/x16c.py) общими тестами EXTRA, обратные R125–R129 общим тестом REVERSE, журналы всех сценариев при inheritance_enabled = False против tests/baseline_pre16c.json (список BASELINES). Прежние проверки не менялись.
2026-10-27: задача 17 (триада): сценарии TR1–TR9 (twin/x17.py, фабрика twin/triad.py) общими тестами EXTRA, обратные R141–R144 общим тестом REVERSE; эталон не нужен (существующие прогоны не менялись). Прежние проверки не менялись.
2026-10-27: задача 19 (допрос): сценарии ID1–ID11 (twin/x19.py) общими тестами EXTRA, обратные R130–R135 общим тестом REVERSE, журналы всех сценариев при interrogation_enabled = False против tests/baseline_pre19.json (список BASELINES). В BUCKETS_OUT добавлено ведро held (пленные игрока): общие проверки сохранения людей считают и его. Прежние проверки не менялись.
2026-10-27: задача 10 (стенд сверки озвучки): сценарии LL1–LL9 (twin/x10.py, модуль twin/voice.py только читает мир) общими тестами EXTRA, обратные R136–R140 общим тестом REVERSE. Эталон не нужен. Прежние проверки не менялись.
2026-10-27: задача 22 (мир «всё включено»): сценарии IG1–IG7 (twin/x22.py, фабрика и таблица флагов twin/integration.py) общими тестами EXTRA, обратные R145–R149 общим тестом REVERSE; IG4 сверяется с уже существующим эталоном tests/baseline_pre19.json, новый эталон не нужен; IG6 сверяет reports/22-flag-table.md с заново построенной таблицей. Прежние проверки не менялись.
2026-10-28: задача 23a (журнал в два уровня; Стан: «исполняй 23», правка tests/test_acceptance.py и эталоны разрешены): сценарии LG1–LG5 (twin/x23a.py) общими тестами EXTRA, обратные R150–R152 общим тестом REVERSE, журналы всех сценариев при log_two_level_enabled = False против tests/baseline_pre23a.json (список BASELINES). Прежние проверки не менялись."""
import json
from pathlib import Path

import pytest

from twin.model import Faction
from twin.params import Params
from twin.scenarios import REVERSE, evaluate, run, ev10, ev11, EXTRA

SCENARIOS = ("DS1", "DS2", "DS4", "RG1", "RG2", "RG3", "RG4", "RG5", "OB1", "OB2", "RG6", "HD1", "HD2", "HD3", "IC1", "IC2", "IC3", "IC5", "RD1", "RD2", "RD3", "RD3S", "RD4", "RP1", "RP2", "RT1", "RT2", "RT2b", "RT3", "RT4", "RL1", "RL2", "RL3", "RL4a", "RL4b", "RL5", "RL6", "MK1", "MK2", "MK3", "MK4", "MK5", "MK6", "WR1", "WR2", "WR3", "WR4", "WR5", "WR6", "WR7a", "WR7b", "WR7c", "WR7d", "WS1", "WS2", "WS3", "WE1", "WE2", "WE3a", "WE3b", "WE3c", "WE3d", "WE3e", "RB1", "RB2", "RB3", "RB4", "RB5", "SW1", "SW2")
EV_SCENARIOS = ("EV1", "EV2", "EV3", "EV4", "EV5", "EV6", "EV7", "EV8", "EV9", "EV12", "EV13", "EV14", "EV15", "EV16", "EV17", "EV18", "EV19",
                "EV20", "EV21", "EV22", "EV23", "EV24", "EV25", "EV26", "EV26b", "EV26c", "EV27", "EV30", "EV31",
                "PL1", "PL2", "PL3", "PL4", "PL5", "PL6", "PL7", "PL8", "PL8b", "PL8c", "PL9", "PL10", "PL11",
                "CR1", "CR2", "CR3", "CR4", "CR5", "CR7", "CR7k", "CR8", "CR9")   # spec 21a, 21a-2, 21a-3, 21a-4, 21b, 21d, 21c; EV10, EV11 и CR6 — отдельные тесты


KNOWN_DEFECT = pytest.mark.xfail(
    strict=True,
    reason="Известный дефект, принят Станом 2026-10-25 (отчёт 01, №3): экономика 06 рассчитана на 5–10 чел., "
           "на тике 33 A (90 чел.) отбирает у B единственный объект, B без объектов вымирает; смены уклада (07) нет. Объекты, склад и регионы (03b) исход не меняют; закрывается 07 (смена уклада) или заявкой 05 (решения при голоде). "
           "Когда DS4 станет зелёным, strict=True уронит прогон — снять пометку.")


@pytest.mark.parametrize("sc", list(SCENARIOS) + list(EV_SCENARIOS))
def test_scenario_green(sc):
    ok, res, *_ = evaluate(sc)
    red = [f"{n}: {d}" for n, k, d in res if not k]
    assert ok, f"{sc} красный — " + "; ".join(red)


@pytest.mark.parametrize("key", sorted(REVERSE))
def test_reverse_check_turns_red(key):
    p, scs, desc = REVERSE[key]
    turned_red = [sc for sc in scs if not evaluate(sc, p)[0]]
    assert turned_red, f"{key} ({desc}) не валит ни один из {scs} — набор слабый"


@pytest.mark.parametrize("sc", list(SCENARIOS) + list(EV_SCENARIOS))
def test_deterministic(sc):
    w1, _ = run(sc)
    w2, _ = run(sc)
    assert w1.log == w2.log


@pytest.mark.parametrize("sc", list(SCENARIOS) + list(EV_SCENARIOS))
def test_people_conserved(sc):
    from twin.model import BUCKETS_OUT
    from twin.scenarios import build
    w0, _ = build(sc, Params())
    start = {n: f.manpower for n, f in w0.factions.items()}
    w, _ = run(sc)
    for n, f in w.factions.items():
        assert f.manpower + f.wounded + sum(getattr(f, b) for b in BUCKETS_OUT) == start[n] + f.absorbed, "люди появились или исчезли без следа (§1)"


OLD_SCENARIOS = ("DS1", "DS2", "DS4", "RG1", "RG2", "RG3", "RG4", "RG5", "OB1", "OB2", "RG6", "HD1", "HD2", "HD3", "IC1", "IC2", "IC3", "IC5", "RD1", "RD2", "RD3", "RD3S", "RD4", "RP1", "RP2")


@pytest.mark.parametrize("sc", OLD_SCENARIOS)
def test_tiers_off_matches_baseline(sc):
    """spec 04, флаг: с tiers_enabled = False журнал совпадает строка в строку с эталоном, снятым до 04."""
    import json
    from dataclasses import replace
    from pathlib import Path
    base = json.loads((Path(__file__).parent / "baseline_pre04.json").read_text(encoding="utf-8"))
    w, _ = run(sc, replace(Params(), tiers_enabled=False))
    assert [list(r) for r in w.log] == base[sc]


@pytest.mark.parametrize("sc", SCENARIOS)
def test_tiers_invariant(sc):
    """RT5: в каждый тик сумма ярусов = Manpower, ярусы раненых = раненые (проверка внутри run()), и в конце тоже."""
    w, _ = run(sc)
    for f in w.factions.values():
        assert f.rank + f.vet + f.off == f.manpower
        assert min(f.rank, f.vet, f.off) >= 0
        assert sum(sum(e[3]) for e in f.wounded_queue) == f.wounded


def test_gear_step_by_tier():
    """spec 04: ступень снаряжения яруса по TF_Armory: Good от 35/45/60, Worn от 10/15/25 (офицеры/ветераны/рядовые)."""
    from twin.model import Faction, World
    f = Faction("A", "Хищники", steady=3, ordinary=4, skittish=3, supply=0.0, armory=50.0)
    w = World({"A": f}, [], Params())
    assert [w.gear_step(f, t) for t in ("rank", "vet", "off")] == ["Worn", "Good", "Good"]
    f.armory = 12.0
    assert [w.gear_step(f, t) for t in ("rank", "vet", "off")] == ["Rags", "Rags", "Worn"]


@pytest.mark.parametrize("sc", [x for x in SCENARIOS if not x.startswith(("RL", "MK", "WR", "WS", "WE", "RB", "SW"))])
def test_relations_off_matches_baseline(sc):
    """spec 08a, флаг: с relations_enabled = False журнал совпадает строка в строку с эталоном, снятым до 08a."""
    import json
    from dataclasses import replace
    from pathlib import Path
    base = json.loads((Path(__file__).parent / "baseline_pre08a.json").read_text(encoding="utf-8"))
    w, _ = run(sc, replace(Params(), relations_enabled=False))
    assert [list(r) for r in w.log] == base[sc]


@pytest.mark.parametrize("sc", [x for x in SCENARIOS if not x.startswith(("RL", "WR", "WS", "WE", "RB", "SW"))])
def test_relations_read_only(sc):
    """spec 08a: при relations_enabled = True журнал без строк модуля 08 совпадает с журналом при False (модуль только читает)."""
    from dataclasses import replace
    off, _ = run(sc, replace(Params(), relations_enabled=False))
    on, _ = run(sc, replace(Params(), relations_enabled=True))
    assert [r for r in on.log if r[2] != "08"] == off.log


@pytest.mark.parametrize("sc", [x for x in SCENARIOS if not x.startswith(("MK", "WR", "WS", "WE", "RB", "SW"))])
def test_knowledge_off_matches_baseline(sc):
    """spec 08c, флаг: с knowledge_enabled = False журнал совпадает строка в строку с эталоном, снятым до 08c."""
    import json
    from dataclasses import replace
    from pathlib import Path
    base = json.loads((Path(__file__).parent / "baseline_pre08c.json").read_text(encoding="utf-8"))
    w, _ = run(sc, replace(Params(), knowledge_enabled=False))
    assert [list(r) for r in w.log] == base[sc]


@pytest.mark.parametrize("rel", [False, True])
@pytest.mark.parametrize("sc", [x for x in SCENARIOS if not x.startswith(("MK", "WR", "WS", "WE", "RB", "SW"))])
def test_knowledge_read_only(sc, rel):
    """spec 08c: при knowledge_enabled = True журнал без строк модуля 08c совпадает с журналом при False, при выключенных и включённых отношениях."""
    from dataclasses import replace
    off, _ = run(sc, replace(Params(), knowledge_enabled=False, relations_enabled=rel))
    on, _ = run(sc, replace(Params(), knowledge_enabled=True, relations_enabled=rel))
    assert [r for r in on.log if r[2] != "08c"] == off.log


@pytest.mark.parametrize("sc", [x for x in SCENARIOS if not x.startswith(("WR", "WS", "WE", "RB", "SW"))])
def test_wars_off_matches_baseline(sc):
    """spec 08b, флаг: с wars_enabled = False журнал совпадает строка в строку с эталоном, снятым до 08b."""
    import json
    from dataclasses import replace
    from pathlib import Path
    base = json.loads((Path(__file__).parent / "baseline_pre08b.json").read_text(encoding="utf-8"))
    w, _ = run(sc, replace(Params(), wars_enabled=False))
    assert [list(r) for r in w.log] == base[sc]


@pytest.mark.parametrize("sc", [x for x in SCENARIOS if not x.startswith(("WR", "WS", "WE", "RB", "SW"))])
def test_wars_read_only(sc):
    """WR8: при wars_enabled = True и war_cost = 0 журнал без строк модуля 08b совпадает с журналом при False (отношения и знание включены в обоих прогонах)."""
    from dataclasses import replace
    base = replace(Params(), relations_enabled=True, knowledge_enabled=True)
    off, _ = run(sc, replace(base, wars_enabled=False))
    on, _ = run(sc, replace(base, wars_enabled=True, war_cost=0.0))
    assert [r for r in on.log if r[2] != "08b"] == off.log


@pytest.mark.parametrize("sc", [x for x in SCENARIOS if not x.startswith(("WS", "WE", "RB", "SW"))])
def test_steers_off_matches_baseline(sc):
    """spec 08d, флаг: с war_steers_attacks = False журнал совпадает строка в строку с эталоном, снятым до 08d."""
    import json
    from dataclasses import replace
    from pathlib import Path
    base = json.loads((Path(__file__).parent / "baseline_pre08d.json").read_text(encoding="utf-8"))
    w, _ = run(sc, replace(Params(), war_steers_attacks=False))
    assert [list(r) for r in w.log] == base[sc]


@pytest.mark.parametrize("sc", [x for x in SCENARIOS if not x.startswith(("WE", "RB", "SW"))])
def test_war_economy_matches_baseline(sc):
    """spec 08e: журналы всех прежних сценариев совпадают с эталоном до 08e строка в строку: сценарии без войны (wars_enabled = False) и WR, WS со старыми числами 08b, закреплёнными в обстановке."""
    import json
    from dataclasses import replace
    from pathlib import Path
    base = json.loads((Path(__file__).parent / "baseline_pre08e.json").read_text(encoding="utf-8"))
    w, _ = run(sc) if sc.startswith(("WR", "WS")) else run(sc, replace(Params(), wars_enabled=False))
    assert [list(r) for r in w.log] == base[sc]


@pytest.mark.parametrize("sc", [x for x in SCENARIOS if not x.startswith(("RB", "SW"))])
def test_raid_discipline_off_matches_baseline(sc):
    """spec 20, флаг: с raid_discipline_enabled = False журнал совпадает строка в строку с эталоном, снятым до задачи 20 (WR, WS, WE идут со своими числами по умолчанию)."""
    import json
    from dataclasses import replace
    from pathlib import Path
    base = json.loads((Path(__file__).parent / "baseline_pre20.json").read_text(encoding="utf-8"))
    w, _ = run(sc) if sc.startswith(("WR", "WS", "WE")) else run(sc, replace(Params(), raid_discipline_enabled=False))
    assert [list(r) for r in w.log] == base[sc]


@pytest.mark.parametrize("sc", SCENARIOS)
def test_evolution_off_matches_baseline(sc):
    """spec 21a, флаг: с evolution_enabled = False (по умолчанию) журнал всех 70 прежних сценариев совпадает строка в строку с эталоном, снятым до 21a."""
    import json
    from pathlib import Path
    base = json.loads((Path(__file__).parent / "baseline_pre21a.json").read_text(encoding="utf-8"))
    w, _ = run(sc)
    assert [list(r) for r in w.log] == base[sc]


@pytest.mark.parametrize("sc", EV_SCENARIOS[:17])
def test_leader_off_matches_baseline(sc):
    """EV28 (spec 21b): с leader_enabled = False (по умолчанию) журналы EV1–EV19 совпадают строка в строку с эталоном, снятым до 21b."""
    import json
    from pathlib import Path
    base = json.loads((Path(__file__).parent / "baseline_pre21b.json").read_text(encoding="utf-8"))
    w, _ = run(sc)
    assert not w.p.leader_enabled
    assert [list(r) for r in w.log] == base[sc]


@pytest.mark.parametrize("sc", ("EV20", "EV21", "EV22", "EV23", "EV24", "EV25", "EV26", "EV26b", "EV26c", "EV27", "EV30", "EV31"))
def test_levers_off_matches_baseline(sc):
    """PL12 (spec 21d): с player_levers_enabled = False (по умолчанию) журналы EV20–EV31 совпадают строка в строку с эталоном, снятым до 21d; репутация при убийстве не меняется."""
    import json
    from pathlib import Path
    base = json.loads((Path(__file__).parent / "baseline_pre21d.json").read_text(encoding="utf-8"))
    w, _ = run(sc)
    assert not w.p.player_levers_enabled
    assert [list(r) for r in w.log] == base[sc]
    assert w.player_rep == {}


def test_levers_off_by_default_and_actions_raise():
    """PL12: выключатель по умолчанию False; действия bribe/tip/persuade без него — ошибка на тике действия."""
    from twin.scenarios import build
    assert Params().player_levers_enabled is False
    w, _ = build("EV20", Params())
    w.player_script = {1: [("bribe", "A", "A", 10.0)]}
    with pytest.raises(ValueError):
        w.step()


@pytest.mark.parametrize("sc", EV_SCENARIOS[:42])
def test_default_order_matches_baseline_21c(sc):
    """CR11 (spec 21c): при прежних порядках правил (без 4 и 9) журналы EV1–EV31 и PL1–PL11 совпадают строка в строку с эталоном, снятым до 21c."""
    import json
    from pathlib import Path
    base = json.loads((Path(__file__).parent / "baseline_pre21c.json").read_text(encoding="utf-8"))
    w, _ = run(sc)
    assert 4 not in w.p.evo_rule_order and 9 not in w.p.evo_rule_order   # правила 4 и 9 в прежних порядках не участвуют
    assert [list(r) for r in w.log] == base[sc]


def test_cr6_walk():
    """CR6 (spec 21c): обход стека (3, 4, 5, 6, 7, 8, 9) без мёртвых и затенённых правил; при порядке (8, 3, 4, 5, 6, 7, 9) затенение найдено."""
    from twin.scenarios import cr6
    ok, det = cr6()
    assert ok, det


def test_cr6_reverse_rule8_first():
    """CR6, обратная: если порядок по умолчанию в обходе заменить на (8, 3, 4, 5, 6, 7, 9) для проверяемого стека, CR6 краснеет."""
    from twin.scenarios import cr6
    p = Params(evo_rule_order=(8, 3, 4, 5, 6, 7, 9))
    from twin import evolution as evo
    assert evo.shadowed(p), "при правиле 8 первым затенение не найдено — проверка слабая"


def test_cr10_two_doctrine_factions_raise():
    """CR10 (spec 21c): две фракции с доктриной не равной 0 — ошибка на первом шаге."""
    from twin.scenarios import build
    w, _ = build("CR1", Params())
    w.factions["A"].doctrine = 1
    w.factions["B"] = Faction("B", "Хранители", supply=100.0, armory=50.0, steady=3, ordinary=4, skittish=3)
    w.factions["B"].doctrine = 2
    with pytest.raises(ValueError):
        w.step()


def test_leader_off_by_default():
    """spec 21b: вожак выключен по умолчанию, автономные убийства вожака выключены («заперт», как в enRAGE)."""
    p = Params()
    assert p.leader_enabled is False and p.leader_kill_seat is False and p.leader_kill_broken is False


def test_leader_requires_evolution():
    """spec 21b §1.6: leader_enabled без evolution_enabled — ошибка на первом тике."""
    from dataclasses import replace
    from twin.scenarios import build
    w, _ = build("DS1", replace(Params(), leader_enabled=True, evolution_enabled=False))
    with pytest.raises(ValueError):
        w.step()


def test_evolution_on_by_default():
    """spec 21a-2: смена уклада включена по умолчанию (решение Стана)."""
    assert Params().evolution_enabled is True


def test_ev10_walk():
    """EV10: обход стека без мёртвых и затенённых правил; при перестановке правила 8 наверх затенение 3, 5, 6, 7 найдено."""
    ok, det = ev10()
    assert ok, det


def test_ev10_reverse_r43():
    """R43: при порядке (8, 3, 5, 6, 7) EV10 краснеет."""
    p, _, _ = REVERSE["R43"]
    assert not ev10(p)[0]


def test_ev11_rule5_reachable():
    """EV11: по всем 70 прежним сценариям с evolution_enabled правило 5 сработало первым хотя бы раз, и при morale_hunger_k = 0 тоже."""
    ok, det, _ = ev11(SCENARIOS)
    assert ok, det


def test_raid_discipline_requires_knowledge():
    """RB6: raid_discipline_enabled без knowledge_enabled — ошибка на первом тике."""
    from dataclasses import replace
    from twin.scenarios import build
    w, _ = build("DS1", replace(Params(), raid_discipline_enabled=True, knowledge_enabled=False))
    with pytest.raises(ValueError):
        w.step()


def test_steers_requires_wars():
    """WS4: war_steers_attacks без wars_enabled — ошибка на первом тике."""
    from dataclasses import replace
    from twin.scenarios import build
    w, _ = build("DS1", replace(Params(), war_steers_attacks=True, wars_enabled=False))
    with pytest.raises(ValueError):
        w.step()


def test_wars_requirements():
    """WR9: wars_enabled без relations_enabled или (при war_needs_motive) без knowledge_enabled — ошибка на первом тике."""
    from dataclasses import replace
    from twin.scenarios import build
    for kw in (dict(relations_enabled=False), dict(knowledge_enabled=False)):
        w, _ = build("DS1", replace(Params(), **{"relations_enabled": True, "knowledge_enabled": True, "wars_enabled": True, **kw}))
        with pytest.raises(ValueError):
            w.step()


# ---------- задачи очереди (plans/QUEUE.md): общие тесты ----------
BASELINES = ("13a", "15", "14", "01n", "02", "03d", "18", "16a", "16b", "16c", "19", "23a")   # имена эталонов tests/baseline_pre<NN>.json, добавляются по мере исполнения задач


def _baseline_pairs():
    out = []
    for name in BASELINES:
        base = json.loads((Path(__file__).parent / f"baseline_pre{name}.json").read_text(encoding="utf-8"))
        out += [(name, sc) for sc in base]
    return out


_DEFAULT_LOGS = {}
_BASES = {}


@pytest.mark.parametrize("name,sc", _baseline_pairs())
def test_flags_off_matches_baseline(name, sc):
    """Все новые выключатели по умолчанию выключены: журнал каждого сценария совпадает строка в строку с эталоном, снятым до задачи <name>.
    Журнал прогона по умолчанию кэшируется в пределах сессии (ускорение, критерий тот же)."""
    if name not in _BASES:
        _BASES[name] = json.loads((Path(__file__).parent / f"baseline_pre{name}.json").read_text(encoding="utf-8"))
    if sc not in _DEFAULT_LOGS:
        w, _ = run(sc)
        _DEFAULT_LOGS[sc] = [list(r) for r in w.log]
    assert _DEFAULT_LOGS[sc] == _BASES[name][sc]


@pytest.mark.parametrize("sc", sorted(EXTRA))
def test_extra_green(sc):
    ok, res, *_ = evaluate(sc)
    red = [f"{n}: {d}" for n, k, d in res if not k]
    assert ok, f"{sc} красный — " + "; ".join(red)


@pytest.mark.parametrize("sc", sorted(EXTRA))
def test_extra_deterministic(sc):
    w1, _ = run(sc)
    w2, _ = run(sc)
    assert w1.log == w2.log


@pytest.mark.parametrize("layout", [1, 2, 3, 4, 5])
def test_bn4_wars_off_is_clean(layout):
    """BN4 (spec 08f): журнал режима «войны выкл» совпадает с журналом режима «войны вкл» без строк 08b при war_cost = 0, репарациях 0 и без управления нападениями."""
    from twin.bench import bn4
    assert bn4(layout)


def test_ry8_kill_options_require_flag():
    """RY8 (spec 02): kill с четвёртым элементом (маска, свидетели) без reputation_enabled — ValueError; reputation_enabled без player_levers_enabled — ValueError."""
    from dataclasses import replace
    from twin.scenarios import build
    w, _ = build("RY8", Params())
    w.player_script = {1: [("kill", "B", "B:офицер1", {"masked": True})]}
    with pytest.raises(ValueError):
        w.step()
    w, _ = build("RY8", Params())
    w.p = replace(w.p, reputation_enabled=True, player_levers_enabled=False)
    with pytest.raises(ValueError):
        w.step()


def test_ed9_frame_requires_flag():
    """ED9 (spec 03d): frame без envoys_enabled — ValueError; envoys_enabled без reputation_enabled — ValueError."""
    from dataclasses import replace
    from twin.scenarios import build
    w, _ = build("ED9", Params())
    w.player_script = {1: [("frame", "B", "C", {})]}
    with pytest.raises(ValueError):
        w.step()
    w, _ = build("ED9", Params())
    w.p = replace(w.p, envoys_enabled=True, reputation_enabled=False)
    with pytest.raises(ValueError):
        w.step()


def test_np9_threaten_requires_flag():
    """NP9 (spec 01): действие threaten без npc_state_enabled — ValueError на тике действия."""
    from twin.scenarios import build
    w, _ = build("NP9", Params())
    w.player_script = {1: [("threaten", "A", "A:вожак")]}
    with pytest.raises(ValueError):
        w.step()


def test_bn1_bench_report_runs():
    """BN1/BN5 (spec 08f): bench.py печатает отчёт по 5 раскладам × 2 режима со всеми строками; «войн: 0» не опускается."""
    import bench
    text = bench.report()
    assert text.count("расклад ") == 10
    for key in ("войн:", "концы:", "штурмов:", "потери людей по причинам:", "минимум запаса", "вымерли до конца:", "сводка по пяти раскладам"):
        assert key in text, key
