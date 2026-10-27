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
2026-10-27: добавлены EV19 и обратная R49 по утверждённому plan 21a-4 (решение Стана: Хищники без объектов не изгоняют людей, а продолжают контрабанду). Прежние проверки не менялись."""
import pytest

from twin.model import Faction
from twin.params import Params
from twin.scenarios import REVERSE, evaluate, run, ev10, ev11

SCENARIOS = ("DS1", "DS2", "DS4", "RG1", "RG2", "RG3", "RG4", "RG5", "OB1", "OB2", "RG6", "HD1", "HD2", "HD3", "IC1", "IC2", "IC3", "IC5", "RD1", "RD2", "RD3", "RD3S", "RD4", "RP1", "RP2", "RT1", "RT2", "RT2b", "RT3", "RT4", "RL1", "RL2", "RL3", "RL4a", "RL4b", "RL5", "RL6", "MK1", "MK2", "MK3", "MK4", "MK5", "MK6", "WR1", "WR2", "WR3", "WR4", "WR5", "WR6", "WR7a", "WR7b", "WR7c", "WR7d", "WS1", "WS2", "WS3", "WE1", "WE2", "WE3a", "WE3b", "WE3c", "WE3d", "WE3e", "RB1", "RB2", "RB3", "RB4", "RB5", "SW1", "SW2")
EV_SCENARIOS = ("EV1", "EV2", "EV3", "EV4", "EV5", "EV6", "EV7", "EV8", "EV9", "EV12", "EV13", "EV14", "EV15", "EV16", "EV17", "EV18", "EV19",
                "EV20", "EV21", "EV22", "EV23", "EV24", "EV25", "EV26", "EV26b", "EV26c", "EV27", "EV30", "EV31")   # spec 21a, 21a-2, 21a-3, 21a-4, 21b; EV10 и EV11 — отдельные тесты


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
