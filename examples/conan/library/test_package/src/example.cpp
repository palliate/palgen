#include "examplelib.h"
#include <vector>
#include <string>

int main() {
    examplelib();

    std::vector<std::string> vec;
    vec.push_back("test_package");

    examplelib_print_vector(vec);
}
