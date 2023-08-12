from conan import ConanFile
from conan.tools.cmake import CMake, cmake_layout


class exampleRecipe(ConanFile):
    name = "example"
    version = "0.1"
    package_type = "application"

    generators = "CMakeToolchain", "CMakeDeps", "palgen"

    # Optional metadata
    license = "<Put the package license here>"
    author = "<Put your name here> <And your email here>"
    url = "<Package recipe repository url here, for issues about the package>"
    description = "<Description of example package here>"

    # Binary configuration
    settings = "os", "compiler", "build_type", "arch"

    # Sources are located in the same place as this recipe, copy them to the recipe
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
