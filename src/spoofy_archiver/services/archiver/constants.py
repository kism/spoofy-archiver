"""Constants for the archiver service."""

import string

DOWNLOAD_URL = "".join(
    [
        string.ascii_lowercase[(string.ascii_lowercase.index(c) + 13) % 26] if c in string.ascii_lowercase else c
        for c in "uggcf://bcra.fcbgvsl.pbz"
    ]
)
