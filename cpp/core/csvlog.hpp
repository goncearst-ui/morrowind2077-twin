// SPDX-License-Identifier: GPL-3.0-or-later
// Двойник Morrowind 2077, C++-ядро. Журнал в CSV (twin/refworld.py: cell/uncell, csv.writer с lineterminator="\n").
// Строка заголовка — обычные строки; остальные строки — ячейки с типами: "n:", "b:0|1", "i:<целое>", "f:<hex>", "s:<текст>".
#pragma once
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace tf {

// Слой 1: поля как строки. Правила csv.writer (минимальное квотирование: поле в кавычках, если в нём , " \n \r;
// кавычка внутри удваивается; единственное пустое поле в строке пишется как ""). Строка кончается "\n".
std::string csv_write_row(const std::vector<std::string>& fields);
// Чтение текста в строки полей. Строки кончаются "\n" (конец текста без \n допускается). Пустая строка недопустима.
std::vector<std::vector<std::string>> csv_read(std::string_view text);

// Слой 2: ячейки с типами.
struct Cell {
  enum class K { Null, Bool, Int, Double, Str };
  K k = K::Null;
  bool b = false;
  int64_t i = 0;
  double d = 0.0;
  std::string s;
};
std::string cell_encode(const Cell& c);
Cell cell_decode(std::string_view text);  // нарушение формата даёт tf::Error

struct CsvLog {
  std::vector<std::string> header;
  std::vector<std::vector<Cell>> rows;
};
CsvLog csvlog_parse(std::string_view text);
std::string csvlog_dump(const CsvLog& log);

}  // namespace tf
