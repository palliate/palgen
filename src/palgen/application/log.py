""" Palgen logging helpers """

import logging
import sys

import colorama


class LogFormatter(logging.Formatter):
    """Custom log formatter"""

    __slots__ = ('formatters',)

    colors = {
        logging.DEBUG:    "\033[36m",
        logging.INFO:     "\033[32m",
        logging.WARNING:  "\033[33m",
        logging.ERROR:    "\033[31m",
        logging.CRITICAL: "\033[1m\033[31m",
    }

    time_fmt = "%Y-%m-%d %H:%M:%S"

    @staticmethod
    def get_format(color: str) -> str:
        """Returns a format string with the appropriate color.

        Args:
            color (str): ANSI escape code

        Returns:
            str: fmt string
        """

        reset = "\033[0m"
        return f"(%(asctime)s) {color}%(brace_l)s%(filename)s:%(lineno)d%(brace_r)s: %(message)s{reset}"

    def __init__(self):
        super().__init__()

        self.formatters = {
            level: logging.Formatter(self.get_format(color), self.time_fmt)
            for level, color in LogFormatter.colors.items()
        }

    def format(self, record: logging.LogRecord) -> str:
        builtin = record.name != 'root'
        record.brace_l = '[' if builtin else '('
        record.brace_r = ']' if builtin else ')'
        formatter = self.formatters.get(record.levelno)
        assert formatter
        return formatter.format(record)


def setup_logger() -> None:
    """Enables this custom logger globally."""
    colorama.init()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(LogFormatter())

    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
    logging.root.addHandler(handler)

    sys.excepthook = handle_exception


def set_min_level(level: int):
    """Disables output of messages below the given level

    Args:
        level (int): log level #TODO copy description from palliate
    """
    logging.root.setLevel((1 + level) * 10)


def handle_exception(type_, value, trace):
    """Global exception handler.
    Prints uncaught exceptions with the custom formatter.

    Args:
        type_: Exception type
        value: Exception value
        trace: Exception trace
    """
    logger = logging.getLogger(__package__)

    if logger.isEnabledFor(logging.DEBUG):
        logger.exception("Exception occurred: ", exc_info=(type_, value, trace))
    else:
        logger.critical("Exception occurred: %s %s", type_.__name__, value)

    raise SystemExit(1)
