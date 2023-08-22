from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout, CMakeDeps
from conan.tools.files import copy


class examplelibRecipe(ConanFile):
    name = "examplelib"
    version = "0.1"
    package_type = "library"

    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    # do not forget to export `palgen.toml`
    exports_sources = "CMakeLists.txt", "src/*", "include/*", "palgen.toml"

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.rm_safe("fPIC")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self)

    def generate(self):
        deps = CMakeDeps(self)
        deps.generate()
        tc = CMakeToolchain(self)
        tc.generate()

        # instead of requiring the global `palgen` generator you can call it manually like this
        from palgen.integrations.conan import generate_manifest
        generate_manifest(self)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

        # copy the generated manifest to the package folder's root, otherwise it will not be found by dependents
        # This is a workaround. Unfortunately this recipe's package_folder is None during the generate() step
        copy(self, "palgen.manifest", self.build_folder, self.package_folder, keep_path=False)

    def package(self):
        cmake = CMake(self)
        cmake.install()


    def package_info(self):
        self.cpp_info.libs = ["examplelib"]
