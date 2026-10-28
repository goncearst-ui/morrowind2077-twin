// SPDX-License-Identifier: GPL-3.0-or-later
// Двойник Morrowind 2077, C++-ядро. Числа: точная запись double, round как в Python, целое деление вниз.
// Категории по spec 25 §6: поведение на g++/clang++ проверено векторами V0; MSVC и ARM64 не проверены (C).
#pragma once
#include <cstdint>
#include <string>
#include <string_view>

namespace tf {

uint64_t bits_of(double x);
double from_bits(uint64_t b);

// Python float.hex(): "0x1.8000000000000p+1", "0x0.0p+0", "-0x0.0p+0", субнормальные "0x0.<13 цифр>p-1022", "inf", "-inf", "nan".
std::string hexfloat(double x);
// Python float.fromhex() для записей, которые пишет hexfloat (допускается и короткая мантисса, как "0x1.8p+1"). Иначе tf::Error.
double parse_hexfloat(std::string_view s);

// Python round(x, n) для float: ближайшее double к десятичному значению, округлённому по ТОЧНОМУ двоичному значению x,
// «ничьи» к чётному. n от 0 до 22.
double py_round(double x, int n);

// Деление и остаток для int64 как в Python (вниз). Деление на ноль и INT64_MIN // -1 дают tf::Error.
int64_t py_floordiv(int64_t a, int64_t b);
int64_t py_mod(int64_t a, int64_t b);

// Сложение, вычитание, умножение int64 с проверкой переполнения (выход за int64 нарушает правила модели: tf::Error).
int64_t add_checked(int64_t a, int64_t b);
int64_t sub_checked(int64_t a, int64_t b);
int64_t mul_checked(int64_t a, int64_t b);

}  // namespace tf
