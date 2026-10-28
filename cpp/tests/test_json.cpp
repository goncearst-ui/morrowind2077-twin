// SPDX-License-Identifier: GPL-3.0-or-later
// Двойник Morrowind 2077, C++-ядро. V0: JSON-подмножество (экранирование строк, канонический вид, разбор) против векторов из Python.
#include "check.hpp"
#include "core/error.hpp"
#include "core/json.hpp"

using namespace tf;

static bool bad(const std::string& text) {
  try {
    json_parse(text);
  } catch (const Error&) {
    return true;
  }
  return false;
}

int main() {
  for (const auto& ln : vector_lines("strings.txt")) {
    auto p = split(ln, ' ');
    std::string s = unhex(p[0]), want = unhex(p[1]), got;
    json_append_string(got, s);
    CHECK_MSG(got == want, "экранирование строки %s", p[0].c_str());
    Json back = json_parse(want);
    CHECK_MSG(back.k == Json::K::Str && back.s == s, "разбор строки %s", p[0].c_str());
  }

  for (const auto& ln : vector_lines("json.txt")) {
    auto tab = ln.find('\t');
    std::string src = unhex(ln.substr(0, tab)), canon = ln.substr(tab + 1);
    std::string got;
    try {
      got = json_dump(json_parse(src));
    } catch (const Error& e) {
      got = std::string("ОШИБКА: ") + e.what();
    }
    CHECK_MSG(got == canon, "канонический вид не совпал: ожидалось %.60s, получено %.60s", canon.c_str(), got.c_str());
    // Канонический вид — неподвижная точка.
    CHECK(json_dump(json_parse(canon)) == canon);
  }

  CHECK(json_dump(json_parse("{\"tick\":0,\"schema\":1,\"logs\":false}")) == "{\"logs\":false,\"schema\":1,\"tick\":0}");
  CHECK(json_dump(json_parse(" [ 1 , -9223372036854775808 , 9223372036854775807 ] ")) == "[1,-9223372036854775808,9223372036854775807]");

  CHECK(bad("1.5"));
  CHECK(bad("1e3"));
  CHECK(bad("01"));
  CHECK(bad("9223372036854775808"));
  CHECK(bad("-9223372036854775809"));
  CHECK(bad("[1,]"));
  CHECK(bad("{\"a\":1,\"a\":2}"));
  CHECK(bad("{\"a\" 1}"));
  CHECK(bad("\"abc"));
  CHECK(bad("\"\\x\""));
  CHECK(bad("\"\\ud800\""));
  CHECK(bad("\"\\udc00\""));
  CHECK(bad("\"a\nb\""));
  CHECK(bad("1 2"));
  CHECK(bad("NaN"));
  CHECK(bad(""));
  CHECK(bad("\"\xff\""));
  CHECK(bad("\"\xed\xa0\x80\""));        // суррогат в UTF-8
  CHECK(bad("\"\xc0\x80\""));            // слишком длинная запись
  CHECK(json_parse("\"\\ud83d\\ude00\"").s == "\xf0\x9f\x98\x80");
  CHECK(json_parse("-0").i == 0);
  return test_done("test_json");
}
