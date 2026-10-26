"""Чек-лист приёмки: spec 00 §6 + spec 01 §2. Меняет только Стан (гейт protect-tests).
2026-10-25: пометка «ожидаемо красный» с DS4 снята по утверждённому plan 01, шаг 5; добавлен RG1.
2026-10-25: добавлены RG2–RG5 и обратная проверка R3 по утверждённому plan 03a, шаг 3. Пометка DS4 не менялась.
2026-10-25: добавлены OB1, RG6 и обратная проверка R4 по утверждённому plan 03b, шаг 4. OB2 добавлен после решения Стана смягчить критерий с 20 до 10 тиков (отчёт 03b).
2026-10-26: добавлены RD1–RD4 (RD3S — вариант RD3 с обороной Хищников), R9, R10; счёт людей включает раненых, захваченных и принятых — по утверждённому plan 03c, шаги 3 и 6.
2026-10-25: добавлены IC1, IC2, IC3, IC5, R7, R8 по утверждённому plan 06, шаг 5; пометка «известный дефект» с DS4 снята — DS4 стал зелёным (см. отчёт 06; указание в самой пометке).
2026-10-25: добавлены HD1–HD3, R5, R6; критерий RG4 переписан (люди ≥ 95, мораль < 55); счёт людей включает изгнанных — по утверждённому plan 05, шаг 5 (решение Стана: порог морали 55, RG4 вариант а).
2026-10-26: добавлены RP1, RP2 и обратная проверка R11 по утверждённому plan 07, шаг 3 (решения Стана: границы RP1 5–10; налёт на регион без потерь)."""
import pytest

from twin.model import Faction
from twin.params import Params
from twin.scenarios import REVERSE, evaluate, run

SCENARIOS = ("DS1", "DS2", "DS4", "RG1", "RG2", "RG3", "RG4", "RG5", "OB1", "OB2", "RG6", "HD1", "HD2", "HD3", "IC1", "IC2", "IC3", "IC5", "RD1", "RD2", "RD3", "RD3S", "RD4", "RP1", "RP2")


KNOWN_DEFECT = pytest.mark.xfail(
    strict=True,
    reason="Известный дефект, принят Станом 2026-10-25 (отчёт 01, №3): экономика 06 рассчитана на 5–10 чел., "
           "на тике 33 A (90 чел.) отбирает у B единственный объект, B без объектов вымирает; смены уклада (07) нет. Объекты, склад и регионы (03b) исход не меняют; закрывается 07 (смена уклада) или заявкой 05 (решения при голоде). "
           "Когда DS4 станет зелёным, strict=True уронит прогон — снять пометку.")


@pytest.mark.parametrize("sc", ["DS1", "DS2", "DS4", "RG1", "RG2", "RG3", "RG4", "RG5", "OB1", "OB2", "RG6", "HD1", "HD2", "HD3", "IC1", "IC2", "IC3", "IC5", "RD1", "RD2", "RD3", "RD3S", "RD4", "RP1", "RP2"])
def test_scenario_green(sc):
    ok, res, *_ = evaluate(sc)
    red = [f"{n}: {d}" for n, k, d in res if not k]
    assert ok, f"{sc} красный — " + "; ".join(red)


@pytest.mark.parametrize("key", sorted(REVERSE))
def test_reverse_check_turns_red(key):
    p, scs, desc = REVERSE[key]
    turned_red = [sc for sc in scs if not evaluate(sc, p)[0]]
    assert turned_red, f"{key} ({desc}) не валит ни один из {scs} — набор слабый"


@pytest.mark.parametrize("sc", SCENARIOS)
def test_deterministic(sc):
    w1, _ = run(sc)
    w2, _ = run(sc)
    assert w1.log == w2.log


@pytest.mark.parametrize("sc", SCENARIOS)
def test_people_conserved(sc):
    from twin.model import BUCKETS_OUT
    from twin.scenarios import build
    w0, _ = build(sc, Params())
    start = {n: f.manpower for n, f in w0.factions.items()}
    w, _ = run(sc)
    for n, f in w.factions.items():
        assert f.manpower + f.wounded + sum(getattr(f, b) for b in BUCKETS_OUT) == start[n] + f.absorbed, "люди появились или исчезли без следа (§1)"
