"""Non-Interactive CLI."""

from pathlib import Path

from spoofy_archiver.services.api import SpoofyAPISession
from spoofy_archiver.services.archiver import SpoofyArchiver
from spoofy_archiver.services.login import login_cli
from spoofy_archiver.utils import SERVICE_NAME
from spoofy_archiver.utils.logger import get_logger

logger = get_logger(__name__)


def noninteractive(output_directory: Path, delay: int, url: str | None = None) -> None:
    """CLI."""
    session = login_cli()
    if not session:
        logger.error("Failed to login to %s.", SERVICE_NAME)
        return
    logger.info("Logged in as %s", session.username())

    spoofy_api = SpoofyAPISession(session, output_directory=output_directory)
    spoofy_archiver: SpoofyArchiver = SpoofyArchiver(
        session=session,
        output_directory=output_directory,
        download_delay=delay,
    )

    if not url:
        logger.info("No URL provided, downloading liked albums from user.")
        liked_album_list = spoofy_api.get_liked_albums()
        spoofy_archiver.download_albums(liked_album_list)
    else:
        spoofy_archiver.download_url(url)
