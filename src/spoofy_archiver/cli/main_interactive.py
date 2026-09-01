"""Main CLI for Entry Point."""

from pathlib import Path
from typing import TYPE_CHECKING

from spoofy_archiver.services.api import SpoofyAPISession
from spoofy_archiver.services.archiver import SpoofyArchiver
from spoofy_archiver.services.login import login_cli_interactive
from spoofy_archiver.utils import SERVICE_NAME, cli_print_heading
from spoofy_archiver.utils.logger import get_logger

if TYPE_CHECKING:
    from librespot.core import Session


logger = get_logger(__name__)

MAIN_MENU_PROMPT = """Select an option:
 dla: Download liked albums
 fla: Fetch liked albums
 mla: Migrate liked albums (from other account, must be cached)
 q: quit

> """


def _nice_input(prompt: str) -> str:
    """Nice input."""
    try:
        return input(prompt).strip().lower()
    except KeyboardInterrupt:
        return "q"


def interactive(output_directory: Path, delay: int) -> None:
    """Main."""
    cli_print_heading(f"{SERVICE_NAME} Archiver Interactive CLI")
    if not output_directory.is_dir():
        _nice_input("Target directory does not exist. Press enter to create it.")
        output_directory.mkdir()

    cli_print_heading(f"Logging in to {SERVICE_NAME}")
    session: Session = login_cli_interactive()
    logger.info("Logged in as %s", session.username())
    spoofy_api = SpoofyAPISession(session, output_directory=output_directory)
    spoofy_archiver: SpoofyArchiver = SpoofyArchiver(
        session=session,
        output_directory=output_directory,
        download_delay=delay,
    )

    user_input = ""
    while user_input != "q":  # spell-checker: disable-next-line
        cli_print_heading("Main CLI Menu")
        user_input = _nice_input(MAIN_MENU_PROMPT)

        if user_input in ("fla", "dla"):
            cli_print_heading("Fetching liked albums for current user")
            liked_album_list = spoofy_api.get_liked_albums()  # Actual

            if user_input == "dla":
                cli_print_heading("Downloading Albums")
                spoofy_archiver.download_albums(liked_album_list)

            if user_input == "fla":
                spoofy_api.print_liked_albums()

        if user_input == "mla":
            spoofy_archiver.print_liked_album_cache_summary()

            user_to_migrate_from = _nice_input("Enter user ID to migrate from: ")
            liked_album_list_tmp = spoofy_archiver.get_liked_album_cache(user_to_migrate_from)
            if liked_album_list_tmp:
                liked_album_list = liked_album_list_tmp
            else:
                logger.error("User not found in cache")
                continue

            if liked_album_list == []:
                logger.error("No liked albums found in cache")
                continue

            cli_print_heading("Updating liked albums for current user")
            spoofy_api.like_album_list(liked_album_list)
