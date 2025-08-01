import logging

import pytest


def assert_no_warnings_in_caplog(caplog: pytest.LogCaptureFixture) -> None:
    """Assert that there are no WARNING or above logs in the caplog."""
    warning_records = [record for record in caplog.records if record.levelno >= logging.WARNING]
    nl = "\n  "  # no \n in f string in python 3.11
    assert len(warning_records) == 0, (
        f"{len(warning_records)} warning(s) in log, run with -vvv to see \n  "
        f"{nl.join(record.message for record in warning_records)}"
    )
