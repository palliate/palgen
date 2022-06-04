import setuptools
from pathlib import Path

root_path = Path(__file__).parent.absolute()
with open(root_path / "README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="palliate-codegen",
    version="0.0.2",
    author="Tsche",
    author_email="contact@palliate.io",
    description="Code generation utility",
    long_description="Code generation utility",
    long_description_content_type="text/markdown",
    url="https://github.com/palliate/codegen",
    project_urls={
        "Bug Tracker": "https://github.com/palliate/codegen/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    install_requires=["jinja2", "click", "colorama", "toml"],
    entry_points={
        'console_scripts': [
            'palliate-codegen=palliate_codegen:main'
        ]
    }
)
