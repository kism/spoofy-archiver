"""Setup the logger functionality."""

import logging
import typing
from typing import cast

from colorama import Fore, init

init(autoreset=True)

COLOURS = {
    "TRACE": Fore.CYAN,
    "DEBUG": Fore.GREEN,
    "INFO": Fore.WHITE,
    "WARNING": Fore.YELLOW,
    "ERROR": Fore.RED,
    "CRITICAL": Fore.RED,
}


class ColourFormatter(logging.Formatter):
    """Custom formatter to add colour to the log messages."""

    def _format_value(self, value: typing.Any) -> str:  # noqa: ANN401
        if isinstance(value, tuple):
            return "(" + " ".join(map(str, value)) + ")"
        if isinstance(value, list):
            return "[" + " ".join(map(str, value)) + "]"
        return str(value) if value is not None else "<NoneType>"

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record."""
        record.msg = self._format_value(record.msg)

        if record.levelno == logging.INFO:
            return f"{record.getMessage()}"

        if colour := COLOURS.get(record.levelname):
            record.name = f"{colour}{record.name}"
            record.levelname = f"{colour}{record.levelname}"
            record.msg = f"{colour}{record.msg}"

        return super().format(record)


LOG_LEVELS = [
    "TRACE",
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
]  # Valid str logging levels.

# This is the logging message format that I like.
LOG_FORMAT = "%(levelname)s:%(name)s:%(message)s"
TRACE_LEVEL_NUM = 5


class CustomLogger(logging.Logger):
    """Custom logger to appease mypy."""

    def trace(self, message: typing.Any, *args: typing.Any, **kwargs: typing.Any) -> None:  # noqa: ANN401 Typing.any required for logging
        """Create logger level for trace."""
        if self.isEnabledFor(TRACE_LEVEL_NUM):
            # Yes, logger takes its '*args' as 'args'.
            self._log(TRACE_LEVEL_NUM, message, args, **kwargs)


logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")
logging.setLoggerClass(CustomLogger)

# This is where we log to in this module, following the standard of every module.
# I don't use the function so we can have this at the top
logger = cast("CustomLogger", logging.getLogger(__name__))


# Pass in the whole app object to make it obvious we are configuring the logger object within the app object.
def setup_logger(
    log_level: str | int = logging.INFO,
    in_logger: logging.Logger | None = None,
) -> None:
    """Setup the logger, set configuration per logging_conf.

    Args:
        log_level: Logging level to set.
        log_path: Path to log to.
        in_logger: Logger to configure, useful for testing.
    """
    if not in_logger:  # in_logger should only exist when testing with PyTest.
        in_logger = logging.getLogger()  # pragma: no cover

    # If the logger doesn't have a console handler (root logger doesn't by default)
    if not _has_console_handler(in_logger):
        _add_console_handler(in_logger)

    _set_log_level(in_logger, log_level)

    loggers_to_silence = ["urllib3", "Librespot:Session"]

    for logger_name in loggers_to_silence:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    logger.debug("Logger configuration set!")


def get_logger(name: str) -> CustomLogger:
    """Get a logger with the name provided."""
    return cast("CustomLogger", logging.getLogger(name))


def _has_file_handler(in_logger: logging.Logger) -> bool:
    """Check if logger has a file handler."""
    return any(isinstance(handler, logging.FileHandler) for handler in in_logger.handlers)


def _has_console_handler(in_logger: logging.Logger) -> bool:
    """Check if logger has a console handler."""
    return any(isinstance(handler, logging.StreamHandler) for handler in in_logger.handlers)


def _set_log_level(in_logger: logging.Logger, log_level: int | str) -> None:
    """Set the log level of the logger."""
    if isinstance(log_level, str):
        log_level = log_level.upper()
        if log_level not in LOG_LEVELS:
            in_logger.setLevel("INFO")
            logger.warning(
                "❗ Invalid logging level: %s, defaulting to INFO",
                log_level,
            )
        else:
            in_logger.setLevel(log_level)
            logger.trace("Set log level: %s", log_level)
            logger.debug("Set log level: %s", log_level)
    else:
        in_logger.setLevel(log_level)


def _add_console_handler(in_logger: logging.Logger) -> None:
    """Add a console handler to the logger."""
    formatter = ColourFormatter(LOG_FORMAT)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    in_logger.addHandler(console_handler)
