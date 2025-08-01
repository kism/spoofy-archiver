"""Constants for Spoofy login service."""

from pathlib import Path

SAVED_CREDENTIALS_FILE = Path.home() / ".config" / "spoofyarchiver" / "credentials.json"
ZEROCONF_SESSION_FILE = Path.home() / ".config" / "spoofyarchiver" / "zeroconf_session.json"
CREDENTIALS_FILE = Path("credentials.json")
