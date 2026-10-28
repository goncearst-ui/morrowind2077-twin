// SPDX-License-Identifier: GPL-3.0-or-later
// Двойник Morrowind 2077, C++-ядро. enc/dec дерева значений (см. value.hpp, twin/snapshot.py).
#include "core/value.hpp"

#include <algorithm>

#include "core/error.hpp"
#include "core/num.hpp"

namespace tf {

namespace {
Json one(const char* key, Json v) {
  Json o = Json::obj();
  o.put(key, std::move(v));
  return o;
}
}  // namespace

Json enc(const Value& v) {
  switch (v.k) {
    case Value::K::Null: return Json::null();
    case Value::K::Bool: return Json::boolean(v.b);
    case Value::K::Int: return Json::integer(v.i);
    case Value::K::Str: return Json::str(v.s);
    case Value::K::Double: return one("f", Json::str(hexfloat(v.d)));
    case Value::K::List: {
      Json a = Json::arr();
      for (const auto& x : v.items) a.a.push_back(enc(x));
      return a;
    }
    case Value::K::Tuple: {
      Json a = Json::arr();
      for (const auto& x : v.items) a.a.push_back(enc(x));
      return one("t", std::move(a));
    }
    case Value::K::Dict: {
      Json a = Json::arr();
      for (size_t n = 0; n < v.items.size(); ++n) {
        Json pr = Json::arr();
        pr.a.push_back(enc(v.items[n]));
        pr.a.push_back(enc(v.vals[n]));
        a.a.push_back(std::move(pr));
      }
      return one("d", std::move(a));
    }
    case Value::K::Set: {  // элементы по возрастанию своей канонической записи (как sorted(..., key=_dump))
      std::vector<std::pair<std::string, Json>> el;
      for (const auto& x : v.items) {
        Json j = enc(x);
        std::string key = json_dump(j);
        el.emplace_back(std::move(key), std::move(j));
      }
      std::sort(el.begin(), el.end(), [](const auto& x, const auto& y) { return x.first < y.first; });
      Json a = Json::arr();
      for (auto& e : el) a.a.push_back(std::move(e.second));
      return one("s", std::move(a));
    }
    case Value::K::Record: {
      Json fields = Json::arr();
      for (size_t n = 0; n < v.names.size(); ++n) {
        Json pr = Json::arr();
        pr.a.push_back(Json::str(v.names[n]));
        pr.a.push_back(enc(v.vals[n]));
        fields.a.push_back(std::move(pr));
      }
      Json o = Json::obj();
      o.put("o", Json::str(v.s));
      o.put("v", std::move(fields));
      return o;
    }
  }
  throw Error("enc: неизвестный вид значения");
}

Value dec(const Json& j) {
  switch (j.k) {
    case Json::K::Null: return Value::null();
    case Json::K::Bool: return Value::boolean(j.b);
    case Json::K::Int: return Value::integer(j.i);
    case Json::K::Str: return Value::str(j.s);
    case Json::K::Arr: {
      Value l = Value::list();
      for (const auto& x : j.a) l.items.push_back(dec(x));
      return l;
    }
    case Json::K::Obj: break;
  }
  const Json* f = j.get("f");
  const Json* t = j.get("t");
  const Json* d = j.get("d");
  const Json* s = j.get("s");
  const Json* o = j.get("o");
  if (j.osize() == 1 && f) {
    if (f->k != Json::K::Str) throw Error("dec: {\"f\"} ждёт строку");
    return Value::real(parse_hexfloat(f->s));
  }
  if (j.osize() == 1 && t) {
    if (t->k != Json::K::Arr) throw Error("dec: {\"t\"} ждёт массив");
    Value v = Value::tuple();
    for (const auto& x : t->a) v.items.push_back(dec(x));
    return v;
  }
  if (j.osize() == 1 && d) {
    if (d->k != Json::K::Arr) throw Error("dec: {\"d\"} ждёт массив пар");
    Value v = Value::dict();
    for (const auto& pr : d->a) {
      if (pr.k != Json::K::Arr || pr.a.size() != 2) throw Error("dec: элемент словаря не пара [ключ, значение]");
      v.items.push_back(dec(pr.a[0]));
      v.vals.push_back(dec(pr.a[1]));
    }
#ifdef TF_BUG_DICT_SORTED  // R179: порядок вставки словаря при чтении теряется
    std::vector<size_t> idx(v.items.size());
    for (size_t n = 0; n < idx.size(); ++n) idx[n] = n;
    std::sort(idx.begin(), idx.end(), [&](size_t x, size_t y) { return json_dump(enc(v.items[x])) < json_dump(enc(v.items[y])); });
    Value w = Value::dict();
    for (size_t n : idx) { w.items.push_back(v.items[n]); w.vals.push_back(v.vals[n]); }
    v = std::move(w);
#endif
    return v;
  }
  if (j.osize() == 1 && s) {
    if (s->k != Json::K::Arr) throw Error("dec: {\"s\"} ждёт массив");
    Value v = Value::set();
    for (const auto& x : s->a) v.items.push_back(dec(x));
    return v;
  }
  if (j.osize() == 2 && o && j.get("v")) {
    const Json* fv = j.get("v");
    if (o->k != Json::K::Str || fv->k != Json::K::Arr) throw Error("dec: неверная запись {\"o\",\"v\"}");
    Value v = Value::record(o->s);
    for (const auto& pr : fv->a) {
      if (pr.k != Json::K::Arr || pr.a.size() != 2 || pr.a[0].k != Json::K::Str) throw Error("dec: неверное поле записи");
      v.names.push_back(pr.a[0].s);
      v.vals.push_back(dec(pr.a[1]));
    }
    return v;
  }
  throw Error("dec: неизвестная запись");
}

bool value_equal(const Value& a, const Value& b) {
  if (a.k != b.k) return false;
  switch (a.k) {
    case Value::K::Null: return true;
    case Value::K::Bool: return a.b == b.b;
    case Value::K::Int: return a.i == b.i;
    case Value::K::Double: return bits_of(a.d) == bits_of(b.d);
    case Value::K::Str: return a.s == b.s;
    case Value::K::Record:
      if (a.s != b.s || a.names != b.names || a.vals.size() != b.vals.size()) return false;
      for (size_t n = 0; n < a.vals.size(); ++n)
        if (!value_equal(a.vals[n], b.vals[n])) return false;
      return true;
    case Value::K::Dict:
      if (a.items.size() != b.items.size() || a.vals.size() != b.vals.size()) return false;
      for (size_t n = 0; n < a.items.size(); ++n)
        if (!value_equal(a.items[n], b.items[n]) || !value_equal(a.vals[n], b.vals[n])) return false;
      return true;
    case Value::K::List:
    case Value::K::Tuple:
    case Value::K::Set:
      if (a.items.size() != b.items.size()) return false;
      for (size_t n = 0; n < a.items.size(); ++n)
        if (!value_equal(a.items[n], b.items[n])) return false;
      return true;
  }
  return false;
}

}  // namespace tf
