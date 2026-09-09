"""Helper functions for the Spoofy API service."""

import string

API_URL = "".join(
    [
        string.ascii_lowercase[(string.ascii_lowercase.index(c) + 13) % 26] if c in string.ascii_lowercase else c
        for c in "uggcf://ncv.fcbgvsl.pbz/i1"
    ]
)
