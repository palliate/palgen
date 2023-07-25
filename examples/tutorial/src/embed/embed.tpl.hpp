#pragma once
#include <map.hpp>
$includes

namespace Embed {
    [[nodiscard]] auto get(std::string_view const key) -> std::span<std::uint8_t const> {
        static constexpr auto map = 
            Map<std::string_view, std::span<std::uint8_t const>, $amount>{
                $pairs
            };

        return map.at(key);
    }
}