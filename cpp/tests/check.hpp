// SPDX-License-Identifier: GPL-3.0-or-later
// Двойник Morrowind 2077, C++-ядро. Минимальная проверялка для тестов (без внешних библиотек).
#pragma once
#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

namespace tt {
inline int& fails() { static int n = 0; return n; }
inline int& checks() { static int n = 0; return n; }
}  // namespace tt

#define CHECK(cond)                                                                \
  do {                                                                             \
    ++tt::checks();                                                                \
    if (!(cond)) {                                                                 \
      if (++tt::fails() <= 20) std::printf("ПРОВАЛ %s:%d: %s\n", __FILE__, __LINE__, #cond); \
    }                                                                              \
  } while (0)

#define CHECK_MSG(cond, ...)                                                       \
  do {                                                                             \
    ++tt::checks();                                                                \
    if (!(cond)) {                                                                 \
      if (++tt::fails() <= 20) {                                                   \
        std::printf("ПРОВАЛ %s:%d: ", __FILE__, __LINE__);                         \
        std::printf(__VA_ARGS__);                                                  \
        std::printf("\n");                                                         \
      }                                                                            \
    }                                                                              \
  } while (0)

inline int test_done(const char* name) {
  std::printf("%s: проверок %d, провалов %d\n", name, tt::checks(), tt::fails());
  return tt::fails() ? 1 : 0;
}

// Строки файла векторов без комментариев (# ...) и пустых.
inline std::vector<std::string> vector_lines(const std::string& name) {
  std::ifstream f(std::string(TF_VECTOR_DIR) + "/" + name, std::ios::binary);
  std::vector<std::string> out;
  if (!f) {
    std::printf("ПРОВАЛ: нет файла векторов %s\n", name.c_str());
    ++tt::fails();
    return out;
  }
  std::string line;
  while (std::getline(f, line)) {
    if (line.empty() || line[0] == '#') continue;
    out.push_back(line);
  }
  if (out.empty()) {
    std::printf("ПРОВАЛ: файл векторов %s пуст\n", name.c_str());
    ++tt::fails();
  }
  return out;
}

inline std::string unhex(const std::string& h) {
  std::string out;
  if (h == "_") return out;
  auto v = [](char c) { return c <= '9' ? c - '0' : c - 'a' + 10; };
  for (size_t i = 0; i + 1 < h.size(); i += 2) out += static_cast<char>(v(h[i]) * 16 + v(h[i + 1]));
  return out;
}

inline std::vector<std::string> split(const std::string& s, char sep) {
  std::vector<std::string> out;
  std::string cur;
  for (char c : s) {
    if (c == sep) { out.push_back(cur); cur.clear(); }
    else cur += c;
  }
  out.push_back(cur);
  return out;
}
