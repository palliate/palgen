from conan import ConanFile
from conan.tools.cmake import CMake, cmake_layout


class exampleRecipe(ConanFile):
    name = "example"
    version = "0.1"
    package_type = "application"
    settings = "os", "compiler", "build_type", "arch"

    # require the global palgen generator
    generators = "CMakeToolchain", "CMakeDeps", "palgen"
    # do not forget to export `palgen.toml`
    exports_sources = "CMakeLists.txt", "src/*", "palgen.toml"

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires("examplelib/0.1")

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
