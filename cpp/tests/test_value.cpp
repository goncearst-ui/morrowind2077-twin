// SPDX-License-Identifier: GPL-3.0-or-later
// Двойник Morrowind 2077, C++-ядро. Дерево значений: enc/dec как в twin/snapshot.py, порядок словаря, множество, запись, типы чисел.
#include "check.hpp"
#include "core/error.hpp"
#include "core/num.hpp"
#include "core/value.hpp"

using namespace tf;

static std::string text(const Value& v) { return json_dump(enc(v)); }
static Value parse(const std::string& s) { return dec(json_parse(s)); }

int main() {
  // Числа: целое и дробное различаются, дробное пишется точно, минус ноль сохраняется.
  CHECK(text(Value::integer(1)) == "1");
  CHECK(text(Value::real(1.0)) == "{\"f\":\"0x1.0000000000000p+0\"}");
  CHECK(text(Value::real(-0.0)) == "{\"f\":\"-0x0.0p+0\"}");
  CHECK(!value_equal(Value::integer(1), Value::real(1.0)));
  CHECK(!value_equal(Value::real(0.0), Value::real(-0.0)));
  CHECK(value_equal(parse("{\"f\":\"-0x0.0p+0\"}"), Value::real(-0.0)));

  // Словарь хранит порядок вставки: ключ «я» раньше «а», порядок не сортируется ни при чтении, ни при записи.
  Value d = Value::dict();
  d.items.push_back(Value::str("я")); d.vals.push_back(Value::integer(1));
  d.items.push_back(Value::str("а")); d.vals.push_back(Value::integer(2));
  d.items.push_back(Value::integer(5)); d.vals.push_back(Value::null());
  CHECK(text(d) == "{\"d\":[[\"я\",1],[\"а\",2],[5,null]]}");
  Value d2 = parse(text(d));
  CHECK(d2.k == Value::K::Dict && d2.items.size() == 3 && d2.items[0].s == "я" && d2.items[1].s == "а" && d2.items[2].i == 5);
  CHECK(value_equal(d, d2));
  Value swapped = d2;
  std::swap(swapped.items[0], swapped.items[1]);
  std::swap(swapped.vals[0], swapped.vals[1]);
  CHECK(!value_equal(d, swapped));      // порядок — часть состояния

  // Множество: элементы пишутся по возрастанию своей записи, независимо от порядка добавления.
  Value s = Value::set();
  for (const char* x : {"б", "а", "в"}) s.items.push_back(Value::str(x));
  s.items.push_back(Value::integer(10));
  s.items.push_back(Value::integer(9));
  CHECK(text(s) == "{\"s\":[\"а\",\"б\",\"в\",10,9]}");

  // Кортеж, запись (порядок полей), вложенность.
  Value t = Value::tuple();
  t.items.push_back(Value::integer(1)); t.items.push_back(Value::real(0.5)); t.items.push_back(Value::null());
  CHECK(text(t) == "{\"t\":[1,{\"f\":\"0x1.0000000000000p-1\"},null]}");
  Value r = Value::record("Faction");
  r.names = {"name", "supply", "pos"};
  r.vals = {Value::str("Дрейф"), Value::real(3.25), t};
  std::string rt = text(r);
  CHECK(rt.rfind("{\"o\":\"Faction\",\"v\":[[\"name\",\"Дрейф\"],[\"supply\",", 0) == 0);
  Value r2 = parse(rt);
  CHECK(value_equal(r, r2) && text(r2) == rt);
  Value lst = Value::list();
  lst.items = {r, d, s, Value::boolean(true), Value::boolean(false), Value::str("")};
  CHECK(text(parse(text(lst))) == text(lst));

  // Ошибки формы.
  auto bad = [](const char* j) {
    try {
      parse(j);
    } catch (const Error&) {
      return true;
    }
    return false;
  };
  CHECK(bad("{\"f\":1}"));
  CHECK(bad("{\"x\":1}"));
  CHECK(bad("{}"));
  CHECK(bad("{\"d\":[[1]]}"));
  CHECK(bad("{\"d\":[[1,2,3]]}"));
  CHECK(bad("{\"o\":\"A\"}"));
  CHECK(bad("{\"f\":\"0x1.8p+1\",\"t\":[]}"));
  CHECK(bad("{\"f\":\"zzz\"}"));
  return test_done("test_value");
}
