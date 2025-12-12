"""Test versioning."""

import tomllib
from pathlib import Path

import spoofy_archiver


def test_version_pyproject() -> None:
    """Verify version in pyproject.toml matches package version."""
    pyproject_path = Path("pyproject.toml")
    with pyproject_path.open("rb") as f:
        pyproject_toml = tomllib.load(f)
    assert pyproject_toml.get("project", {}).get("version") == spoofy_archiver.__version__, (
        "Version in pyproject.toml does not match package version."
    )


def test_version_lock() -> None:
    """Verify version in uv.lock matches package version."""
    lock_path = Path("uv.lock")
    with lock_path.open("rb") as f:
        uv_lock = tomllib.load(f)

    found_version = False
    for package in uv_lock.get("package", []):
        if package["name"] == "spoofy-archiver":
            assert package["version"] == spoofy_archiver.__version__
            found_version = True
            break

    assert found_version, "spoofy-archiver not found in uv.lock"
