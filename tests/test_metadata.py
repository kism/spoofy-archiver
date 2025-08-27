"""Tests for the metadata module."""

import json
from pathlib import Path
from typing import Any

import pytest

from spoofy_archiver.services.metadata import MetadataAlbum, MetadataArtist, MetadataTrack


@pytest.fixture
def test_data_dir() -> Path:
    """Return the path to the test data directory."""
    # Assuming test_api_results folder is in the same directory as the tests
    return Path(__file__).parent / "test_api_results"


@pytest.fixture
def artist_data(test_data_dir: Path) -> Any:
    """Load artist test data from JSON file."""
    with (test_data_dir / "artist.json").open() as file:
        return json.load(file)


@pytest.fixture
def album_data(test_data_dir: Path) -> Any:
    """Load album test data from JSON file."""
    with (test_data_dir / "album.json").open() as file:
        return json.load(file)


@pytest.fixture
def track_data(test_data_dir: Path) -> Any:
    """Load track test data from JSON file."""
    with (test_data_dir / "track.json").open() as file:
        return json.load(file)


class TestMetadataArtist:
    """Test the MetadataArtist class."""

    def test_init(self, artist_data: Any) -> None:
        """Test the initialization of a MetadataArtist object."""
        MetadataArtist(**artist_data)


class TestMetadataAlbum:
    """Test the MetadataAlbum class."""

    def test_init(self, album_data: Any) -> None:
        """Test the initialization of a MetadataAlbum object."""
        MetadataAlbum(**album_data)


class TestMetadataTrack:
    """Test the MetadataTrack class."""

    def test_init(self, track_data: Any) -> None:
        """Test the initialization of a MetadataTrack object."""
        try:
            MetadataTrack(**track_data)
        except Exception as e:
            pytest.fail(repr(e))
