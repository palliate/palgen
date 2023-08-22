#include "examplelib/demo.h"

std::expected<int, std::error_code> demo_error_code(bool fail, bool custom_error) {
    if (fail) {
        if (custom_error) {
            return std::unexpected{Error::Library::Test};
        }
        return std::unexpected{
            std::make_error_code(std::errc::value_too_large)};
    }
    return 42;
}

std::expected<int, Error::Library::Code> demo_custom_error(bool fail) {
    if (fail) {
        return std::unexpected{Error::Library::Test};
    }
    return 10;
}