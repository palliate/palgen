cmake_minimum_required(VERSION 3.24)
set(CMAKE_VERBOSE_MAKEFILE ON)
if(NOT EXISTS ${CMAKE_BINARY_DIR}/palgen.cmake)
    message(STATUS "palgen: CMake helper not found, generating.")
    execute_process(
        COMMAND palgen cmake --outpath ${CMAKE_BINARY_DIR} --toolchain
        WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
        RESULT_VARIABLE palgen_setup_ret)

    if(palgen_setup_ret AND NOT palgen_setup_ret EQUAL 0)
        message(FATAL_ERROR "Generating cmake helper failed (${palgen_setup_ret}). Is palgen installed?")
    endif()
endif()

include(${CMAKE_BINARY_DIR}/palgen.cmake)
palgen_setup()

project(
  ${TARGET}
  VERSION "${TARGET_VERSION}"
  LANGUAGES CXX)

add_executable(${TARGET} "")
set_property(TARGET ${TARGET} PROPERTY CXX_STANDARD 20)

palgen_run(${TARGET})
target_include_directories(${TARGET} PRIVATE ${CMAKE_BINARY_DIR}/src)

# cannot find source file - palgen_run needs deps
target_sources(${TARGET} PRIVATE ${CMAKE_BINARY_DIR}/src/main.cpp)