import logging
import sys


class LogFormatter(logging.Formatter):
    debug = "\033[36m"
    info = "\033[32m"
    warning = "\033[33m"
    error = "\033[31m"
    fatal = "\033[1m\033[31m"
    reset = "\033[0m"

    format = "(%(asctime)s) "
    time_format = "%Y-%m-%d %H:%M:%S"
    FORMATS = {
        logging.DEBUG:    logging.Formatter(format + debug + "%(message)s" + reset, time_format),
        logging.INFO:     logging.Formatter(format + info + "%(message)s" + reset, time_format),
        logging.WARNING:  logging.Formatter(format + warning + "%(message)s" + reset, time_format),
        logging.ERROR:    logging.Formatter(format + error + "%(message)s" + reset, time_format),
        logging.CRITICAL: logging.Formatter(
            format + fatal + "%(message)s" + reset, time_format)
    }

    def format(self, record):
        formatter = self.FORMATS.get(record.levelno)
        return formatter.format(record)


def set_min_level(level):
    # Convert from palliate log levels to python logging loglevels
    logger.setLevel((1 + level) * 10)


logger = logging.getLogger('codegen')
logger.setLevel(logging.INFO)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
ch.setFormatter(LogFormatter())
logger.addHandler(ch)
