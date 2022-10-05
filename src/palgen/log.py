''' Palgen logging helpers '''

import logging
import sys


class LogFormatter(logging.Formatter):
    """Custom log formatter
    """

    colors = {
        logging.DEBUG:    "\033[36m",
        logging.INFO:     "\033[32m",
        logging.WARNING:  "\033[33m",
        logging.ERROR:    "\033[31m",
        logging.CRITICAL: "\033[1m\033[31m"
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
        return f"(%(asctime)s) {color}[%(filename)s:%(lineno)d]: %(message)s{reset}"

    def __init__(self):
        super().__init__()

        self.formatters = {
            level: logging.Formatter(self.get_format(color), self.time_fmt)
            for level, color
            in LogFormatter.colors.items()
        }

    def format(self, record: logging.LogRecord) -> str:
        formatter = self.formatters.get(record.levelno)
        return formatter.format(record)


def setup_logger() -> None:
    """Enables this custom logger globally.
    """

    logger = logging.getLogger(__package__)
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(LogFormatter())
    logger.addHandler(handler)


def set_min_level(level: int):
    """Disables output of messages below the given level

    Args:
        level (int): log level #TODO copy description from palliate
    """
    logging.getLogger(__package__).setLevel((1 + level) * 10)
