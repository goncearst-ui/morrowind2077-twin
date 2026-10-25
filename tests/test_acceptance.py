"""Чек-лист приёмки: spec 00 §6 + spec 01 §2. Меняет только Стан (гейт protect-tests).
2026-10-25: пометка «ожидаемо красный» с DS4 снята по утверждённому plan 01, шаг 5; добавлен RG1.
2026-10-25: добавлены RG2–RG5 и обратная проверка R3 по утверждённому plan 03a, шаг 3. Пометка DS4 не менялась."""
import pytest

from twin.model import Faction
from twin.params import Params
from twin.scenarios import REVERSE, evaluate, run

SCENARIOS = ("DS1", "DS2", "DS4", "RG1", "RG2", "RG3", "RG4", "RG5")


KNOWN_DEFECT = pytest.mark.xfail(
    strict=True,
    reason="Известный дефект, принят Станом 2026-10-25 (отчёт 01, №3): экономика 06 рассчитана на 5–10 чел., "
           "на тике 33 A (90 чел.) отбирает у B единственный объект, B без объектов вымирает; смены уклада (07) нет. Закрывается intent 03b (больше объектов у фракции) и 07. Свой регион у каждой фракции сам по себе не помогает (проба 03b). "
           "Когда DS4 станет зелёным, strict=True уронит прогон — снять пометку.")


@pytest.mark.parametrize("sc", ["DS1", "DS2", pytest.param("DS4", marks=KNOWN_DEFECT), "RG1", "RG2", "RG3", "RG4", "RG5"])
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
    from twin.scenarios import build
    w0, _ = build(sc, Params())
    start = {n: f.manpower for n, f in w0.factions.items()}
    w, _ = run(sc)
    for n, f in w.factions.items():
        assert f.manpower + f.dead + f.deserted == start[n], "люди появились или исчезли без следа (§1)"
