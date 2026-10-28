// SPDX-License-Identifier: GPL-3.0-or-later
// Двойник Morrowind 2077, C++-ядро. Файл снимка (формат 23d, schema 1; twin/snapshot.py): шапка и строки ["поле", значение].
// В 25a поля хранятся как универсальные значения, без типизации мира (она в 25b).
#pragma once
#include <cstdint>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "core/value.hpp"

namespace tf {

struct Snapshot {
  int64_t schema = 1;
  int64_t tick = 0;
  bool logs = false;
  std::vector<std::pair<std::string, Value>> fields;  // порядок строк файла
};

Snapshot snapshot_parse(std::string_view text);
std::string snapshot_dump(const Snapshot& s);

// SN4 (port exact_report): места, где {"f": s} записано не точной hex-записью, то есть hexfloat(parse(s)) != s.
// Каждое место — строка «путь: запись». Пустой список — все числа записаны точно.
std::vector<std::string> exact_report(std::string_view text);

// Файлы целиком, побайтово (без перевода строк).
std::string read_file(const std::string& path);
void write_file(const std::string& path, std::string_view data);

}  // namespace tf
