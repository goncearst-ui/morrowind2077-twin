"""Задача 23e: простая сумма слева направо (spec 23e). Встроенная sum() Python 3.12+ суммирует дробные с компенсацией;
C++ при обычном сложении дал бы другой последний бит, поэтому модельные модули суммируют так. Двойник; Creation Kit не описывает."""


def fsum(iterable, start=0, _bug=False):
    if _bug:
        return sum(iterable, start)        # R163: встроенная сумма вместо простого цикла
    t = start
    for x in iterable:
        t = t + x
    return t
