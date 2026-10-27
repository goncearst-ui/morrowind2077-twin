"""Хроника двойника: python3 chronicle.py <сценарий> [candidates] — печатает строки с типом и следом (spec 09)."""
import sys
from dataclasses import replace

from twin.chronicle import render, strength
from twin.scenarios import run

if len(sys.argv) < 2:
    sys.exit("использование: python3 chronicle.py <сценарий> [candidates]")
w, _ = run(sys.argv[1])
if "candidates" in sys.argv[2:]:
    w.p = replace(w.p, chronicle_candidates=True)
for r in render(w):
    print(f"[{r['type']}] {r['text']}\n      след: {r['trace']}")
print("крепость: " + ", ".join(f"{n} {strength(w, n):.0f}" for n in w.factions))
