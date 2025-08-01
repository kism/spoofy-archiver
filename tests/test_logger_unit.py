"""Logger unit tests."""

import logging
import random
from collections.abc import Generator
from typing import TYPE_CHECKING

import pytest

from spoofyarchiver.utils.logger import (
    TRACE_LEVEL_NUM,
    CustomLogger,
    _set_log_level,
    get_logger,
    setup_logger,
)
from tests.helpers import assert_no_warnings_in_caplog

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
else:
    MockerFixture = object


@pytest.fixture
def logger() -> Generator[CustomLogger]:
    """Logger to use in unit tests, including cleanup."""
    random_str = str(random.randint(1, 99999))  # Avoid conflicts? this runs weird

    logger_raw = logging.getLogger(f"TEST_LOGGER_{random_str}")
    assert len(logger_raw.handlers) == 0  # Check the logger has no handlers

    setup_logger(
        log_level=logging.DEBUG,
        in_logger=logger_raw,
    )
    logger = get_logger(logger_raw.name)

    yield logger

    # Reset the test object since it will persist.
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()


def test_handler_console_added(logger: logging.Logger) -> None:
    """Test logging console handler."""
    log_level = "INFO"

    # TEST: Only one handler (console), should exist when no logging path provided
    setup_logger(log_level=log_level, in_logger=logger)
    assert len(logger.handlers) == 1

    # TEST: If a console handler exists, another one shouldn't be created
    setup_logger(log_level=log_level, in_logger=logger)
    assert len(logger.handlers) == 1


@pytest.mark.parametrize(
    ("log_level_in", "log_level_expected"),
    [
        (50, 50),
        ("INFO", 20),
        ("WARNING", 30),
        ("INVALID", 20),
        ("TRACE", TRACE_LEVEL_NUM),
    ],
)
def test_set_log_level(log_level_in: str | int, log_level_expected: int, logger: logging.Logger) -> None:
    """Test if _set_log_level results in correct log_level."""
    _set_log_level(logger, log_level_in)
    assert logger.getEffectiveLevel() == log_level_expected


def test_trace_level(logger: CustomLogger, caplog: pytest.LogCaptureFixture) -> None:
    """Test trace level."""

    _set_log_level(logger, "TRACE")

    assert logger.getEffectiveLevel() == TRACE_LEVEL_NUM

    with caplog.at_level(TRACE_LEVEL_NUM):
        logger.trace("Test trace")

    assert "Test trace" in caplog.text
    assert_no_warnings_in_caplog(caplog)


def test_logging_types(logger: CustomLogger, caplog: pytest.LogCaptureFixture) -> None:
    """Test trace level."""

    with caplog.at_level(logging.INFO):
        logger.info(("tuple1", "tuple2"))
        logger.info(["list1", "list2"])
        logger.info({"dict_key": "dict_value"})
        logger.info(1)

    assert "(tuple1 tuple2)" in caplog.text
    assert "[list1 list2]" in caplog.text
    assert "{'dict_key': 'dict_value'}" in caplog.text
    assert "1" in caplog.text
    assert_no_warnings_in_caplog(caplog)
