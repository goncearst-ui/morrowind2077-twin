// SPDX-License-Identifier: GPL-3.0-or-later
// Двойник Morrowind 2077, C++-ядро. Чтение и запись снимка (см. snapshot.hpp).
#include "core/snapshot.hpp"

#include <fstream>
#include <iterator>

#include "core/error.hpp"
#include "core/num.hpp"

namespace tf {

namespace {
std::vector<std::string_view> split_lines(std::string_view text) {
  std::vector<std::string_view> rows;
  size_t st = 0;
  while (true) {
    size_t nl = text.find('\n', st);
    if (nl == std::string_view::npos) {
      if (st < text.size()) rows.push_back(text.substr(st));
      break;
    }
    rows.push_back(text.substr(st, nl - st));
    st = nl + 1;
  }
  return rows;
}
}  // namespace

Snapshot snapshot_parse(std::string_view text) {
  auto rows = split_lines(text);
  if (rows.empty()) throw Error("снимок пуст");
  Json head = json_parse(rows[0]);
  const Json* sc = head.get("schema");
  const Json* tk = head.get("tick");
  const Json* lg = head.get("logs");
  if (head.k != Json::K::Obj || head.osize() != 3 || !sc || !tk || !lg || sc->k != Json::K::Int || tk->k != Json::K::Int ||
      lg->k != Json::K::Bool)
    throw Error("неверная шапка снимка");
  if (sc->i != 1) throw Error("схема " + std::to_string(sc->i) + " не поддерживается (ожидалась 1)");
  Snapshot s;
  s.schema = sc->i;
  s.tick = tk->i;
  s.logs = lg->b;
  for (size_t n = 1; n < rows.size(); ++n) {
    Json row = json_parse(rows[n]);
    if (row.k != Json::K::Arr || row.a.size() != 2 || row.a[0].k != Json::K::Str)
      throw Error("строка " + std::to_string(n + 1) + ": ожидалось [\"поле\", значение]");
    s.fields.emplace_back(row.a[0].s, dec(row.a[1]));
  }
  return s;
}

std::string snapshot_dump(const Snapshot& s) {
  Json head = Json::obj();
  head.put("schema", Json::integer(s.schema));
  head.put("tick", Json::integer(s.tick));
  head.put("logs", Json::boolean(s.logs));
  std::string out = json_dump(head);
  out += '\n';
  for (const auto& f : s.fields) {
    Json row = Json::arr();
    row.a.push_back(Json::str(f.first));
    row.a.push_back(enc(f.second));
    out += json_dump(row);
    out += '\n';
  }
  return out;
}

namespace {
void walk(const Json& x, const std::string& path, std::vector<std::string>& bad) {
  if (x.k == Json::K::Arr) {
    for (size_t n = 0; n < x.a.size(); ++n) walk(x.a[n], path + "[" + std::to_string(n) + "]", bad);
  } else if (x.k == Json::K::Obj) {
    const Json* f = x.get("f");
    if (x.osize() == 1 && f) {
      if (f->k != Json::K::Str) {
        bad.push_back(path + ": не строка");
        return;
      }
      try {
        if (hexfloat(parse_hexfloat(f->s)) != f->s) bad.push_back(path + ": " + f->s);
      } catch (const Error&) {
        bad.push_back(path + ": " + f->s);
      }
    } else {
      for (size_t n = 0; n < x.okeys.size(); ++n) walk(x.ovals[n], path + "." + x.okeys[n], bad);
    }
  }
}
}  // namespace

std::vector<std::string> exact_report(std::string_view text) {
  std::vector<std::string> bad;
  auto rows = split_lines(text);
  for (size_t n = 1; n < rows.size(); ++n) {
    if (rows[n].empty()) continue;
    Json row = json_parse(rows[n]);
    if (row.k != Json::K::Arr || row.a.size() != 2 || row.a[0].k != Json::K::Str) throw Error("строка снимка не [поле, значение]");
    walk(row.a[1], row.a[0].s, bad);
  }
  return bad;
}

std::string read_file(const std::string& path) {
  std::ifstream f(path, std::ios::binary);
  if (!f) throw Error("не открывается файл: " + path);
  return std::string(std::istreambuf_iterator<char>(f), std::istreambuf_iterator<char>());
}

void write_file(const std::string& path, std::string_view data) {
  std::ofstream f(path, std::ios::binary | std::ios::trunc);
  if (!f) throw Error("не открывается для записи: " + path);
  f.write(data.data(), static_cast<std::streamsize>(data.size()));
  if (!f) throw Error("ошибка записи: " + path);
}

}  // namespace tf
