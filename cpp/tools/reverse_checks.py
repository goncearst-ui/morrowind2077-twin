#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Двойник Morrowind 2077, C++-ядро. Обратные проверки (как R-номера в двойнике): сборка с одним внесённым дефектом TF_BUG_<имя>
должна дать красный ctest. Без дефекта ctest должен быть зелёным (иначе проверка ничего не доказывает).

Запуск из корня репозитория: python3 cpp/tools/reverse_checks.py [компилятор ...]   (по умолчанию g++ и clang++)
Код возврата 0 — эталонная сборка зелёная и каждый дефект покраснел минимум в одном тесте.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CASES = [  # (номер, имя дефекта, что внесено)
    ("R176", "HEX_SHORT", "hex-запись сокращена, как %a"),
    ("R177", "ROUND_NAIVE", "round через floor(x*10^n+0.5)/10^n"),
    ("R178", "NO_KEYSORT", "ключи JSON-объектов не сортируются"),
    ("R179", "DICT_SORTED", "порядок словаря при чтении теряется"),
    ("R180", "CSV_NOQUOTE", "CSV без квотирования"),
    ("R181", "IDIV_TRUNC", "деление и остаток как в C (к нулю)"),
]


def run(cmd, **kw):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, **kw)


def build_and_test(cxx, bug, tmp):
    bdir = os.path.join(tmp, f"{cxx.replace('+', 'p')}-{bug or 'base'}")
    cfg = ["cmake", "-S", os.path.join(ROOT, "cpp"), "-B", bdir, "-DCMAKE_BUILD_TYPE=Release", f"-DCMAKE_CXX_COMPILER={cxx}", f"-DTF_BUG={bug}"]
    r = run(cfg)
    if r.returncode:
        raise SystemExit(r.stdout)
    r = run(["cmake", "--build", bdir, "-j", str(os.cpu_count() or 2)])
    if r.returncode:
        raise SystemExit(r.stdout)
    t = run(["ctest", "--test-dir", bdir])
    failed = re.findall(r"\d+ - (\w+) \(Failed\)", t.stdout)
    return t.returncode, failed


def main():
    compilers = sys.argv[1:] or ["g++", "clang++"]
    tmp = tempfile.mkdtemp(prefix="tf-rev-")
    bad = 0
    try:
        for cxx in compilers:
            if not shutil.which(cxx):
                print(f"{cxx}: не найден, пропущен")
                continue
            code, failed = build_and_test(cxx, "", tmp)
            print(f"{cxx}: эталонная сборка {'зелёная' if code == 0 else 'КРАСНАЯ ' + str(failed)}")
            bad += code != 0
            for rid, bug, what in CASES:
                code, failed = build_and_test(cxx, bug, tmp)
                ok = code != 0 and failed
                print(f"{cxx}: {rid} {what}: {'красный в ' + ', '.join(failed) if ok else 'НЕ ПОКРАСНЕЛ'}")
                bad += not ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
