// SPDX-License-Identifier: GPL-3.0-or-later
// Двойник Morrowind 2077, C++-ядро. Числа (см. num.hpp).
#include "core/num.hpp"

#include <charconv>
#include <cmath>
#include <cstring>
#include <limits>

#include "core/error.hpp"

namespace tf {

uint64_t bits_of(double x) {
  uint64_t b;
  std::memcpy(&b, &x, sizeof b);
  return b;
}

double from_bits(uint64_t b) {
  double x;
  std::memcpy(&x, &b, sizeof x);
  return x;
}

std::string hexfloat(double x) {
  uint64_t b = bits_of(x);
  bool neg = (b >> 63) != 0;
  int e = static_cast<int>((b >> 52) & 0x7ff);
  uint64_t frac = b & ((uint64_t(1) << 52) - 1);
  if (e == 0x7ff) return frac != 0 ? "nan" : (neg ? "-inf" : "inf");
  std::string out = neg ? "-0x" : "0x";
  if (e == 0 && frac == 0) return out + "0.0p+0";
  out += (e == 0 ? "0." : "1.");
  static const char* digits = "0123456789abcdef";
  for (int sh = 48; sh >= 0; sh -= 4) {
    out += digits[(frac >> sh) & 15];
  }
#ifdef TF_BUG_HEX_SHORT  // R176: запись как у %a, без хвостовых нулей мантиссы
  while (out.back() == '0' && out[out.size() - 2] != '.') out.pop_back();
#endif
  int exp = (e == 0) ? -1022 : e - 1023;
  out += 'p';
  out += exp < 0 ? '-' : '+';
  out += std::to_string(exp < 0 ? -exp : exp);
  return out;
}

namespace {
int hexval(char c) {
  if (c >= '0' && c <= '9') return c - '0';
  if (c >= 'a' && c <= 'f') return c - 'a' + 10;
  if (c >= 'A' && c <= 'F') return c - 'A' + 10;
  return -1;
}
[[noreturn]] void bad_hex(std::string_view s) { throw Error("неверная hex-запись числа: " + std::string(s)); }
}  // namespace

double parse_hexfloat(std::string_view s) {
  std::string_view t = s;
  bool neg = false;
  if (!t.empty() && (t[0] == '-' || t[0] == '+')) {
    neg = t[0] == '-';
    t.remove_prefix(1);
  }
  if (t == "inf") return neg ? -std::numeric_limits<double>::infinity() : std::numeric_limits<double>::infinity();
  if (t == "nan") return std::numeric_limits<double>::quiet_NaN();
  if (t.size() < 3 || t[0] != '0' || (t[1] != 'x' && t[1] != 'X')) bad_hex(s);
  t.remove_prefix(2);
  uint64_t mant = 0;
  int exp2 = 0;
  size_t i = 0;
  size_t ndigits = 0;
  bool frac = false;
  for (; i < t.size(); ++i) {
    char c = t[i];
    if (c == '.') {
      if (frac) bad_hex(s);
      frac = true;
      continue;
    }
    int d = hexval(c);
    if (d < 0) break;
    ++ndigits;
    if ((mant >> 60) == 0) {
      mant = mant * 16 + static_cast<uint64_t>(d);
      if (frac) exp2 -= 4;
    } else {
      if (d != 0) bad_hex(s);  // не помещается в 64 бита: точное значение не гарантируется
      if (!frac) exp2 += 4;
    }
  }
  if (ndigits == 0) bad_hex(s);
  long pexp = 0;
  if (i < t.size()) {
    if (t[i] != 'p' && t[i] != 'P') bad_hex(s);
    ++i;
    bool eneg = false;
    if (i < t.size() && (t[i] == '+' || t[i] == '-')) eneg = t[i++] == '-';
    if (i >= t.size()) bad_hex(s);
    for (; i < t.size(); ++i) {
      if (t[i] < '0' || t[i] > '9') bad_hex(s);
      pexp = pexp * 10 + (t[i] - '0');
      if (pexp > 100000) bad_hex(s);
    }
    if (eneg) pexp = -pexp;
  }
  if (mant == 0) return neg ? -0.0 : 0.0;
  while (mant >= (uint64_t(1) << 53) && (mant & 1) == 0) {
    mant >>= 1;
    ++exp2;
  }
  if (mant >= (uint64_t(1) << 53)) bad_hex(s);
  double r = std::ldexp(static_cast<double>(mant), static_cast<int>(exp2 + pexp));
  if (std::isinf(r)) bad_hex(s);
  return neg ? -r : r;
}

double py_round(double x, int n) {
  if (n < 0 || n > 22) throw Error("py_round: число знаков вне 0..22");
  if (!std::isfinite(x)) return x;
#ifdef TF_BUG_ROUND_NAIVE
  double sc = std::pow(10.0, n);  // R177: округление через floor(x*10^n+0.5)/10^n
  return std::floor(x * sc + 0.5) / sc;
#else
  char buf[512];
  auto w = std::to_chars(buf, buf + sizeof buf, x, std::chars_format::fixed, n);
  if (w.ec != std::errc()) throw Error("py_round: to_chars не справился");
  double y = 0;
  auto r = std::from_chars(buf, w.ptr, y, std::chars_format::fixed);
  if (r.ec != std::errc() || r.ptr != w.ptr) throw Error("py_round: from_chars не справился");
  return y;
#endif
}

int64_t py_floordiv(int64_t a, int64_t b) {
  if (b == 0) throw Error("деление на ноль");
  if (a == std::numeric_limits<int64_t>::min() && b == -1) throw Error("переполнение int64 при делении");
  int64_t q = a / b;
#ifndef TF_BUG_IDIV_TRUNC  // R181: деление как в C (к нулю)
  if ((a % b != 0) && ((a < 0) != (b < 0))) --q;
#endif
  return q;
}

int64_t py_mod(int64_t a, int64_t b) {
  if (b == 0) throw Error("остаток от деления на ноль");
  if (b == -1) return 0;
  int64_t r = a % b;
#ifndef TF_BUG_IDIV_TRUNC
  if (r != 0 && ((r < 0) != (b < 0))) r += b;
#endif
  return r;
}

int64_t add_checked(int64_t a, int64_t b) {
  if ((b > 0 && a > std::numeric_limits<int64_t>::max() - b) || (b < 0 && a < std::numeric_limits<int64_t>::min() - b))
    throw Error("переполнение int64 при сложении");
  return a + b;
}

int64_t sub_checked(int64_t a, int64_t b) {
  if ((b < 0 && a > std::numeric_limits<int64_t>::max() + b) || (b > 0 && a < std::numeric_limits<int64_t>::min() + b))
    throw Error("переполнение int64 при вычитании");
  return a - b;
}

int64_t mul_checked(int64_t a, int64_t b) {
  if (a == 0 || b == 0) return 0;
  const int64_t mx = std::numeric_limits<int64_t>::max(), mn = std::numeric_limits<int64_t>::min();
  bool bad;
  if (a > 0) bad = b > 0 ? a > mx / b : b < mn / a;
  else bad = b > 0 ? a < mn / b : (a == -1 ? b == mn : b < mx / a);
  if (bad) throw Error("переполнение int64 при умножении");
  return a * b;
}

}  // namespace tf
