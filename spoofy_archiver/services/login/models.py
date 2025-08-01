"""Models for Spoofy login service."""

from spoofy_archiver.utils import SERVICE_NAME


class SpoofyLoginError(Exception):
    """Spoofy login error."""

    def __init__(self, msg: str | None = None) -> None:
        """Initialise the SpoofyLoginError."""
        if not msg:
            msg = f"Failed to login to {SERVICE_NAME}"
        super().__init__(msg)
