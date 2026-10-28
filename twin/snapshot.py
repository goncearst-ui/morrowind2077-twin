"""Задача 23d: снимок состояния World в каноническом виде (spec 23 §1.23d). Двойник; Creation Kit и SFSE не описывает.

Назначение: опорные файлы для побитовой сверки будущего C++-ядра с двойником и проверка «прогон от снимка = продолжение прогона».

Формат (текст UTF-8, строки через \\n, без пробелов внутри JSON):
  строка 1: шапка {"schema":1,"tick":T,"logs":false}
  далее по одной строке на поле мира: ["имя поля", значение]
Значение кодируется так (всё, что есть в состоянии, кроме журнала):
  null, true, false, целое, строка — как в JSON;
  число с плавающей точкой — {"f":"0x1.8p+1"} (float.hex(), точно, без потерь);
  список — JSON-массив;  кортеж — {"t":[...]};
  словарь — {"d":[[ключ,значение],...]} в порядке вставки (порядок обхода словаря в двойнике влияет на суммы, поэтому он часть состояния);
  множество — {"s":[...]}, элементы отсортированы по своей записи;
  запись (Site, Planet, Faction, Relation, Params) — {"o":"Имя","v":[["поле",значение],...]} в порядке полей, затем прочие атрибуты по алфавиту.
Журналы (World.log, World.log_sum) в снимок не входят: это выход, а не состояние (иначе снимок зависел бы от режима журнала).
Отложенные вызовы (World.scheduled) в снимок не входят и должны быть пусты: функцию в файл не записать.
"""
import json
from dataclasses import fields, is_dataclass

from .model import Faction, Planet, Relation, Site, World
from .params import Params

SCHEMA = 1
CLASSES = {c.__name__: c for c in (Site, Planet, Faction, Relation, Params)}
SKIP_WORLD = ("log", "log_sum", "scheduled")           # выход и вызовы; в состояние не входят
SKIP_EXTRA = ("ig_bad", "step")                         # служебное от integration.instrument (проверки), не состояние модели


class SnapshotError(ValueError):
    pass


def _dump(x):
    return json.dumps(x, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _hexf(x, round_bug):
    if round_bug:
        return round(x, 6)          # R168: число записано округлённым, без точной записи
    return {"f": float(x).hex()}


def enc(x, bug=None):
    """Состояние -> дерево из JSON-типов (см. шапку модуля)."""
    bug = bug or {}
    if x is None or isinstance(x, (bool, str)):
        return x
    if isinstance(x, int):
        return x
    if isinstance(x, float):
        return _hexf(x, bug.get("round"))
    if isinstance(x, list):
        return [enc(v, bug) for v in x]
    if isinstance(x, tuple):
        return {"t": [enc(v, bug) for v in x]}
    if isinstance(x, dict):
        return {"d": [[enc(k, bug), enc(v, bug)] for k, v in x.items()]}
    if isinstance(x, (set, frozenset)):
        items = sorted((enc(v, bug) for v in x), key=_dump)
        return {"s": items}
    if is_dataclass(x) and type(x).__name__ in CLASSES:
        return {"o": type(x).__name__, "v": [[n, enc(v, bug)] for n, v in _attrs(x)]}
    raise SnapshotError(f"тип {type(x).__name__} не записывается в снимок: {x!r}")


def _attrs(obj):
    """Поля записи в порядке объявления, затем прочие атрибуты (создаются на лету, напр. Faction._pub_*) по алфавиту."""
    names = [f.name for f in fields(obj)]
    extra = sorted(k for k in vars(obj) if k not in names and k not in SKIP_EXTRA)
    return [(n, getattr(obj, n)) for n in names + extra if n in vars(obj)]


def dec(x):
    """Обратное к enc."""
    if isinstance(x, list):
        return [dec(v) for v in x]
    if not isinstance(x, dict):
        return x
    if "f" in x:
        return float.fromhex(x["f"])
    if "t" in x:
        return tuple(dec(v) for v in x["t"])
    if "d" in x:
        return {_hashable(dec(k)): dec(v) for k, v in x["d"]}
    if "s" in x:
        return {_hashable(dec(v)) for v in x["s"]}
    if "o" in x:
        cls = CLASSES[x["o"]]
        obj = object.__new__(cls)                           # без __init__ и __post_init__: ничего не пересчитывается
        for n, v in x["v"]:
            object.__setattr__(obj, n, dec(v))
        return obj
    raise SnapshotError(f"неизвестная запись: {list(x)[:3]}")


def _hashable(v):
    return tuple(_hashable(i) for i in v) if isinstance(v, list) else v


def snapshot_write(w, bug=None):
    """Полный снимок мира как текст. bug — только для обратных проверок: {'round': True} | {'skip': ('war_acc',...)}."""
    if bug is None:                                         # обычный вызов: дефекты берутся из флагов мира (только для обратных проверок); bug={} — чистая запись
        bug = {"round": w.p.sn_bug_round, "skip": ("war_acc",) if w.p.sn_bug_no_acc else ()}
    if w.scheduled:
        raise SnapshotError("в мире есть отложенные вызовы (World.scheduled): функцию в снимок не записать")
    skip = set(SKIP_WORLD) | set(bug.get("skip", ()))
    head = {"schema": SCHEMA, "tick": w.tick, "logs": False}
    lines = [_dump(head)]
    for n, v in _attrs(w):
        if n in skip:
            continue
        lines.append(_dump([n, enc(v, bug)]))
    return "\n".join(lines) + "\n"


def snapshot_read(text):
    """Текст -> новый World (без журнала). Отложенных вызовов нет."""
    rows = text.split("\n")
    if rows and rows[-1] == "":
        rows.pop()
    head = json.loads(rows[0])
    if head.get("schema") != SCHEMA:
        raise SnapshotError(f"схема {head.get('schema')} не поддерживается (ожидалась {SCHEMA})")
    w = object.__new__(World)
    object.__setattr__(w, "log", [])
    object.__setattr__(w, "log_sum", {})
    object.__setattr__(w, "scheduled", {})
    for row in rows[1:]:
        n, v = json.loads(row)
        object.__setattr__(w, n, dec(v))
    missing = [f.name for f in fields(World) if f.name not in vars(w)]
    if missing:
        raise SnapshotError(f"в снимке нет полей мира: {missing}")
    return w


def exact_report(text):
    """SN4: список мест, где число записано без точной записи (вещественное число JSON или {"f":..} с потерей при обратном чтении)."""
    bad = []

    def walk(x, path):
        if isinstance(x, float):
            bad.append((path, x))
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, f"{path}[{i}]")
        elif isinstance(x, dict):
            if "f" in x and len(x) == 1:
                s = x["f"]
                try:
                    if float.fromhex(s).hex() != s:
                        bad.append((path, s))
                except ValueError:
                    bad.append((path, s))
            else:
                for k, v in x.items():
                    walk(v, f"{path}.{k}")

    for row in text.split("\n")[1:]:
        if row:
            n, v = json.loads(row)
            walk(v, n)
    return bad
