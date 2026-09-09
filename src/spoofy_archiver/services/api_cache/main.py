"""Spoofy API cache database."""

import datetime
import json
from pathlib import Path

import duckdb

from spoofy_archiver.services.metadata import (
    MetadataAlbum,
    MetadataArtist,
    MetadataTrack,
)
from spoofy_archiver.utils.logger import get_logger

from .models import AlbumCacheSummary

logger = get_logger(__name__)


class SpoofyAPICacheDB:
    """Spoofy API cache database."""

    def __init__(self, db_path: Path) -> None:
        """Initialise the SpoofyAPICacheDB object."""
        if not db_path.exists():
            logger.info("Creating new cache database at: %s", db_path)
        else:
            logger.debug("Using existing cache database at: %s", db_path)

        self.db_path = db_path
        self.conn: duckdb.DuckDBPyConnection = duckdb.connect(str(self.db_path))

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS albums (
                id VARCHAR PRIMARY KEY,
                data JSON
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS artists (
                id VARCHAR PRIMARY KEY,
                data JSON
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tracks (
                id VARCHAR PRIMARY KEY,
                data JSON
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS liked_albums (
                user_id VARCHAR PRIMARY KEY,
                last_updated TIMESTAMP,
                album_list JSON
            )
        """)

    def get_artist_from_id(self, artist_id: str) -> MetadataArtist | None:
        """Get artist from the cache."""
        try:
            artist_info = self.conn.execute("SELECT data FROM artists WHERE id = ?", [artist_id]).fetchone()
            return MetadataArtist(**json.loads(artist_info[0])) if artist_info else None
        except TypeError:
            return None

    def get_album_from_id(self, album_id: str) -> MetadataAlbum | None:
        """Get album from the cache."""
        try:
            album_info = self.conn.execute("SELECT data FROM albums WHERE id = ?", [album_id]).fetchone()
            return MetadataAlbum(**json.loads(album_info[0])) if album_info else None
        except TypeError:
            return None

    def get_track_from_id(self, track_id: str) -> MetadataTrack | None:
        """Get track from the cache."""
        try:
            track_info = self.conn.execute("SELECT data FROM tracks WHERE id = ?", [track_id]).fetchone()
            return MetadataTrack(**json.loads(track_info[0])) if track_info else None
        except TypeError:
            logger.exception("Track ID %s not found in cache", track_id)
            return None

    def get_liked_album_list_from_user_id(self, user_id: str, *, stale_cache_okay: bool = False) -> list[str] | None:
        """Get the list of liked albums from the cache."""
        try:
            liked_album_tuple = self.conn.execute(
                "SELECT album_list, last_updated FROM liked_albums WHERE user_id = ?", [user_id]
            ).fetchone()
            if not liked_album_tuple:
                return None
            liked_albums, last_updated = liked_album_tuple
        except TypeError:
            return None

        if (datetime.datetime.now() - last_updated).total_seconds() / 3600 > 1:
            logger.info("Liked albums cache is over one hour old")
            if not stale_cache_okay:
                return None

        logger.info("Using cached liked albums")
        liked_albums_list: list[str] = json.loads(liked_albums)

        return liked_albums_list

    def insert_replace_album(self, album_id: str, album_info: MetadataAlbum) -> None:
        """Insert an album into the cache."""
        self.conn.execute(
            "INSERT OR REPLACE INTO albums (id, data) VALUES (?, ?)",
            [album_id, album_info.model_dump_json()],
        )

    def insert_replace_artist(self, artist_id: str, artist_info: MetadataArtist) -> None:
        """Insert an artist into the cache."""
        self.conn.execute(
            "INSERT OR REPLACE INTO artists (id, data) VALUES (?, ?)",
            [artist_id, artist_info.model_dump_json()],
        )

    def insert_replace_track(self, track_id: str, track_info: MetadataTrack) -> None:
        """Insert a track into the cache."""
        self.conn.execute(
            "INSERT OR REPLACE INTO tracks (id, data) VALUES (?, ?)",
            [track_id, track_info.model_dump_json()],
        )

    def insert_replace_liked_album_list(self, user_id: str, liked_album_list: list[str]) -> None:
        """Insert a list of liked albums into the cache."""
        self.conn.execute(
            "INSERT OR REPLACE INTO liked_albums (user_id, last_updated, album_list) VALUES (?, ?, ?)",
            [user_id, datetime.datetime.now(), json.dumps(liked_album_list)],
        )

    def delete_liked_album_list(self, user_id: str) -> None:
        """Delete a list of liked albums from the cache."""
        self.conn.execute("DELETE FROM liked_albums WHERE user_id = ?", [user_id])

    def get_liked_album_cache_summary(self) -> list[AlbumCacheSummary]:
        """Get a summary of the album cache."""
        liked_albums_results_nice_list = []

        liked_albums_results = self.conn.execute(
            "SELECT user_id, last_updated, album_list FROM liked_albums"
        ).fetchall()

        for result in liked_albums_results:
            liked_album_list = json.loads(result[2])
            user_id = result[0]
            last_updated = datetime.datetime.strftime(result[1], "%Y-%m-%d %H:%M:%S")
            n_albums = len(liked_album_list)

            first_album_listed = None
            if n_albums != 0:
                first_album_listed_id = liked_album_list[0]
                first_album_listed = self.get_album_from_id(first_album_listed_id)

            first_album_listed_name = "<user has not liked any albums>"
            if first_album_listed:
                first_album_listed_name = first_album_listed.name

            results = AlbumCacheSummary(
                user_id=user_id,
                last_updated=last_updated,
                n_albums=n_albums,
                first_album_listed_name=first_album_listed_name,
            )

            liked_albums_results_nice_list.append(results)

        return liked_albums_results_nice_list
