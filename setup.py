#!/usr/bin/env python3
import setuptools

setuptools.setup(
    name="palgen",
    version="0.0.1",
    author="Tsche",
    author_email="contact@palliate.io",
    description="Code generation utility",
    long_description="Code generation utility",
    long_description_content_type="text/markdown",
    url="https://github.com/palliate/palgen",
    project_urls={
        "Bug Tracker": "https://github.com/palliate/palgen/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    install_requires=["jinja2", "click", "colorama", "toml"],
    entry_points={
        'console_scripts': [
            'palgen=palgen:main'
        ]
    }
)
