from conan import ConanFile


class palgen:
    def __init__(self, conan_file: ConanFile):
        self.conan_file = conan_file

    def generate(self):
        from palgen.integrations.conan import generate_manifest
        generate_manifest(self.conan_file)
