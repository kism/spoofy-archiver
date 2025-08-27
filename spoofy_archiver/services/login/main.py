"""Spoofy login related functions."""

import sys
from pathlib import Path

from librespot.core import Session

from spoofy_archiver.utils import get_logger

from .authentication import (
    get_librespot_rs_credentials,
    login_oauth,
    login_saved_session,
    login_user_pass,
    login_zeroconf,
)

logger = get_logger(__name__)


SAVED_CREDENTIALS_FILE = Path.home() / ".config" / "spoofyarchiver" / "credentials.json"

CREDENTIALS_FILE = Path("credentials.json")


def login_cli_interactive() -> Session:
    """Login to Spoofy and return a session."""
    session = login_saved_session()
    if session:
        return session

    logger.info("Saved credentials not found, prompting...")
    logger.info("Oauth is the best method, librespot-rs works, the rest I haven't had work.")

    user_input = ""
    while True:
        try:
            user_input = input(  # spell-checker: disable-next-line
                "Login with [u]sername and password, [o]auth, [z]eroconf, librespot-[r]s or [q]uit: "
            ).lower()
        except KeyboardInterrupt:
            user_input = "q"
        if user_input[0] == "u":
            session = login_user_pass()
        if user_input[0] == "z":
            session = login_zeroconf()
        if user_input[0] == "o":
            session = login_oauth()
        if user_input[0] == "r":
            session = get_librespot_rs_credentials()
        if user_input[0] == "q":
            sys.exit(0)

        if session:
            return session

        logger.error("Login failed, try again.")


def login_cli() -> Session | None:
    """Login to Spoofy using the CLI, non-interactively."""
    session = login_saved_session()
    if session:
        return session

    return login_oauth()
