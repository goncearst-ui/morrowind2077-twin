// SPDX-License-Identifier: GPL-3.0-or-later
// Двойник Morrowind 2077, C++-ядро. V1: круговой проход двух золотых журналов (подробный и сводный) байт в байт.
#include "check.hpp"
#include "core/csvlog.hpp"
#include "core/error.hpp"
#include "core/snapshot.hpp"

using namespace tf;

int main() {
  struct File { const char* name; size_t width; const char* first; const char* last; };
  const File files[] = {{"ref_small_log_detail.csv", 7, "tick", "reason"}, {"ref_small_log_summary.csv", 8, "window", "nonnumeric"}};
  for (const auto& fl : files) {
    const char* name = fl.name;
    try {
      std::string src = read_file(std::string(TF_GOLDEN_DIR) + "/" + name);
      CsvLog log = csvlog_parse(src);
      CHECK_MSG(log.header.size() == fl.width && log.header[0] == fl.first && log.header.back() == fl.last, "%s: шапка", name);
      CHECK_MSG(log.rows.size() > 100, "%s: строк %zu", name, log.rows.size());
      std::string back = csvlog_dump(log);
      CHECK_MSG(back == src, "%s: записанное не совпало с исходным", name);
      // В каждой строке первый столбец (tick или window) — целое, как его пишет двойник.
      for (const auto& r : log.rows) {
        CHECK(r.size() == fl.width && r[0].k == Cell::K::Int);
        if (tt::fails() > 20) break;
      }
    } catch (const Error& e) {
      CHECK_MSG(false, "%s: %s", name, e.what());
    }
  }
  return test_done("test_csv_golden");
}
