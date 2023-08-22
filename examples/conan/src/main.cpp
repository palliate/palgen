#include "example.h"
#include <vector>
#include <string>
#include <examplelib/demo.h>
#include <examplelib/examplelib.h>

int main() {
    example();
    examplelib();

    puts("");
    assert(demo_error_code().value() == 42);
    assert(demo_custom_error().value() == 10);

    $try(demo_error_code(true).value());
    $try(demo_error_code(true, true).value());
    $try(demo_custom_error(true).value());
    
    $try($printf("{}\n", get_number().and_then(increment).value()));
    $try($printf("{}\n", get_number(true).and_then(increment).value()));

    puts("get_number(true).or_else(...)");
    auto value = get_number(true).or_else(
        [](auto exc) -> std::expected<int, std::error_code>{
            $printf("->or_else\n\tmessage: {}\n", exc.message());
            return 3;
        }).value();
    assert(value == 3);
}
