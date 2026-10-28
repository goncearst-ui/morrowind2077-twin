// SPDX-License-Identifier: GPL-3.0-or-later
// Двойник Morrowind 2077, C++-ядро. V0: CSV (минимальное квотирование csv.writer) и ячейки журнала против векторов из Python.
#include <cstdlib>

#include "check.hpp"
#include "core/csvlog.hpp"
#include "core/error.hpp"
#include "core/num.hpp"

using namespace tf;

static bool bad(const std::string& t) {
  try {
    csv_read(t);
  } catch (const Error&) {
    return true;
  }
  return false;
}

int main() {
  for (const auto& ln : vector_lines("csv.txt")) {
    auto tab = ln.find('\t');
    std::vector<std::string> fields;
    for (const auto& h : split(ln.substr(0, tab), ' ')) fields.push_back(unhex(h));
    std::string want = unhex(ln.substr(tab + 1));
    CHECK_MSG(csv_write_row(fields) == want, "запись строки CSV не совпала: ожидалось %.50s", want.c_str());
    try {
      auto rows = csv_read(want);
      CHECK(rows.size() == 1 && rows[0] == fields);
    } catch (const Error& e) {
      CHECK_MSG(false, "чтение: %s", e.what());
    }
  }

  for (const auto& ln : vector_lines("cells.txt")) {
    auto p = split(ln, ' ');
    std::string want = unhex(p[2]);
    Cell c;
    switch (p[0][0]) {
      case 'n': break;
      case 'b': c.k = Cell::K::Bool; c.b = p[1] == "1"; break;
      case 'i': c.k = Cell::K::Int; c.i = std::strtoll(p[1].c_str(), nullptr, 10); break;
      case 'f': c.k = Cell::K::Double; c.d = from_bits(std::strtoull(p[1].c_str(), nullptr, 16)); break;
      default: c.k = Cell::K::Str; c.s = unhex(p[1]);
    }
    CHECK_MSG(cell_encode(c) == want, "кодирование ячейки %s", p[0].c_str());
    Cell back = cell_decode(want);
    CHECK_MSG(back.k == c.k && back.b == c.b && back.i == c.i && bits_of(back.d) == bits_of(c.d) && back.s == c.s, "разбор ячейки %s", want.c_str());
  }

  CHECK(bad("a,\"b\n"));
  CHECK(bad("a\rb\n"));
  CHECK(bad("a\"b,c\n"));
  CHECK(bad("\"a\"b,c\n"));
  CHECK(bad("a\n\nb\n"));
  CHECK(csv_read("a,b").size() == 1);               // без конечного перевода строки допускается
  CHECK(csv_read("").empty());
  auto r = csv_read("x,\"\"\n,\n");
  CHECK(r.size() == 2 && r[0].size() == 2 && r[0][1].empty() && r[1].size() == 2 && r[1][0].empty() && r[1][1].empty());

  auto cbad = [](const char* t) {
    try {
      cell_decode(t);
    } catch (const Error&) {
      return true;
    }
    return false;
  };
  CHECK(cbad("") && cbad("x") && cbad("q:1") && cbad("b:2") && cbad("i:1.5") && cbad("i:+5") && cbad("i:05") && cbad("i: 5") && cbad("i:") &&
        cbad("n:x") && cbad("f:1.5") && cbad("i:9223372036854775808"));
  return test_done("test_csv");
}
