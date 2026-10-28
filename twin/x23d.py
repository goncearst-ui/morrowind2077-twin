"""Задача 23d: снимок состояния и эталонный мир (spec 23). Сценарии SN1–SN4, обратные R161–R162. Двойник; Creation Kit не описывает."""
import re
from dataclasses import replace
from pathlib import Path

from . import scenarios as S
from . import snapshot as SN
from . import refworld as R
from .params import Params

SNS = ("SN1", "SN2", "SN3", "SN4")
GOLDEN = Path(__file__).resolve().parent.parent / "tests" / "golden"


def build(sc):
    def f(p):
        if sc in ("SN1", "SN2", "SN4"):
            return R.ref_small(p), 100
        return R.ref_small(p), 1          # SN3: мир нужен только как носитель параметров; файлы генерирует сама проверка
    return f


def _run(w, n):
    for _ in range(n):
        w.step()


def _chk(sc):
    def f(w, series):
        res = []
        ok = lambda n, c, d: res.append((n, bool(c), d))
        p = w.p
        if sc == "SN1":
            a = SN.snapshot_write(w)
            b = SN.snapshot_write(SN.snapshot_read(a))
            ok("снимок на тике 100, прочитанный и записанный снова, байт в байт равен исходному",
               w.tick == 100 and a == b and len(a) > 10000, f"тик {w.tick}, байт {len(a.encode())} и {len(b.encode())}, строк {a.count(chr(10))}")
        elif sc == "SN2":
            clean = lambda x: SN.snapshot_write(x, bug={})            # сравнение чистой записью: дефект записи не должен прятать расхождение
            segs, good = [], True
            for t0, t1 in ((100, 500), (500, 1000)):                  # 100→500 по spec; 500→1000 добавлен: на тике 100 накопитель войны ещё пуст
                try:
                    w2 = SN.snapshot_read(SN.snapshot_write(w))
                except SN.SnapshotError as e:
                    segs.append(f"{t0}→{t1}: снимок не читается ({e})")
                    good = False
                    break
                n = len(w.log)
                _run(w, t1 - t0)
                _run(w2, t1 - t0)
                lo = t0 + 10                                          # сводный журнал: окно, начатое до снимка, у продолжения неполное
                sa = {k: v for k, v in w.log_sum.items() if k[0] >= lo and k[0] >= w.tick - (t1 - t0) + 10}
                sb = {k: v for k, v in w2.log_sum.items() if k[0] >= lo}
                same = w.tick == t1 and w2.tick == t1 and w.log[n:] == w2.log and sa == sb and clean(w) == clean(w2) and len(w2.log) > 0 and len(sb) > 100
                good = good and same
                segs.append(f"{t0}→{t1}: строк {len(w2.log)} и {len(w.log) - n}, окон сводного {len(sb)}, {'совпало' if same else 'РАСХОЖДЕНИЕ'}")
            ok("прогон от снимка на тике 100 до 500 (и на тике 500 до 1000): подробный журнал идентичен строкам непрерывного прогона, сводный — с окна после снимка, состояние на конце совпадает",
               good and len(segs) == 2, "; ".join(segs))
        elif sc == "SN3":
            first = R.generate(p)
            second = R.generate(p)
            same = first == second
            names = set(first) == set(R.FILES) and all(len(first[n]) > 1000 for n in first)
            golden = {n: (GOLDEN / n).read_text(encoding="utf-8") for n in R.FILES if (GOLDEN / n).exists()}
            man = GOLDEN / "MANIFEST.json"
            man_ok = man.exists() and man.read_text(encoding="utf-8") == R.manifest(first)
            same_golden = len(golden) == len(R.FILES) and all(golden[n] == first[n] for n in R.FILES)
            ok("снимки ref_small на тиках 0, 100, 500, 1000 и канонические CSV журналов созданы; повторная генерация даёт идентичные байты; файлы tests/golden/ совпадают с генерацией и манифест верен",
               same and names and same_golden and man_ok,
               f"повтор {same}, файлов {len(first)} из {len(R.FILES)}, золотых на диске {len(golden)}, совпали {same_golden}, манифест {man_ok}, "
               f"байт: {', '.join(f'{n}={len(first[n].encode())}' for n in R.FILES)}")
        elif sc == "SN4":
            a = SN.snapshot_write(w)
            bad = SN.exact_report(a)
            floats = a.count('{"f":')
            m = re.search(r'\{"f":"[^"]+"\}', a)
            probe = a.replace(m.group(0), "0.1", 1) if m else a              # чужая проверка: подставить число без точной записи
            caught = bool(m) and bool(SN.exact_report(probe))
            ok("в снимке нет чисел без точной записи (float.hex); проверка ловит число, записанное округлённым",
               not bad and floats > 500 and caught, f"чисел с точной записью {floats}, без неё {len(bad)} {bad[:2]}, проверка ловит подмену {caught}")
        return res
    return f


for _sc in SNS:
    S.EXTRA[_sc] = (build(_sc), _chk(_sc))

_ON = Params()
S.REVERSE_EXTRA.update({
    "R161": (replace(_ON, sn_bug_round=True), ("SN4",), "число с плавающей точкой пишется в снимок округлённым"),
    "R162": (replace(_ON, sn_bug_no_acc=True), ("SN2",), "снимок не содержит накопителей (war_acc)"),
})
