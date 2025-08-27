"""Models for Spoofy login service."""

from spoofy_archiver.services.login.constants import CREDENTIALS_FILE, SPOTIPY_CACHE_FILE
from spoofy_archiver.utils import SERVICE_NAME


class SpoofyLoginError(Exception):
    """Spoofy login error."""

    def __init__(self, msg: str | None = None) -> None:
        """Initialise the SpoofyLoginError."""
        if not msg:
            msg = f"Failed to login to {SERVICE_NAME}"

        if CREDENTIALS_FILE.exists():
            CREDENTIALS_FILE.unlink()
        if SPOTIPY_CACHE_FILE.exists():
            SPOTIPY_CACHE_FILE.unlink()

        super().__init__(msg)
