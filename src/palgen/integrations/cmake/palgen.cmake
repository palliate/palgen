macro(palgen_setup)
    message(STATUS "palgen: Running setup")

    # generate project information
    execute_process(COMMAND palgen cmake --outpath ${CMAKE_BINARY_DIR} --project
                    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
                    RESULT_VARIABLE PALGEN_CONF_RESULT)
    if(NOT PALGEN_CONF_RESULT EQUAL "0")
        message(PALGEN_CONF_RESULT)
        message(FATAL_ERROR "Palgen did not run successfully")
    endif()

    # load project information
    include(${CMAKE_BINARY_DIR}/palgen_info.cmake)
endmacro()

function(palgen_run target)
    add_custom_target(
        "palgen_${target}"
        ALL
        COMMAND palgen --extra-folders "\"${CONAN_INCLUDE_DIRS}\""
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    )

    add_dependencies(${target} "palgen_${target}")
endfunction()