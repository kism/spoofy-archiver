"""Helper Functions for Spoofy Archiver."""

from .logger import get_logger

logger = get_logger(__name__)


def cli_print_heading(heading: str) -> None:
    """Print a heading."""
    print(f"\n--- {heading} ---")  # noqa: T201


def cli_newline() -> None:
    """Print a newline."""
    print()  # noqa: T201


def replace_slashes(input_str: str) -> str:
    """Replace forward slashes with underscores."""
    input_str = input_str.replace("/", "／")  # noqa: RUF001
    input_str = input_str.replace("\\", "＼")  # noqa: RUF001
    return input_str  # noqa: RET504
