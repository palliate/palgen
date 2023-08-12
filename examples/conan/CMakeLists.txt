cmake_minimum_required(VERSION 3.15)
project(example CXX)



add_executable(example src/example.cpp src/main.cpp)



install(TARGETS example DESTINATION "."
        RUNTIME DESTINATION bin
        ARCHIVE DESTINATION lib
        LIBRARY DESTINATION lib
        )
