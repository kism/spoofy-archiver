"""Authentication functions for Spoofy Archiver."""

import base64
import json
import os
import time
from pathlib import Path

import spotipy
from dotenv import load_dotenv
from librespot.core import Session
from librespot.mercury import MercuryClient
from librespot.zeroconf import ZeroconfServer
from spotipy.oauth2 import SpotifyPKCE

from spoofy_archiver.utils import SERVICE_NAME, get_logger

from .constants import CLIENT_ID, CREDENTIALS_FILE, SAVED_CREDENTIALS_FILE
from .models import SpoofyLoginError

logger = get_logger(__name__)

SERVICE_NAME_UPPER = SERVICE_NAME.upper()


def login_oauth() -> Session | None:
    """Login to Spoofy using OAuth."""
    # https://github.com/spotipy-dev/spotipy
    scopes = [
        "playlist-read",
        "playlist-read-collaborative",
        "playlist-read-private",
        "playlist-modify-private",
        "playlist-modify-public",
        "streaming",
        "user-follow-modify",
        "user-follow-read",
        "user-library-modify",
        "user-library-read",
        "user-top-read",
    ]

    load_dotenv()

    client_id = os.environ.get("SPOTIPY_CLIENT_ID")
    redirect_uri = os.environ.get("SPOTIPY_REDIRECT_URI")

    if not client_id or not redirect_uri:
        logger.info(
            "No client_id or redirect_uri found in environment variables, using desktop client id, you may get throttled."  # noqa: E501
        )
        client_id = CLIENT_ID
        redirect_uri = "http://127.0.0.1:8898/login"
    else:
        logger.info("Using custom client as defined in environment variables.")

    spotipy_cache_path = Path("spotipy.cache")
    auth_manager = SpotifyPKCE(
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=" ".join(scopes),
        cache_path=spotipy_cache_path,
    )

    sp = spotipy.Spotify(auth_manager=auth_manager)

    logger.info("Logging in with OAuth...")
    credentials = auth_manager.get_access_token()
    credentials_b64 = base64.b64encode(credentials.encode()).decode()
    user_name = sp.me()["id"]
    logger.info("Logged in as: %s", user_name)

    saved_credentials = {
        "username": user_name,
        "credentials": credentials_b64,
        "type": f"AUTHENTICATION_{SERVICE_NAME_UPPER}_TOKEN",
        "source": "oauth",
    }

    with CREDENTIALS_FILE.open("w") as f:
        json.dump(saved_credentials, f, indent=4)

    # This is a hack, first time gets a 403 but the library converts the credentials to something usable.
    logger.info("Getting session, there may be Mercury exceptions")

    session = login_saved_session()
    spotipy_cache_path.unlink()  # We don't need this once we have the real credentials.json file.
    return session


def saved_credential_get() -> None:
    """Due to librespot not being able to handle credentials.json being elsewhere, we copy it to the current dir."""
    if CREDENTIALS_FILE.is_file():
        logger.debug("Credentials found in current dir.")
    elif SAVED_CREDENTIALS_FILE.is_file():
        logger.debug("Credentials found %s", SAVED_CREDENTIALS_FILE)
        with SAVED_CREDENTIALS_FILE.open() as f:
            data = json.load(f)

        with CREDENTIALS_FILE.open("w") as f:  # This has to be the file we use for login.
            json.dump(data, f, indent=4)


def saved_credential_save() -> None:
    """Save the credentials in current dir to home dir."""
    if not CREDENTIALS_FILE.is_file():
        logger.warning("No credentials file in current dir to save.")
    else:
        logger.debug("Saving credentials file to home dir.")
        with CREDENTIALS_FILE.open() as f:
            data = json.load(f)

        SAVED_CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)

        with SAVED_CREDENTIALS_FILE.open("w") as f:
            json.dump(data, f, indent=4)

        CREDENTIALS_FILE.unlink()


def login_saved_session() -> Session | None:
    """Login to Spoofy using saved credentials."""
    login_retries = 3

    saved_credential_get()

    if CREDENTIALS_FILE.is_file():  # This is always the file we use for login.
        logger.info("Found credentials.json, using saved credentials")
        for _ in range(login_retries):
            try:
                session = Session.Builder().stored_file().create()  # Doesn't handle credentials.json being elsewhere?
                saved_credential_save()
                return session  # noqa: TRY300, this is fine
            except ConnectionRefusedError:
                pass
            except MercuryClient.MercuryException as e:
                logger.warning("Non-fatal Mercury exception: %s", e)
            except Session.SpotifyAuthenticationException as e:
                logger.exception("Failed to login to %s", SERVICE_NAME)
                msg = "Remove credentials.json and log in again."
                raise SpoofyLoginError(msg) from e
            except Exception as e:
                logger.exception("Unhandled %s login error", SERVICE_NAME)
                raise SpoofyLoginError from e

            logger.info("Trying to connect to %s", SERVICE_NAME)
            time.sleep(1)

        raise SpoofyLoginError

    return None


def get_librespot_rs_credentials() -> Session | None:
    """Get the credentials from librespot-rs."""
    librespot_credentials_path = Path.home() / ".config" / "librespot" / "credentials.json"

    if not librespot_credentials_path.exists():
        msg = f"No librespot credentials found at: {librespot_credentials_path}"
        raise SpoofyLoginError(msg)

    logger.info("Found librespot (rust) credentials at: %s, copying those.", librespot_credentials_path)

    with librespot_credentials_path.open() as f:
        data = json.load(f)
        new_data = {
            "username": data["username"],
            "credentials": data["auth_data"],
            "type": data["type"],
            "source": "librespot-rs",
        }

    with CREDENTIALS_FILE.open() as f:
        json.dump(new_data, f, indent=4)

    return login_saved_session()


def login_user_pass(user_name: str = "", password: str = "") -> Session:
    """Login to Spoofy using username and password. I don't think this works."""
    logger.info("Prompting for username and password, this has never worked for me.")

    if not user_name:
        user_name = input("Username: ")

    if not password:
        password = input("Password: ")

    return Session.Builder().user_pass(user_name, password).create()


def login_zeroconf() -> Session | None:
    """Login to Spoofy using zeroconf."""
    zeroconf = ZeroconfServer.Builder().create()

    while not zeroconf.has_valid_session():
        time.sleep(1)

    return login_saved_session()
