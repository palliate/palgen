#pragma once
#include <cassert>
#include <cstdio>
#include <format>
#include <expected>
#include <system_error>

#include <examplelib/error.hpp>
#include <error.hpp>

void example();

#define $printf(fmt, ...) puts(std::format(fmt, __VA_ARGS__).c_str())

void try_safely(auto try_) {
    auto print = [] (auto const& exception){
        $printf("\twhat(): {}\n\tmessage: {}\n\tcategory: {}\n", 
                exception.what(),
                exception.error().message(),
                exception.error().category().name());
    };

    try {
        try_();
    } catch (std::bad_expected_access<std::error_code> const& exception) {
        puts("-> Caught std::bad_expected_access<std::error_code>");
        print(exception);
    } catch (std::bad_expected_access<Error::Library::Code> const& exception) {
        puts("-> Caught std::bad_expected_access<Error::Generic::Code>");
        print(exception);
    } catch (std::bad_expected_access<Error::Application::Code> const& exception) {
        puts("-> Caught std::bad_expected_access<Error::Application::Code>");
        print(exception);
    }
}

#define $try(FNC) puts( #FNC ); try_safely([] { FNC; })

auto get_number(bool fail = false) -> std::expected<int, std::error_code>;
auto increment(int x) -> std::expected<int, std::error_code>;