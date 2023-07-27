# Palgen

[![PyPI](https://img.shields.io/pypi/v/palgen.svg)](https://pypi.org/project/palgen/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/your_username/palgen/blob/main/LICENSE)
[![Documentation](https://img.shields.io/badge/Documentation-palgen.palliate.io-brightgreen)](https://palgen.palliate.io)

Palgen is a powerful and modular command line tool aiming to simplify writing various common utilities such as build scripts, code generators and preprocessors. Palgen provides an easy-to-use interface for creating command line applications by automatically generating command line interfaces (CLIs) from pydantic schemas. This allows for file-based configurations and setting validation.

## Features

- Easily extendible. Once your user provided class inherits from palgen's `Extension` interface it will be recoginized as extension and become runnable.
- Automatic generation of command line interfaces.
- Settings validation using pydantic.
- Easy migration from existing Python projects.
- Easy-to-use ingest pipelines for processing data.
- Automatic parallelization of extension pipelines unless disabled.
- Comprehensive documentation available at [palgen.palliate.io](https://palgen.palliate.io).

## Installation

Palgen can be installed via pip:

```shell
pip install git+https://github.com/palliate/palgen.git@master
```

For now it is necessary to pull it from git directly. A proper release will soon follow.


## Documentation

The detailed documentation for palgen can be found at [palgen.palliate.io](https://palgen.palliate.io). It includes guides, examples, and API reference documentation to help you get started and make the most out of palgen.

## Examples

Check out the [examples](https://github.com/palliate/palgen/tree/master/examples) subfolder in the repository for various usage examples for palgen.

Palgen itself uses palgen to generate parts of its documentation. You can check out those more complex extensions in the [docs/modules](https://github.com/palliate/palgen/tree/master/docs/modules) subfolder. Since this project is part of the [palliate](https://palliate.io) project you may find additional usage examples in the other repositories within the [palliate organization](https://github.com/palliate).

## Contributing

Contributions to palgen are very welcome! If you find any issues or have suggestions for improvements, please open an issue on the [GitHub repository](https://github.com/palliate/palgen). You can also submit pull requests with bug fixes or new features.

Before making a contribution, please ensure that you have read and understood the [Contributing Guidelines](https://github.com/palliate/palgen/blob/main/CONTRIBUTING.md).

## Community and Support

Join the palliate Discord server to connect with the community and get support for palgen and other palliate projects. [Join here](https://discord.palliate.io).

## License

Palgen is licensed under the MIT License. See the [LICENSE](https://github.com/palliate/palgen/blob/master/LICENSE) file for more details.

