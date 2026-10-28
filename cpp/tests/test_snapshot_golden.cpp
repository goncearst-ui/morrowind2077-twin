// SPDX-License-Identifier: GPL-3.0-or-later
// Двойник Morrowind 2077, C++-ядро. V1: круговой проход четырёх золотых снимков tests/golden/ref_small_t*.snap байт в байт.
#include "check.hpp"
#include "core/error.hpp"
#include "core/snapshot.hpp"

using namespace tf;

int main() {
  const int ticks[] = {0, 100, 500, 1000};
  for (int t : ticks) {
    char name[64];
    std::snprintf(name, sizeof name, "/ref_small_t%04d.snap", t);
    std::string path = std::string(TF_GOLDEN_DIR) + name;
    std::string src;
    try {
      src = read_file(path);
    } catch (const Error& e) {
      CHECK_MSG(false, "%s", e.what());
      continue;
    }
    CHECK_MSG(exact_report(src).empty(), "%s: числа без точной записи", name);
    try {
      Snapshot s = snapshot_parse(src);
      CHECK_MSG(s.tick == t, "%s: тик в шапке %lld", name, static_cast<long long>(s.tick));
      CHECK(s.fields.size() > 10);
      std::string back = snapshot_dump(s);
      CHECK_MSG(back == src, "%s: записанное не совпало с исходным", name);
      // Второй проход: прочитанное из записанного равно прочитанному (значения, не только байты).
      Snapshot s2 = snapshot_parse(back);
      CHECK(s2.fields.size() == s.fields.size());
      for (size_t i = 0; i < s.fields.size() && i < s2.fields.size(); ++i)
        CHECK_MSG(s.fields[i].first == s2.fields[i].first && value_equal(s.fields[i].second, s2.fields[i].second), "поле %s", s.fields[i].first.c_str());
      // Порядок словаря фракций — как в двойнике (вставка, не алфавит): Метрополия, Налётчики, Колония, Дрейф.
      for (const auto& f : s.fields) {
        if (f.first == "factions") {
          CHECK(f.second.k == Value::K::Dict && f.second.items.size() == 4);
          CHECK(f.second.items[0].s == "Метрополия" && f.second.items[1].s == "Налётчики" && f.second.items[2].s == "Колония" &&
                f.second.items[3].s == "Дрейф");
        }
      }
    } catch (const Error& e) {
      CHECK_MSG(false, "%s: %s", name, e.what());
    }
  }
  return test_done("test_snapshot_golden");
}
