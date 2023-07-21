#include <array>
#include <cstdint>
#include <string_view>
#include <span>

namespace Embed {
    using Resource = std::pair<std::string_view, std::span<const std::uint8_t>>;

    constexpr static auto r${hash}_data = std::to_array<std::uint8_t>({
        $data
    });
    constexpr static auto r$hash = Resource{R"($path)", r${hash}_data};
}
