"""Constants for Spoofy login service."""

import string
from pathlib import Path

SAVED_CREDENTIALS_FILE = Path.home() / ".config" / "spoofyarchiver" / "credentials.json"
CREDENTIALS_FILE = Path("credentials.json")
SPOTIPY_CACHE_FILE = Path("spotipy.cache")
CLIENT_ID = "".join(
    [
        string.ascii_lowercase[(string.ascii_lowercase.index(c) + 13) % 26] if c in string.ascii_lowercase else c
        for c in "65o708073sp0480rn92n077233pn87oq"
    ]
)
