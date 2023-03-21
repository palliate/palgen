from packaging import version

import conans
if version.parse(conans.__version__) < version.parse("2.0.0"):
    from pathlib import Path
    from conans.client.generators.text import TXTGenerator
    from conans.model.build_info import DepsCppInfo


    def parse_conanbuildinfo(file: Path) -> list[Path]:
        with open(file, 'r', encoding="utf-8") as conanbuildinfo:
            content = conanbuildinfo.read()
            deps_cpp_info, _, _, _ = TXTGenerator.loads(content)
            assert isinstance(deps_cpp_info, DepsCppInfo)
            return [Path(path) for path in deps_cpp_info.include_paths]


    def get_paths(root: Path) -> list[Path]:
        if (file := root / "conanbuildinfo.txt").exists():
            return parse_conanbuildinfo(file)
        if (root / "conanfile.py").exists() or (root / "conanfile.txt").exists():
            file = root / "build" / "conanbuildinfo.txt"
            if file.exists():
                return parse_conanbuildinfo(file)
        return []
