#pragma once

#include <vector>
#include <string>


#ifdef _WIN32
  #define EXAMPLELIB_EXPORT __declspec(dllexport)
#else
  #define EXAMPLELIB_EXPORT
#endif

EXAMPLELIB_EXPORT void examplelib();
EXAMPLELIB_EXPORT void examplelib_print_vector(const std::vector<std::string> &strings);
