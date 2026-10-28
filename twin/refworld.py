"""Задача 23d: уменьшенный эталонный мир для побитовой сверки будущего C++-ядра с двойником (spec 23 §1.23d).
Двойник; Creation Kit и SFSE не описывает.

ref_small: 4 фракции, 20 планет (по два объекта), 25 именных на фракцию (всего 100), 1000 тиков [решение Стана 2026-10-28].
Параметры мира подобраны перебором так, чтобы на 1000 тиках остались живы все четыре фракции и случились штурмы, налёты,
дезертирство, объявление войны и смена хозяина планеты (отчёт reports/23d-report.md). Вход «игрока» задан сценарием:
гибель двух вожаков и одного офицера (проверяет преемственность 21b и дугу 18).
"""
import csv
import hashlib
import io
import json
from dataclasses import replace

from . import integration as I
from .params import Params
from .planets import planet_world
from . import snapshot as SN

REF_TICKS = (0, 100, 500, 1000)
REF_HORIZON = 1000
REF_CFG = dict(n_planets=20, named=25, y1=56, y2=24, dos=16)    # [предл] подобрано перебором, см. отчёт 23d
REF_KILLS = {400: [("kill", "Метрополия", "Метрополия:вожак")],
             450: [("kill", "Колония", "Колония:офицер1")],
             600: [("kill", "Налётчики", "Налётчики:вожак")]}  # [предл] вход игрока вместо игрока
REF_FLAGS = ('raids_enabled', 'decisions_enabled', 'smuggling_enabled', 'fees_enabled', 'prisoner_sale_enabled', 'object_raids_enabled',
             'tiers_enabled', 'relations_enabled', 'knowledge_enabled', 'wars_enabled', 'raid_discipline_enabled', 'evolution_enabled',
             'leader_enabled', 'player_levers_enabled', 'region_share_enabled', 'planet_hegemon_enabled', 'npc_state_enabled',
             'reputation_enabled', 'envoys_enabled', 'arc_enabled', 'obj_enabled', 'strategy_enabled', 'inheritance_enabled',
             'interrogation_enabled')   # набор флагов на момент 23d; флаги будущих задач в мир не входят (иначе золотые файлы менялись бы сами)
FILES = tuple(f"ref_small_t{t:04d}.snap" for t in REF_TICKS) + ("ref_small_log_detail.csv", "ref_small_log_summary.csv")


def ref_small(p=None):
    """Мир ref_small: флаги из REF_FLAGS включены (набор мира 22 на момент 23d), несколько планет, журнал в два уровня."""
    p = p or Params()
    q = replace(p, log_two_level_enabled=True)
    w, _ = planet_world(q, off=tuple(f for f in I.flags() if f not in REF_FLAGS), **REF_CFG)
    w.player_script = {t: list(a) for t, a in REF_KILLS.items()}
    return w


# ---- канонический CSV журнала: каждая ячейка с типом, числа с плавающей точкой точно ----
def cell(v):
    if v is None:
        return "n:"
    if isinstance(v, bool):
        return "b:" + ("1" if v else "0")
    if isinstance(v, int):
        return f"i:{v}"
    if isinstance(v, float):
        return "f:" + v.hex()
    if isinstance(v, str):
        return "s:" + v
    raise TypeError(f"ячейка журнала не кодируется: {v!r}")


def uncell(c):
    t, v = c[0], c[2:]
    return {"n": lambda: None, "b": lambda: v == "1", "i": lambda: int(v), "f": lambda: float.fromhex(v), "s": lambda: v}[t]()


def _csv(header, rows):
    out = io.StringIO()
    wr = csv.writer(out, lineterminator="\n")
    wr.writerow(header)
    for r in rows:
        wr.writerow([cell(v) for v in r])
    return out.getvalue()


def detail_csv(w):
    return _csv(("tick", "phase", "module", "target", "old", "new", "reason"), w.log)


def summary_csv(w):
    rows = [(*k, *v) for k, v in w.log_sum.items()]          # порядок вставки: первая запись окна идёт первой
    return _csv(("window", "module", "target_class", "reason", "planet", "count", "sum_delta", "nonnumeric"), rows)


def generate(p=None, world=None):
    """Прогон ref_small на 1000 тиков; возвращает {имя файла: текст} (снимки на REF_TICKS, CSV журналов).
    Дефекты снимка (обратные проверки) берутся из флагов Params."""
    w = world if world is not None else ref_small(p)
    out = {}
    for t in range(REF_HORIZON + 1):
        if t in REF_TICKS:
            out[f"ref_small_t{t:04d}.snap"] = SN.snapshot_write(w)
        if t < REF_HORIZON:
            w.step()
    out["ref_small_log_detail.csv"] = detail_csv(w)
    out["ref_small_log_summary.csv"] = summary_csv(w)
    return out


def manifest(files):
    """Шапка золотых файлов: конфигурация и sha256 каждого файла."""
    return json.dumps({"schema": SN.SCHEMA, "horizon": REF_HORIZON, "ticks": list(REF_TICKS), "config": REF_CFG,
                       "player_script": {str(t): [list(a) for a in acts] for t, acts in REF_KILLS.items()},
                       "sha256": {n: hashlib.sha256(files[n].encode("utf-8")).hexdigest() for n in sorted(files)}},
                      ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def write_golden(path):
    """Записывает золотые файлы и MANIFEST.json в каталог path (python3 -m twin.refworld tests/golden). Только по разрешению Стана (tests/ меняет он)."""
    from pathlib import Path
    d = Path(path)
    d.mkdir(parents=True, exist_ok=True)
    files = generate()
    for n, text in files.items():
        with open(d / n, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
    with open(d / "MANIFEST.json", "w", encoding="utf-8", newline="") as fh:
        fh.write(manifest(files))
    return sorted(files)


if __name__ == "__main__":
    import sys
    print("\n".join(write_golden(sys.argv[1] if len(sys.argv) > 1 else "tests/golden")))
