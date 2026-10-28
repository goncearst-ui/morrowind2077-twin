// SPDX-License-Identifier: GPL-3.0-or-later
// Двойник Morrowind 2077, C++-ядро. CSV журнала (см. csvlog.hpp).
#include "core/csvlog.hpp"

#include <limits>

#include "core/error.hpp"
#include "core/json.hpp"
#include "core/num.hpp"

namespace tf {

std::string csv_write_row(const std::vector<std::string>& fields) {
  std::string out;
  for (size_t n = 0; n < fields.size(); ++n) {
    if (n) out += ',';
    const std::string& f = fields[n];
    bool q = f.empty() && fields.size() == 1;
    for (char c : f)
      if (c == ',' || c == '"' || c == '\n' || c == '\r') q = true;
#ifdef TF_BUG_CSV_NOQUOTE  // R180: CSV без квотирования
    q = false;
#endif
    if (!q) {
      out += f;
      continue;
    }
    out += '"';
    for (char c : f) {
      if (c == '"') out += '"';
      out += c;
    }
    out += '"';
  }
  out += '\n';
  return out;
}

std::vector<std::vector<std::string>> csv_read(std::string_view t) {
  if (!utf8_valid(t)) throw Error("CSV: недопустимый UTF-8");
  std::vector<std::vector<std::string>> rows;
  std::vector<std::string> row;
  std::string field;
  enum { Start, Plain, Quoted, QuoteSeen } st = Start;
  bool row_open = false;
  auto end_field = [&] {
    row.push_back(std::move(field));
    field.clear();
  };
  auto end_row = [&] {
    end_field();
    rows.push_back(std::move(row));
    row.clear();
    row_open = false;
    st = Start;
  };
  for (size_t p = 0; p < t.size(); ++p) {
    char c = t[p];
    row_open = true;
    switch (st) {
      case Start:
        if (c == '"') st = Quoted;
        else if (c == ',') end_field();
        else if (c == '\n') {
          if (row.empty() && field.empty()) throw Error("CSV: пустая строка на байте " + std::to_string(p));
          end_row();
        } else if (c == '\r') throw Error("CSV: \\r вне кавычек на байте " + std::to_string(p));
        else { field += c; st = Plain; }
        break;
      case Plain:
        if (c == ',') { end_field(); st = Start; }
        else if (c == '\n') end_row();
        else if (c == '\r') throw Error("CSV: \\r вне кавычек на байте " + std::to_string(p));
        else if (c == '"') throw Error("CSV: кавычка внутри обычного поля на байте " + std::to_string(p));
        else field += c;
        break;
      case Quoted:
        if (c == '"') st = QuoteSeen;
        else field += c;
        break;
      case QuoteSeen:
        if (c == '"') { field += '"'; st = Quoted; }
        else if (c == ',') { end_field(); st = Start; }
        else if (c == '\n') end_row();
        else throw Error("CSV: символ после закрывающей кавычки на байте " + std::to_string(p));
        break;
    }
  }
  if (st == Quoted) throw Error("CSV: кавычка не закрыта");
  if (row_open) end_row();
  return rows;
}

std::string cell_encode(const Cell& c) {
  switch (c.k) {
    case Cell::K::Null: return "n:";
    case Cell::K::Bool: return c.b ? "b:1" : "b:0";
    case Cell::K::Int: return "i:" + std::to_string(c.i);
    case Cell::K::Double: return "f:" + hexfloat(c.d);
    case Cell::K::Str: return "s:" + c.s;
  }
  throw Error("cell_encode: неизвестный вид");
}

Cell cell_decode(std::string_view t) {
  if (t.size() < 2 || t[1] != ':') throw Error("ячейка без типа: " + std::string(t));
  std::string_view v = t.substr(2);
  Cell c;
  switch (t[0]) {
    case 'n':
      if (!v.empty()) throw Error("n: с данными");
      return c;
    case 'b':
      if (v != "0" && v != "1") throw Error("b: ждёт 0 или 1");
      c.k = Cell::K::Bool;
      c.b = v == "1";
      return c;
    case 'i': {
      if (v.empty() || v.back() < '0' || v.back() > '9' || (v.front() != '-' && (v.front() < '0' || v.front() > '9')))
        throw Error("i: ждёт целое без пробелов");
      Json j = json_parse(v);  // та же грамматика целого: без плюса, без ведущих нулей, int64
      if (j.k != Json::K::Int) throw Error("i: ждёт целое");
      c.k = Cell::K::Int;
      c.i = j.i;
      return c;
    }
    case 'f':
      c.k = Cell::K::Double;
      c.d = parse_hexfloat(v);
      return c;
    case 's':
      c.k = Cell::K::Str;
      c.s = std::string(v);
      return c;
    default: throw Error("неизвестный тип ячейки: " + std::string(t));
  }
}

CsvLog csvlog_parse(std::string_view text) {
  auto rows = csv_read(text);
  if (rows.empty()) throw Error("CSV: нет заголовка");
  CsvLog log;
  log.header = std::move(rows[0]);
  for (size_t n = 1; n < rows.size(); ++n) {
    if (rows[n].size() != log.header.size()) throw Error("CSV: строка " + std::to_string(n + 1) + " другой ширины");
    std::vector<Cell> r;
    for (const auto& f : rows[n]) r.push_back(cell_decode(f));
    log.rows.push_back(std::move(r));
  }
  return log;
}

std::string csvlog_dump(const CsvLog& log) {
  std::string out = csv_write_row(log.header);
  for (const auto& r : log.rows) {
    std::vector<std::string> f;
    for (const auto& c : r) f.push_back(cell_encode(c));
    out += csv_write_row(f);
  }
  return out;
}

}  // namespace tf
