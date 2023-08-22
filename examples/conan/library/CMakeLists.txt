cmake_minimum_required(VERSION 3.15)

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


add_library(${TARGET} src/examplelib.cpp src/demo.cpp)
set_property(TARGET ${TARGET} PROPERTY CXX_STANDARD 23)

palgen_run(${TARGET} ${CMAKE_SOURCE_DIR})

target_include_directories(${TARGET} PUBLIC include ${CMAKE_BINARY_DIR}/include)

install(TARGETS ${TARGET})
