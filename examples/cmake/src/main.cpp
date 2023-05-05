#include <iostream>
#include "generated/info.h"

int main() {
    std::cout 
        << "Name:        " << project_info.name        << '\n'
        << "Version:     " << project_info.version     << '\n'
        << "Description: " << project_info.description << '\n';
}