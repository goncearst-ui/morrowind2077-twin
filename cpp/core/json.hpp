// SPDX-License-Identifier: GPL-3.0-or-later
// Двойник Morrowind 2077, C++-ядро. JSON-подмножество снимка: null, true/false, целые int64, строки, массивы, объекты.
// Дробные числа в JSON не допускаются (в снимке они пишутся как {"f":"0x..."}). Целые вне int64 не допускаются.
// Писатель = Python json.dumps(x, ensure_ascii=False, separators=(",", ":"), sort_keys=True).
#pragma once
#include <cstdint>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace tf {

struct Json {
  enum class K { Null, Bool, Int, Str, Arr, Obj };
  K k = K::Null;
  bool b = false;
  int64_t i = 0;
  std::string s;
  std::vector<Json> a;
  std::vector<std::string> okeys;  // объект: ключи в порядке источника; писатель сортирует по байтам UTF-8
  std::vector<Json> ovals;         // значения, ovals[n] парно okeys[n]

  static Json null() { return Json(); }
  static Json boolean(bool v) { Json j; j.k = K::Bool; j.b = v; return j; }
  static Json integer(int64_t v) { Json j; j.k = K::Int; j.i = v; return j; }
  static Json str(std::string v) { Json j; j.k = K::Str; j.s = std::move(v); return j; }
  static Json arr() { Json j; j.k = K::Arr; return j; }
  static Json obj() { Json j; j.k = K::Obj; return j; }

  const Json* get(std::string_view key) const;  // для объекта; nullptr, если ключа нет
  void put(std::string key, Json v) { okeys.push_back(std::move(key)); ovals.push_back(std::move(v)); }
  size_t osize() const { return okeys.size(); }
};

// Разбор одного значения; пробелы по краям допускаются. Нарушение формата даёт tf::Error.
Json json_parse(std::string_view text);
// Канонический вид (см. шапку).
std::string json_dump(const Json& j);
// Экранирование строки как json.dumps(ensure_ascii=False), с кавычками.
void json_append_string(std::string& out, std::string_view s);
bool utf8_valid(std::string_view s);

}  // namespace tf
