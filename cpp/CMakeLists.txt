# SPDX-License-Identifier: GPL-3.0-or-later
# Двойник Morrowind 2077, C++-ядро (задача 25). Ступень 25a: каркас, числа, дерево значений, снимок, CSV.
# Сборка: cmake -S cpp -B build && cmake --build build && ctest --test-dir build
# Обратная проверка: cmake -S cpp -B build-r176 -DTF_BUG=HEX_SHORT  (один дефект, тесты обязаны покраснеть)
cmake_minimum_required(VERSION 3.20)
project(tf_core CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(TF_BUG "" CACHE STRING "Внести один дефект для обратной проверки: HEX_SHORT, ROUND_NAIVE, NO_KEYSORT, DICT_SORTED, CSV_NOQUOTE, IDIV_TRUNC")

# Правила чисел (reports/23-formula-order.md): без слияния умножения со сложением, без fast-math.
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  set(TF_FLAGS -ffp-contract=off -fno-fast-math -Wall -Wextra -Wpedantic -Werror)
elseif(MSVC)
  # [C] точный набор флагов MSVC на HP OMEN не проверен (spec 25 §6)
  set(TF_FLAGS /fp:precise /fp:contract- /W4 /WX /utf-8)
endif()

add_library(tf_core STATIC
  core/num.cpp core/json.cpp core/value.cpp core/snapshot.cpp core/csvlog.cpp)
target_include_directories(tf_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_options(tf_core PUBLIC ${TF_FLAGS})
if(NOT TF_BUG STREQUAL "")
  target_compile_definitions(tf_core PUBLIC TF_BUG_${TF_BUG}=1)
endif()

add_executable(tf_snapcheck tools/tf_snapcheck.cpp)
target_link_libraries(tf_snapcheck PRIVATE tf_core)

enable_testing()
set(TF_GOLDEN_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../tests/golden")
set(TF_VECTOR_DIR "${CMAKE_CURRENT_SOURCE_DIR}/tests/vectors")
foreach(t test_num test_json test_value test_snapshot_golden test_csv test_csv_golden)
  add_executable(${t} tests/${t}.cpp)
  target_link_libraries(${t} PRIVATE tf_core)
  target_compile_definitions(${t} PRIVATE TF_GOLDEN_DIR="${TF_GOLDEN_DIR}" TF_VECTOR_DIR="${TF_VECTOR_DIR}")
  add_test(NAME ${t} COMMAND ${t})
endforeach()
