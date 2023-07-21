#include <iostream>
#include <span>
#include <cstdint>

#include <src/embed.hpp>

void print(std::span<std::uint8_t const> data){
    for (auto const& element: data) {
        std::cout << element;
    }
}

int main() {
    auto data = Embed::get("src/test.txt");
    print(data);
}