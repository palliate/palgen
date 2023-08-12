#pragma once

#include <vector>
#include <string>


#ifdef _WIN32
  #define EXAMPLE_EXPORT __declspec(dllexport)
#else
  #define EXAMPLE_EXPORT
#endif

EXAMPLE_EXPORT void example();
EXAMPLE_EXPORT void example_print_vector(const std::vector<std::string> &strings);
