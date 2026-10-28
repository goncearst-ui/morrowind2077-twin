// SPDX-License-Identifier: GPL-3.0-or-later
// Двойник Morrowind 2077, C++-ядро. V0: числа (hex-запись, round, деление вниз, проверка переполнения) против векторов из Python.
#include <cstdlib>
#include <limits>

#include "check.hpp"
#include "core/error.hpp"
#include "core/num.hpp"

using namespace tf;

static uint64_t hex64(const std::string& h) { return std::strtoull(h.c_str(), nullptr, 16); }

template <class F>
static bool throws(F f) {
  try {
    f();
  } catch (const Error&) {
    return true;
  }
  return false;
}

int main() {
  for (const auto& ln : vector_lines("hex.txt")) {
    auto p = split(ln, ' ');
    uint64_t b = hex64(p[0]);
    CHECK_MSG(hexfloat(from_bits(b)) == p[1], "hexfloat(%s) = %s, ожидалось %s", p[0].c_str(), hexfloat(from_bits(b)).c_str(), p[1].c_str());
    CHECK_MSG(bits_of(parse_hexfloat(p[1])) == b, "parse_hexfloat(%s)", p[1].c_str());
  }

  for (const auto& ln : vector_lines("round.txt")) {
    auto p = split(ln, ' ');
    int n = std::atoi(p[0].c_str());
    double x = from_bits(hex64(p[1]));
    uint64_t want = hex64(p[2]);
    uint64_t got = bits_of(py_round(x, n));
    CHECK_MSG(got == want, "round(%s, %d): получено %016llx, ожидалось %016llx", hexfloat(x).c_str(), n,
              static_cast<unsigned long long>(got), static_cast<unsigned long long>(want));
  }

  for (const auto& ln : vector_lines("idiv.txt")) {
    auto p = split(ln, ' ');
    int64_t a = std::strtoll(p[0].c_str(), nullptr, 10), b = std::strtoll(p[1].c_str(), nullptr, 10);
    int64_t q = std::strtoll(p[2].c_str(), nullptr, 10), r = std::strtoll(p[3].c_str(), nullptr, 10);
    CHECK_MSG(py_floordiv(a, b) == q, "%lld // %lld", static_cast<long long>(a), static_cast<long long>(b));
    CHECK_MSG(py_mod(a, b) == r, "%lld %% %lld", static_cast<long long>(a), static_cast<long long>(b));
  }

  // Явные случаи деления и границы int64.
  CHECK(py_floordiv(-7, 2) == -4 && py_mod(-7, 2) == 1);
  CHECK(py_floordiv(7, -2) == -4 && py_mod(7, -2) == -1);
  CHECK(py_floordiv(-8, 2) == -4 && py_mod(-8, 2) == 0);
  const int64_t mx = std::numeric_limits<int64_t>::max(), mn = std::numeric_limits<int64_t>::min();
  CHECK(throws([] { py_floordiv(1, 0); }));
  CHECK(throws([] { py_mod(1, 0); }));
  CHECK(throws([=] { py_floordiv(mn, -1); }));
  CHECK(py_mod(mn, -1) == 0);
  CHECK(throws([=] { add_checked(mx, 1); }) && add_checked(mx - 1, 1) == mx);
  CHECK(throws([=] { add_checked(mn, -1); }) && add_checked(mn + 1, -1) == mn);
  CHECK(throws([=] { sub_checked(mn, 1); }) && sub_checked(mn + 1, 1) == mn);
  CHECK(throws([=] { sub_checked(mx, -1); }) && sub_checked(mx - 1, -1) == mx);
  CHECK(throws([=] { mul_checked(mx, 2); }) && mul_checked(mx, 1) == mx && mul_checked(mn, 1) == mn);
  CHECK(throws([=] { mul_checked(mn, -1); }) && throws([=] { mul_checked(-1, mn); }));
  CHECK(mul_checked(3037000499LL, 3037000499LL) == 9223372030926249001LL && throws([] { mul_checked(3037000500LL, 3037000500LL); }));
  CHECK(mul_checked(-3037000499LL, 3037000499LL) == -9223372030926249001LL);

  // Разбор hex: короткая мантисса допускается, мусор — нет.
  CHECK(parse_hexfloat("0x1.8p+1") == 3.0);
  CHECK(parse_hexfloat("-0x1p-2") == -0.25);
  CHECK(bits_of(parse_hexfloat("-0x0.0p+0")) == bits_of(-0.0));
  CHECK(throws([] { parse_hexfloat(""); }));
  CHECK(throws([] { parse_hexfloat("1.5"); }));
  CHECK(throws([] { parse_hexfloat("0x"); }));
  CHECK(throws([] { parse_hexfloat("0x1.8q+1"); }));
  CHECK(throws([] { parse_hexfloat("0x1.8p"); }));
  CHECK(throws([] { parse_hexfloat("0x1p+2000"); }));
  CHECK(throws([] { parse_hexfloat("0x1.123456789abcdef1p+0"); }));  // больше 53 значащих бит

  CHECK(hexfloat(1.0) == "0x1.0000000000000p+0");   // не «0x1p+0» как у %a
  CHECK(hexfloat(3.0) == "0x1.8000000000000p+1");
  CHECK(py_round(2.5, 0) == 2.0 && py_round(0.03125, 4) == 0.0312 && py_round(0.09375, 4) == 0.0938);
  CHECK(throws([] { py_round(1.0, 23); }));
  return test_done("test_num");
}
