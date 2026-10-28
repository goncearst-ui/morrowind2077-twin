// SPDX-License-Identifier: GPL-3.0-or-later
// Двойник Morrowind 2077, C++-ядро. JSON-подмножество (см. json.hpp).
#include "core/json.hpp"

#include <algorithm>
#include <cstring>
#include <limits>

#include "core/error.hpp"

namespace tf {

const Json* Json::get(std::string_view key) const {
  for (size_t n = 0; n < okeys.size(); ++n)
    if (okeys[n] == key) return &ovals[n];
  return nullptr;
}

bool utf8_valid(std::string_view s) {
  size_t i = 0, n = s.size();
  auto cont = [&](size_t j) { return j < n && (static_cast<unsigned char>(s[j]) & 0xC0) == 0x80; };
  while (i < n) {
    unsigned char c = static_cast<unsigned char>(s[i]);
    if (c < 0x80) { ++i; continue; }
    if (c >= 0xC2 && c <= 0xDF) {
      if (!cont(i + 1)) return false;
      i += 2;
    } else if (c >= 0xE0 && c <= 0xEF) {
      if (!cont(i + 1) || !cont(i + 2)) return false;
      unsigned char c1 = static_cast<unsigned char>(s[i + 1]);
      if (c == 0xE0 && c1 < 0xA0) return false;   // слишком длинная запись
      if (c == 0xED && c1 >= 0xA0) return false;  // суррогаты
      i += 3;
    } else if (c >= 0xF0 && c <= 0xF4) {
      if (!cont(i + 1) || !cont(i + 2) || !cont(i + 3)) return false;
      unsigned char c1 = static_cast<unsigned char>(s[i + 1]);
      if (c == 0xF0 && c1 < 0x90) return false;
      if (c == 0xF4 && c1 >= 0x90) return false;
      i += 4;
    } else {
      return false;
    }
  }
  return true;
}

namespace {

struct Parser {
  std::string_view t;
  size_t p = 0;
  int depth = 0;

  [[noreturn]] void fail(const char* what) const {
    throw Error(std::string("JSON: ") + what + " на байте " + std::to_string(p));
  }
  void ws() {
    while (p < t.size() && (t[p] == ' ' || t[p] == '\t' || t[p] == '\n' || t[p] == '\r')) ++p;
  }
  bool eat(char c) {
    if (p < t.size() && t[p] == c) { ++p; return true; }
    return false;
  }
  void lit(const char* w) {
    size_t n = std::strlen(w);
    if (t.compare(p, n, w) != 0) fail("неизвестное слово");
    p += n;
  }

  unsigned hex4() {
    if (p + 4 > t.size()) fail("обрыв \\u");
    unsigned v = 0;
    for (int k = 0; k < 4; ++k) {
      char c = t[p++];
      v <<= 4;
      if (c >= '0' && c <= '9') v |= static_cast<unsigned>(c - '0');
      else if (c >= 'a' && c <= 'f') v |= static_cast<unsigned>(c - 'a' + 10);
      else if (c >= 'A' && c <= 'F') v |= static_cast<unsigned>(c - 'A' + 10);
      else fail("неверная цифра в \\u");
    }
    return v;
  }
  static void put_utf8(std::string& out, unsigned cp) {
    if (cp < 0x80) out += static_cast<char>(cp);
    else if (cp < 0x800) { out += static_cast<char>(0xC0 | (cp >> 6)); out += static_cast<char>(0x80 | (cp & 0x3F)); }
    else if (cp < 0x10000) {
      out += static_cast<char>(0xE0 | (cp >> 12));
      out += static_cast<char>(0x80 | ((cp >> 6) & 0x3F));
      out += static_cast<char>(0x80 | (cp & 0x3F));
    } else {
      out += static_cast<char>(0xF0 | (cp >> 18));
      out += static_cast<char>(0x80 | ((cp >> 12) & 0x3F));
      out += static_cast<char>(0x80 | ((cp >> 6) & 0x3F));
      out += static_cast<char>(0x80 | (cp & 0x3F));
    }
  }

  std::string string() {  // после открывающей кавычки
    std::string out;
    while (true) {
      if (p >= t.size()) fail("строка не закрыта");
      unsigned char c = static_cast<unsigned char>(t[p++]);
      if (c == '"') return out;
      if (c < 0x20) fail("управляющий символ в строке");
      if (c != '\\') { out += static_cast<char>(c); continue; }
      if (p >= t.size()) fail("обрыв после обратной косой");
      char e = t[p++];
      switch (e) {
        case '"': out += '"'; break;
        case '\\': out += '\\'; break;
        case '/': out += '/'; break;
        case 'b': out += '\b'; break;
        case 'f': out += '\f'; break;
        case 'n': out += '\n'; break;
        case 'r': out += '\r'; break;
        case 't': out += '\t'; break;
        case 'u': {
          unsigned cp = hex4();
          if (cp >= 0xD800 && cp <= 0xDBFF) {
            if (p + 2 > t.size() || t[p] != '\\' || t[p + 1] != 'u') fail("одиночный суррогат");
            p += 2;
            unsigned lo = hex4();
            if (lo < 0xDC00 || lo > 0xDFFF) fail("неверная пара суррогатов");
            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
          } else if (cp >= 0xDC00 && cp <= 0xDFFF) {
            fail("одиночный суррогат");
          }
          put_utf8(out, cp);
          break;
        }
        default: fail("неизвестная escape-последовательность");
      }
    }
  }

  Json number() {
    size_t st = p;
    bool neg = eat('-');
    if (p >= t.size() || t[p] < '0' || t[p] > '9') fail("ожидалась цифра");
    if (t[p] == '0' && p + 1 < t.size() && t[p + 1] >= '0' && t[p + 1] <= '9') fail("ведущий ноль");
    uint64_t v = 0;
    const uint64_t lim = neg ? (uint64_t(1) << 63) : static_cast<uint64_t>(std::numeric_limits<int64_t>::max());
    while (p < t.size() && t[p] >= '0' && t[p] <= '9') {
      uint64_t d = static_cast<uint64_t>(t[p] - '0');
      if (v > (lim - d) / 10) fail("целое вне int64");
      v = v * 10 + d;
      ++p;
    }
    if (p < t.size() && (t[p] == '.' || t[p] == 'e' || t[p] == 'E')) fail("дробные числа в снимке не допускаются");
    (void)st;
    return Json::integer(neg ? static_cast<int64_t>(0 - v) : static_cast<int64_t>(v));
  }

  Json value() {
    ws();
    if (p >= t.size()) fail("обрыв значения");
    if (++depth > 256) fail("слишком глубокая вложенность");
    Json r;
    char c = t[p];
    if (c == '{') {
      ++p;
      r = Json::obj();
      ws();
      if (!eat('}')) {
        while (true) {
          ws();
          if (!eat('"')) fail("ожидался ключ");
          std::string key = string();
          for (const auto& k0 : r.okeys)
            if (k0 == key) fail("повтор ключа");
          ws();
          if (!eat(':')) fail("ожидалось двоеточие");
          Json v = value();
          r.put(std::move(key), std::move(v));
          ws();
          if (eat(',')) continue;
          if (eat('}')) break;
          fail("ожидалась запятая или }");
        }
      }
    } else if (c == '[') {
      ++p;
      r = Json::arr();
      ws();
      if (!eat(']')) {
        while (true) {
          r.a.push_back(value());
          ws();
          if (eat(',')) continue;
          if (eat(']')) break;
          fail("ожидалась запятая или ]");
        }
      }
    } else if (c == '"') {
      ++p;
      r = Json::str(string());
    } else if (c == 't') { lit("true"); r = Json::boolean(true); }
    else if (c == 'f') { lit("false"); r = Json::boolean(false); }
    else if (c == 'n') { lit("null"); r = Json::null(); }
    else if (c == '-' || (c >= '0' && c <= '9')) r = number();
    else fail("неожиданный символ");
    --depth;
    return r;
  }
};

[[maybe_unused]] bool key_less(const std::string& x, const std::string& y) {
  size_t n = std::min(x.size(), y.size());
  int c = n ? std::memcmp(x.data(), y.data(), n) : 0;  // побайтово: для UTF-8 совпадает с порядком кодовых точек Python
  return c != 0 ? c < 0 : x.size() < y.size();
}

void dump(std::string& out, const Json& j) {
  switch (j.k) {
    case Json::K::Null: out += "null"; break;
    case Json::K::Bool: out += j.b ? "true" : "false"; break;
    case Json::K::Int: out += std::to_string(j.i); break;
    case Json::K::Str: json_append_string(out, j.s); break;
    case Json::K::Arr:
      out += '[';
      for (size_t n = 0; n < j.a.size(); ++n) {
        if (n) out += ',';
        dump(out, j.a[n]);
      }
      out += ']';
      break;
    case Json::K::Obj: {
      std::vector<size_t> items;
      for (size_t n = 0; n < j.okeys.size(); ++n) items.push_back(n);
#ifndef TF_BUG_NO_KEYSORT  // R178: ключи объектов не сортируются
      std::sort(items.begin(), items.end(), [&](size_t x, size_t y) { return key_less(j.okeys[x], j.okeys[y]); });
#endif
      out += '{';
      for (size_t n = 0; n < items.size(); ++n) {
        if (n) out += ',';
        json_append_string(out, j.okeys[items[n]]);
        out += ':';
        dump(out, j.ovals[items[n]]);
      }
      out += '}';
      break;
    }
  }
}

}  // namespace

void json_append_string(std::string& out, std::string_view s) {
  static const char* hex = "0123456789abcdef";
  out += '"';
  for (char ch : s) {
    unsigned char c = static_cast<unsigned char>(ch);
    switch (c) {
      case '"': out += "\\\""; break;
      case '\\': out += "\\\\"; break;
      case '\b': out += "\\b"; break;
      case '\f': out += "\\f"; break;
      case '\n': out += "\\n"; break;
      case '\r': out += "\\r"; break;
      case '\t': out += "\\t"; break;
      default:
        if (c < 0x20) {
          out += "\\u00";
          out += hex[c >> 4];
          out += hex[c & 15];
        } else {
          out += ch;
        }
    }
  }
  out += '"';
}

Json json_parse(std::string_view text) {
  if (!utf8_valid(text)) throw Error("JSON: недопустимый UTF-8");
  Parser ps{text};
  Json r = ps.value();
  ps.ws();
  if (ps.p != text.size()) ps.fail("лишний текст после значения");
  return r;
}

std::string json_dump(const Json& j) {
  std::string out;
  dump(out, j);
  return out;
}

}  // namespace tf
