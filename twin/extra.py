"""Регистрация сценариев задач 13a и далее: каждая задача — свой модуль twin/x<имя>.py (см. plans/QUEUE.md)."""
from dataclasses import replace

from .model import Site, World
from .params import Params


def clean(p: Params, **kw) -> Params:
    """Чистая обстановка (как PL_SIMPLE): налёты, контрабанда, поборы, решения при голоде и штрафы выключены."""
    return replace(p, evolution_enabled=False, hunger_threshold=0.0, underpay_morale=0.0, raids_enabled=False,
                   object_raids_enabled=False, smuggling_enabled=False, fees_enabled=False, prisoner_sale_enabled=False,
                   decisions_enabled=False, archetype_assault_threshold={}, **kw)


def rows(w, target, reason=None):
    return [r for r in w.log if r[3] == target and (reason is None or r[6] == reason)]


from . import x13a, x15, x14, x08f, x01, x02, x03d, x18, x09, x16a, x16b, x16c, x17, x19, x10, x22, x23a, x23b  # noqa: E402,F401
