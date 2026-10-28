"""Задача 23e: простая сумма вместо встроенной (spec 23e). Сценарии SM1–SM3, обратные R163–R164. Двойник; Creation Kit не описывает."""
import ast
import hashlib
from dataclasses import replace
from pathlib import Path

from . import scenarios as S
from .arith import fsum
from .params import Params

SMS = ("SM1", "SM2", "SM3")
TWIN = Path(__file__).resolve().parent
ROOT = TWIN.parent
EXCLUDE = ("scenarios.py", "extra.py", "integration.py", "bench.py", "chronicle.py", "arith.py")    # проверочный код и стенды: мир не считают; arith.py содержит саму fsum и хук обратной проверки R163


def model_modules():
    """Модули, считающие состояние мира: twin/*.py без проверочных x*.py, сценариев и стендов."""
    return sorted(f for f in TWIN.glob("*.py") if not f.name.startswith("x") and f.name not in EXCLUDE)


def builtin_sum_calls(src, name="<src>"):
    tree = ast.parse(src)
    return [(name, n.lineno) for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "sum"]


def build(sc):
    return lambda p: (S.build("DS1", p)[0], 1)


def _chk(sc):
    def f(w, series):
        res = []
        ok = lambda n, c, d: res.append((n, bool(c), d))
        p = w.p
        if sc == "SM1":
            found = []
            for f_ in model_modules():
                found += builtin_sum_calls(f_.read_text(encoding="utf-8"), f_.name)
            if p.sm_bug_leftover:
                found += builtin_sum_calls("x = sum(a)\n", "<вставка R164>")
            ok("в модельных модулях нет вызова встроенной sum (разбор исходников)", not found and len(model_modules()) > 10,
               f"модулей {len(model_modules())}, найдено вызовов {len(found)}: {found[:3]}")
        elif sc == "SM2":
            a = fsum([0.1] * 10, _bug=p.sm_bug_builtin_sum)
            b = fsum([1, 2, 3], _bug=p.sm_bug_builtin_sum)
            ok("fsum([0.1]*10) = 0.9999999999999999 (встроенная даёт 1.0); fsum([1, 2, 3]) = 6 целое",
               a == 0.9999999999999999 and b == 6 and isinstance(b, int), f"{a!r} и {b!r}; встроенная sum даёт {sum([0.1] * 10)!r}")
        elif sc == "SM3":
            man = (ROOT / "tests" / "golden" / "MANIFEST.json")
            from . import refworld as R
            files = R.generate(p)
            ok("золотые файлы и MANIFEST.json tests/golden/ совпадают с заново сгенерированными (замена суммы ничего не изменила)",
               man.exists() and man.read_text(encoding="utf-8") == R.manifest(files) and all((ROOT / "tests" / "golden" / n).read_text(encoding="utf-8") == files[n] for n in R.FILES),
               f"файлов {len(files)}, sha256 манифеста {hashlib.sha256(man.read_bytes()).hexdigest()[:12]}")
        return res
    return f


for _sc in SMS:
    S.EXTRA[_sc] = (build(_sc), _chk(_sc))

_ON = Params()
S.REVERSE_EXTRA.update({
    "R163": (replace(_ON, sm_bug_builtin_sum=True), ("SM2",), "fsum зовёт встроенную сумму"),
    "R164": (replace(_ON, sm_bug_leftover=True), ("SM1",), "в разбираемых исходниках остался вызов встроенной суммы"),
})
