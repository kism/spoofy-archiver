"""The conftest.py file serves as a means of providing fixtures for an entire directory.

Fixtures defined in a conftest.py can be used by any test in that package without needing to import them.
"""

from pathlib import Path

import pytest

from spoofyarchiver.services.api.main import SpoofyAPISession


@pytest.fixture
def my_cool_object(tmp_path: Path) -> SpoofyAPISession:
    """Fixture for MyCoolObject."""
    return SpoofyAPISession("Hello, World!", tmp_path / "output_directory")
