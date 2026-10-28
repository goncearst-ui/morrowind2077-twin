// SPDX-License-Identifier: GPL-3.0-or-later
// Двойник Morrowind 2077, C++-ядро. tf_snapcheck ФАЙЛ...: для каждого файла прочитать, записать обратно и сравнить байты.
//   *.snap — снимок (schema 1); дополнительно проверяется, что каждое дробное число записано точной hex-записью.
//   *.csv  — журнал с типизированными ячейками.
// Код возврата 0 — все файлы совпали байт в байт; 1 — есть расхождение или файл не читается.
#include <cstdio>
#include <string>

#include "core/csvlog.hpp"
#include "core/error.hpp"
#include "core/snapshot.hpp"

namespace {
bool ends_with(const std::string& s, const char* suf) {
  std::string t(suf);
  return s.size() >= t.size() && s.compare(s.size() - t.size(), t.size(), t) == 0;
}

void report_diff(const std::string& a, const std::string& b) {
  size_t n = 0;
  while (n < a.size() && n < b.size() && a[n] == b[n]) ++n;
  size_t line = 1;
  for (size_t k = 0; k < n; ++k)
    if (a[k] == '\n') ++line;
  std::printf("  первое расхождение: байт %zu, строка %zu (размер исходного %zu, записанного %zu)\n", n, line, a.size(), b.size());
}
}  // namespace

int main(int argc, char** argv) {
  if (argc < 2) {
    std::printf("использование: tf_snapcheck ФАЙЛ.snap|ФАЙЛ.csv ...\n");
    return 1;
  }
  int bad = 0;
  for (int n = 1; n < argc; ++n) {
    std::string path = argv[n];
    try {
      std::string src = tf::read_file(path);
      std::string back;
      if (ends_with(path, ".snap")) {
        auto inexact = tf::exact_report(src);
        if (!inexact.empty()) {
          std::printf("%s: числа без точной записи: %zu (первое: %s)\n", path.c_str(), inexact.size(), inexact[0].c_str());
          ++bad;
          continue;
        }
        back = tf::snapshot_dump(tf::snapshot_parse(src));
      } else if (ends_with(path, ".csv")) {
        back = tf::csvlog_dump(tf::csvlog_parse(src));
      } else {
        std::printf("%s: неизвестный тип файла\n", path.c_str());
        ++bad;
        continue;
      }
      if (back == src) {
        std::printf("%s: совпало (%zu байт)\n", path.c_str(), src.size());
      } else {
        std::printf("%s: РАСХОЖДЕНИЕ\n", path.c_str());
        report_diff(src, back);
        ++bad;
      }
    } catch (const tf::Error& e) {
      std::printf("%s: ошибка: %s\n", path.c_str(), e.what());
      ++bad;
    }
  }
  return bad ? 1 : 0;
}
