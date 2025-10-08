cmake_minimum_required(VERSION 3.18)
project(tetwrap LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

# Try installed pybind11 first, then fetch if missing
find_package(pybind11 CONFIG QUIET)
if(NOT pybind11_FOUND)
  include(FetchContent)
  FetchContent_Declare(
    pybind11
    GIT_REPOSITORY https://github.com/pybind/pybind11.git
    GIT_TAG        v2.12.0
  )
  FetchContent_MakeAvailable(pybind11)
endif()

# Locate TetGen sources one level up
set(TETGEN_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../tetgen")

if(NOT EXISTS "${TETGEN_DIR}/tetgen.cxx")
  message(FATAL_ERROR "tetgen.cxx not found at ${TETGEN_DIR} (expected ../tetgen)")
endif()
if(NOT EXISTS "${TETGEN_DIR}/tetgen.h")
  message(FATAL_ERROR "tetgen.h not found at ${TETGEN_DIR}")
endif()

set(TETGEN_SOURCES "${TETGEN_DIR}/tetgen.cxx")
if(EXISTS "${TETGEN_DIR}/predicates.cxx")
  list(APPEND TETGEN_SOURCES "${TETGEN_DIR}/predicates.cxx")
else()
  message(WARNING "predicates.cxx not found; robust predicates may be missing.")
endif()

add_library(tet STATIC ${TETGEN_SOURCES})
target_compile_definitions(tet PUBLIC TETLIBRARY)
target_include_directories(tet PUBLIC "${TETGEN_DIR}")

if(APPLE)
  target_link_options(tet PRIVATE "-Wl,-undefined,error")
endif()

pybind11_add_module(_tetwrap tetwrap.cpp)
target_link_libraries(_tetwrap PRIVATE tet)

set_target_properties(_tetwrap PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
  RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
  ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
)

if(MSVC)
  target_compile_options(tet PRIVATE /W4)
  target_compile_options(_tetwrap PRIVATE /W4)
else()
  target_compile_options(tet PRIVATE -Wall -Wextra -Wpedantic)
  target_compile_options(_tetwrap PRIVATE -Wall -Wextra -Wpedantic)
endif()

