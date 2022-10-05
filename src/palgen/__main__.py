#!/usr/bin/env python3
''' Allow running palgen as module: `python -m palgen` '''

from colorama import init
from . import main

init()


if __name__ == "__main__":
    # Disable missing parameter warning - these are handled by click
    # pylint: disable=no-value-for-parameter
    main()
