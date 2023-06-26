# Contributing

Thank you for considering contributing to palgen! We welcome contributions from the community to help improve and enhance the project. This document outlines the guidelines and instructions for contributing to palgen.

## Table of Contents

- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Issues](#reporting-issues)
  - [Submitting Pull Requests](#submitting-pull-requests)
- [Development Setup](#development-setup)
- [Style Guidelines](#style-guidelines)
- [License](#license)

## How Can I Contribute?

There are several ways you can contribute to palgen:

### Reporting Issues

If you encounter any bugs, issues, or have suggestions for improvements, please [open an issue](https://github.com/palliate/palgen/issues). When reporting an issue, please provide as much detail as possible, including steps to reproduce, expected behavior, and actual behavior. This helps us understand and address the problem effectively.

### Submitting Pull Requests

If you have a bug fix, enhancement, or new feature that you would like to contribute, you can submit a pull request (PR). Here are the general steps to follow:

1. Fork the repository to your GitHub account.
2. Clone the forked repository to your local machine.
3. Create a new branch for your changes.
4. Make the necessary code changes and additions.
5. Commit your changes with clear and descriptive commit messages.
6. Push your branch to your forked repository on GitHub.
7. Open a pull request against the main repository's `master` branch.

We appreciate well-documented and concise pull requests. Please ensure that your code adheres to the style guidelines mentioned in the next section.

Once your pull request is submitted, it will be reviewed by the project maintainers. We may provide feedback or ask for additional changes before merging it.

## Development Setup

To set up a development environment for palgen, follow these steps:

1. Fork the repository to your GitHub account.
2. Clone the forked repository to your local machine.
3. Create a virtual environment using Python 3.10 or above.
4. Install the required dependencies by running `pip install -r requirements.txt -r requirements_dev.txt`.
5. You can now start making changes to the codebase.

It's usually recommended to install the package in editable mode when developing. This can be done by running `pip install -e .` in the repository's root folder.

## Style Guidelines

We follow the recommended style guidelines to maintain a consistent and readable codebase. Please ensure that your code adheres to the following:

- Use the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code.
- Use meaningful variable and function names.
- Write clear and concise comments to explain the intent and logic of the code. Try not to repeat what your code does in natural language.
- Add docstrings to classes, methods, and functions to provide necessary documentation. Palgen uses Google style docstrings.
- Write unit tests for new features and ensure existing tests pass.

## License

By contributing to palgen, you agree that your contributions will be licensed under the [MIT License](LICENSE). This allows the project to be distributed under an open-source license while protecting contributors and users from liability.

---

Thank you for your interest in contributing to palgen! Your contributions help make the project better and benefit the entire community.