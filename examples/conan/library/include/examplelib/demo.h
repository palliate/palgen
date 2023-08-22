#pragma once
#include <expected>
#include <system_error>

#include <examplelib/visibility.h>
#include <examplelib/error.hpp>

EXPORTED std::expected<int, std::error_code>
demo_error_code(bool fail = false, bool custom_error = false);

EXPORTED std::expected<int, Error::Library::Code>
demo_custom_error(bool fail = false);