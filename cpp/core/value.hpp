// SPDX-License-Identifier: GPL-3.0-or-later
// Двойник Morrowind 2077, C++-ядро. Дерево значений состояния мира (то, что в двойнике кодирует twin/snapshot.py enc/dec).
// null, bool, целое int64, double, строка, список, кортеж, словарь (порядок вставки хранится явно), множество, запись (имя + поля по порядку).
#pragma once
#include <cstdint>
#include <string>
#include <utility>
#include <vector>

#include "core/json.hpp"

namespace tf {

struct Value {
  enum class K { Null, Bool, Int, Double, Str, List, Tuple, Dict, Set, Record };
  K k = K::Null;
  bool b = false;
  int64_t i = 0;
  double d = 0.0;
  std::string s;                 // Str; для Record — имя записи
  std::vector<Value> items;      // List, Tuple, Set; для Dict — ключи
  std::vector<Value> vals;       // Dict — значения (vals[n] парно items[n]); Record — значения полей
  std::vector<std::string> names;  // Record — имена полей

  static Value null() { return Value(); }
  static Value boolean(bool v) { Value x; x.k = K::Bool; x.b = v; return x; }
  static Value integer(int64_t v) { Value x; x.k = K::Int; x.i = v; return x; }
  static Value real(double v) { Value x; x.k = K::Double; x.d = v; return x; }
  static Value str(std::string v) { Value x; x.k = K::Str; x.s = std::move(v); return x; }
  static Value list() { Value x; x.k = K::List; return x; }
  static Value tuple() { Value x; x.k = K::Tuple; return x; }
  static Value dict() { Value x; x.k = K::Dict; return x; }
  static Value set() { Value x; x.k = K::Set; return x; }
  static Value record(std::string name) { Value x; x.k = K::Record; x.s = std::move(name); return x; }
};

// Состояние -> дерево JSON (форма snapshot.py: {"f":...}, {"t":...}, {"d":...}, {"s":...}, {"o":...,"v":...}).
Json enc(const Value& v);
// Обратное. Неизвестная форма даёт tf::Error.
Value dec(const Json& j);

// Точное равенство (типы различаются: 1 и 1.0 — разные; double сравнивается по битам; словарь — с учётом порядка).
bool value_equal(const Value& a, const Value& b);

}  // namespace tf
