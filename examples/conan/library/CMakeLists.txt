cmake_minimum_required(VERSION 3.15)
project(examplelib CXX)




add_library(examplelib src/examplelib.cpp)
target_include_directories(examplelib PUBLIC include)



set_target_properties(examplelib PROPERTIES PUBLIC_HEADER "include/examplelib.h")
install(TARGETS examplelib)
