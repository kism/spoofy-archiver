"""Download Delayer Module."""

import random
import sys
import time

from .helpers import cli_newline
from .logger import get_logger

logger = get_logger(__name__)


class DownloadDelayer:
    """Manages download delays with configurable base delay and randomization."""

    def __init__(self, base_delay: int = 30) -> None:
        """Initialize the download delayer.

        Args:
            base_delay: Base delay in seconds between downloads
        """
        self.base_delay = base_delay

    def delay(self, additional_delay: int = 0) -> None:
        """Apply a delay with randomization.

        Args:
            additional_delay: Additional delay in seconds to add to the base delay
        """
        delay_base = self.base_delay + additional_delay
        if delay_base > 0:
            random_offset = max(delay_base // 8, 5)  # Additional can be +/- 1/8th of the base delay, minimum 5 seconds
            delay = random.randint(delay_base, delay_base + random_offset)  # noqa: S311, This is not for cryptography
            delay = max(delay, 0)
            logger.info("Delaying download for %d seconds...", delay)
            try:
                time.sleep(delay)
            except KeyboardInterrupt:
                logger.info("...Exiting cleanly")
                sys.exit(1)
        cli_newline()

    def delay_short(self) -> None:
        """Apply a short delay, mostly for showing tqdm after a download."""
        if self.base_delay > 0:
            time.sleep(0.5)
