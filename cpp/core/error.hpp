// SPDX-License-Identifier: GPL-3.0-or-later
// Двойник Morrowind 2077, C++-ядро. Общая ошибка ядра: нарушение формата или правил чисел.
#pragma once
#include <stdexcept>
#include <string>

namespace tf {
struct Error : std::runtime_error {
  explicit Error(const std::string& m) : std::runtime_error(m) {}
};
}  // namespace tf
