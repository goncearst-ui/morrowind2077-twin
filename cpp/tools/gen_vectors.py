#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Двойник Morrowind 2077, C++-ядро, ступень 25a. Генератор числовых векторов V0 (spec 25 §4).

Это инструмент теста, а не модель: правило «без случайности» относится к модели двойника. Сид фиксирован, в шапке каждого файла
записана версия Python. Векторы считает Python (эталон): C++ обязан совпасть построчно. Файлы коммитятся в cpp/tests/vectors/.

Запуск из корня репозитория: python3 cpp/tools/gen_vectors.py
Файлы (строки с # — комментарии):
  hex.txt     <биты double, 16 hex> <float.hex()>
  round.txt   <n> <биты x> <биты round(x, n)>                 (n = 4 и 6)
  idiv.txt    <a> <b> <a // b> <a % b>                        (int64, b != 0)
  strings.txt <hex UTF-8 строки или _> <hex json.dumps(s, ensure_ascii=False)>
  json.txt    <hex исходного JSON>\t<канонический JSON: sort_keys, ensure_ascii=False, без пробелов>
  csv.txt     <поля через пробел: hex или _ для пустого>\t<hex вывода csv.writer(lineterminator="\\n")>
  cells.txt   <вид n|b|i|f|s> <данные> <hex ячейки twin.refworld.cell>
"""
import csv
import io
import json
import math
import os
import platform
import random
import struct
import sys

SEED = 20261028
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "tests", "vectors")
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from twin.refworld import cell  # noqa: E402  (эталонное кодирование ячейки журнала)

rng = random.Random(SEED)
MAXI, MINI = 2**63 - 1, -(2**63)


def bits(x):
    return struct.unpack("<Q", struct.pack("<d", x))[0]


def frombits(b):
    return struct.unpack("<d", struct.pack("<Q", b))[0]


def hx(s):
    return s.encode("utf-8").hex() if s else "_"


def header(name):
    return f"# {name}: сгенерировано cpp/tools/gen_vectors.py, Python {platform.python_version()}, сид {SEED}. Не править руками.\n"


def write(name, lines):
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(header(name))
        for ln in lines:
            f.write(ln + "\n")
    print(f"{name}: {len(lines)} строк")


def finite_bits():
    while True:
        b = rng.getrandbits(64)
        if (b >> 52) & 0x7FF != 0x7FF:
            return b


def float_pool(n_rand=8000):
    xs = [0.0, -0.0, 1.0, -1.0, 0.1, 0.5, 1 / 3, 2 / 3, math.pi, math.e, 5e-324, -5e-324, 2.2250738585072014e-308,
          2.225073858507201e-308, 1.7976931348623157e308, -1.7976931348623157e308, 1e22, 1e23, 123456789.123456789,
          float(2**53), float(2**53 + 2), 3 * 2.0**-1074, 0.30000000000000004, 1e-7, 4503599627370496.5, math.inf, -math.inf]
    xs += [frombits(finite_bits()) for _ in range(n_rand)]
    xs += [frombits(rng.getrandbits(52) | (rng.getrandbits(1) << 63)) for _ in range(1500)]            # субнормальные и нули
    xs += [rng.uniform(0, 5000) for _ in range(3000)]                                                   # как числа мира
    xs += [rng.randrange(-10**6, 10**6) / 1000 for _ in range(2000)]
    xs += [rng.randrange(1, 10**5) / rng.randrange(1, 97) for _ in range(2000)]
    xs += [rng.uniform(-1, 1) * 10.0 ** rng.randrange(-20, 20) for _ in range(2000)]
    return xs


def gen_hex():
    write("hex.txt", [f"{bits(x):016x} {x.hex()}" for x in float_pool()])


def round_pool(n):
    xs = []
    step = 32 if n == 4 else 128                      # j/32 при n=4 и j/128 при n=6 — точные «ничьи» (x*10^n = целое + 1/2)
    for j in range(-1501, 1502, 2):
        xs.append(j / step)
    for j in range(1, 4000, 2):
        xs.append(j / step + rng.randrange(0, 50))
    xs += [math.nextafter(x, math.inf) for x in xs[:600]] + [math.nextafter(x, -math.inf) for x in xs[:600]]
    xs += [rng.randrange(-10**7, 10**7) / 10 ** (n + 1) for _ in range(2500)]                        # похожие на ничьи десятичные
    xs += [rng.randrange(1, 10**6) * 5 / 10 ** (n + 1) for _ in range(1500)]
    xs += [rng.uniform(-1e4, 1e4) for _ in range(1500)]
    xs += [rng.uniform(-1, 1) * 10.0 ** rng.randrange(-12, 3) for _ in range(1500)]                  # в том числе уходящие в -0.0
    xs += [frombits(finite_bits()) for _ in range(800)]
    xs += [10.0 ** k for k in range(-10, 308, 7)] + [-(10.0 ** k) for k in range(-10, 308, 11)]
    xs += [0.0, -0.0, 1e-9, -1e-9, 0.00005, 0.00015, 0.00025, 2.5, 0.5, 1.5, 1e15 + 0.5, 4503599627370495.5]
    return xs


def gen_round():
    lines = []
    for n in (4, 6):
        for x in round_pool(n):
            if math.isfinite(x):
                lines.append(f"{n} {bits(x):016x} {bits(round(x, n)):016x}")
    write("round.txt", lines)


def gen_idiv():
    edge = [0, 1, -1, 2, -2, 3, -3, 7, -7, 10, -10, 100, -100, 2**31, -(2**31), 2**32 + 1, MAXI, MAXI - 1, MINI, MINI + 1]
    lines = []
    for a in edge:
        for b in edge:
            if b != 0 and not (a == MINI and b == -1):
                lines.append(f"{a} {b} {a // b} {a % b}")
    for _ in range(8000):
        a = rng.getrandbits(rng.randrange(1, 64)) * rng.choice((1, -1))
        b = rng.getrandbits(rng.randrange(1, 64)) * rng.choice((1, -1))
        if b != 0:
            lines.append(f"{a} {b} {a // b} {a % b}")
    write("idiv.txt", lines)


POOL = (list("abcxyzAZ019 _-.:") + ['"', "\\", "/", "\n", "\r", "\t", "\b", "\f", "\x00", "\x01", "\x1f", "\x7f", ",", ";", "{", "}"]
        + list("Метрополия") + ["ё", "Ё", "é", "ß", "\u0080", "߿", "ࠀ", " ", " ", "﻿", "￿", "中", "文", "😀",
                                "\U00010000", "\U0010ffff"])


def rstr(maxlen=12):
    return "".join(rng.choice(POOL) for _ in range(rng.randrange(0, maxlen + 1)))


def gen_strings():
    lines = []
    allc = [chr(c) for c in range(0, 128)] + ["ё", "М", "中", "😀", " ", "﻿"]
    for ch in allc:
        s = json.dumps(ch, ensure_ascii=False)
        lines.append(f"{hx(ch)} {hx(s)}")
    for _ in range(3000):
        s = rstr()
        lines.append(f"{hx(s)} {hx(json.dumps(s, ensure_ascii=False))}")
    write("strings.txt", lines)


def rjson(depth=0):
    r = rng.random()
    if depth >= 4 or r < 0.45:
        return rng.choice([None, True, False, 0, 1, -1, MAXI, MINI, rng.randrange(-10**12, 10**12), rng.getrandbits(62),
                           rstr(), rstr(6), ""])
    if r < 0.7:
        return [rjson(depth + 1) for _ in range(rng.randrange(0, 5))]
    d = {}
    for _ in range(rng.randrange(0, 6)):
        d[rstr(5)] = rjson(depth + 1)
    return d


def gen_json():
    lines = []
    keys_sets = [{"schema": 1, "tick": 0, "logs": False}, {"v": [], "o": "Faction"}, {"d": 1, "t": 2, "s": 3, "f": 4, "o": 5},
                 {"ab": 1, "a": 2, "": 3, "b": 4, "ё": 5, "я": 6, "😀": 7, "￿": 8, "\U00010000": 9}]
    docs = [json.loads(json.dumps(k)) for k in keys_sets]
    for _ in range(2500):
        docs.append(rjson())
    for obj in docs:
        canon = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        src = rng.choice([
            lambda: json.dumps(obj, ensure_ascii=True),
            lambda: json.dumps(obj, ensure_ascii=False, indent="\t"),
            lambda: json.dumps(obj, ensure_ascii=True, indent=2),
            lambda: json.dumps(obj, ensure_ascii=False, separators=(",", ":")),
        ])()
        lines.append(f"{src.encode('utf-8').hex()}\t{canon}")
    write("json.txt", lines)


def gen_csv():
    lines = []
    rows = [[""], ["", ""], ["a"], ["a,b"], ['a"b'], ["a\nb", "c"], ["a\rb"], ["a\r\nb", ""], [" a ", "b "], ["\"", "\""], [",", ","],
            ["Метрополия.envoy", "ENVOY_INIT"], ["", "", ""], ['"""'], ["ё\n"]]
    for _ in range(3000):
        rows.append([rstr(8).replace("\x00", "") for _ in range(rng.randrange(1, 7))])
    for row in rows:
        o = io.StringIO()
        csv.writer(o, lineterminator="\n").writerow(row)
        lines.append(" ".join(hx(f) for f in row) + "\t" + hx(o.getvalue()))
    write("csv.txt", lines)


def gen_cells():
    lines = ["n - " + hx(cell(None)), "b 1 " + hx(cell(True)), "b 0 " + hx(cell(False))]
    for v in (0, 1, -1, 7, MAXI, MINI, 1000000, -1000000):
        lines.append(f"i {v} {hx(cell(v))}")
    for _ in range(300):
        v = rng.getrandbits(rng.randrange(1, 64)) * rng.choice((1, -1))
        lines.append(f"i {v} {hx(cell(v))}")
    pool = float_pool(300)
    for x in pool[:27] + rng.sample(pool[27:], 1500):
        lines.append(f"f {bits(x):016x} {hx(cell(x))}")
    for _ in range(300):
        s = rstr().replace("\x00", "")
        lines.append(f"s {hx(s)} {hx(cell(s))}")
    write("cells.txt", lines)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    gen_hex(); gen_round(); gen_idiv(); gen_strings(); gen_json(); gen_csv(); gen_cells()
