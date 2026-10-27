"""Задача 08f: расклады стенда как сценарии (проверки BN2, BN3 и честная сводка); BN4 и BN1 — отдельные тесты."""
from . import scenarios as S
from .bench import LAYOUTS, build_bench, people_conserved, summary

BN = tuple(f"BN{i}{m}" for i in LAYOUTS for m in ("on", "off"))


def build(sc):
    return lambda p: build_bench(int(sc[2]), sc.endswith("on"), p)


def _chk(sc):
    def f(w, series):
        res = []
        start = {n: s[0][1] for n, s in series.items()}
        res.append(("BN3: люди сохраняются", people_conserved(w, start), "сумма людей и вёдер сходится у всех фракций"))
        s = summary(w)
        res.append(("BN5: сводка честная: войны, нападения и вымершие выводятся даже при нуле", all(k in s for k in ("wars", "assaults", "raids", "extinct")), f"войн: {s['wars']}, штурмов {s['assaults']}, налётов {s['raids']}, вымерли {s['extinct']}"))
        return res
    return f


for _sc in BN:
    S.EXTRA[_sc] = (build(_sc), _chk(_sc))
