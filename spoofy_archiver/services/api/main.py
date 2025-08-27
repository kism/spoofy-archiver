"""Spoofy API related Objects and functions."""

import json
from pathlib import Path

import requests
from librespot.core import Session

from spoofy_archiver.services.api_cache import SpoofyAPICacheDB
from spoofy_archiver.services.metadata import (
    AlbumListResult,
    MetadataAlbum,
    MetadataArtist,
    MetadataPlaylist,
    MetadataTrack,
    MetadataTrackList,
)
from spoofy_archiver.utils import cli_newline, get_logger

from .constants import API_URL

logger = get_logger(__name__)


class SpoofyAPISession:
    """Spoofy API session object, caches API responses in a DuckDB cache_db."""

    def __init__(self, session: Session, output_directory: str | Path) -> None:
        """Initialise the SpoofyAPISession object."""
        self.session = session
        if isinstance(output_directory, str):
            output_directory = Path(output_directory)

        output_directory.mkdir(parents=True, exist_ok=True)
        self.cache_db = SpoofyAPICacheDB(output_directory / "spoofy-archiver_api_cache.duckdb")

    def get_playlist_tracks(self, playlist_id: str) -> list[str]:
        """Get the tracks from a playlist."""
        playlist_api = f"{API_URL}/playlists/{playlist_id}/tracks"
        bearer_token = self.session.tokens().get("playlist-read-private")
        headers = {"Authorization": f"Bearer {bearer_token}"}

        request = requests.get(playlist_api, headers=headers, timeout=5)
        playlist_info = MetadataTrackList(**json.loads(request.content))

        tracks = []
        for track in playlist_info.items:
            track_id = track.id
            tracks.append(track_id)

        return tracks

    def get_liked_albums(self) -> list[str]:
        """Get the liked albums from the user's Spoofy account."""
        user = self.session.username()
        logger.info("Fetching liked albums for user: %s", user)
        cached_liked_album_list = self.cache_db.get_liked_album_list_from_user_id(user)

        if cached_liked_album_list:
            return cached_liked_album_list

        liked_album_list = []
        self.cache_db.delete_liked_album_list(self.session.username())

        my_liked_albums_api = f"{API_URL}/me/albums?limit=50"
        logger.debug("Fetching album info")
        while True:  # We need to go through pages
            bearer_token = self.session.tokens().get("user-library-read")
            headers = {"Authorization": f"Bearer {bearer_token}"}

            response = requests.get(my_liked_albums_api, headers=headers, timeout=5)
            response.raise_for_status()  # Ensure we handle HTTP errors

            my_liked_albums_info = AlbumListResult(**json.loads(response.content))

            for liked_album in my_liked_albums_info.items:
                album_id = liked_album.album.id

                # Update the cache, and avoid having to use album['album'] everywhere, maybe this gets more info too
                album_complete = self.get_album_from_id(album_id)

                primary_artist_id = album_complete.get_first_artist_id()

                liked_album_list.append(album_id)

                self.get_artist_from_id(primary_artist_id)  # Update the cache

                progress_str = "\rFetched album info: " + str(len(liked_album_list))
                print(progress_str, end="", flush=True)  # noqa: T201 # Progress indicator

            if not my_liked_albums_info.next:
                break

            my_liked_albums_api = my_liked_albums_info.next + "&limit=50"

        self.cache_db.insert_replace_liked_album_list(
            user_id=self.session.username(),
            liked_album_list=liked_album_list,
        )

        print(", Done!")  # noqa: T201 # Progress indicator

        return liked_album_list

    def get_album_from_id(self, album_id: str) -> MetadataAlbum:
        """Get the album information from the album ID."""
        album_cache = self.cache_db.get_album_from_id(album_id)
        if album_cache:
            return album_cache

        album_api = f"{API_URL}/albums/{album_id}"
        bearer_token = self.session.tokens().get("user-library-read")
        headers = {"Authorization": f"Bearer {bearer_token}"}

        request = requests.get(album_api, headers=headers, timeout=5)
        album_info = MetadataAlbum(**json.loads(request.content))

        self.cache_db.insert_replace_album(album_id, album_info)

        return album_info

    def get_artist_from_id(self, artist_id: str) -> MetadataArtist:
        """Get the artist information from the artist ID."""
        artist_cache = self.cache_db.get_artist_from_id(artist_id)
        if artist_cache:
            return artist_cache

        artist_api = f"{API_URL}/artists/{artist_id}"
        bearer_token = self.session.tokens().get("user-library-read")
        headers = {"Authorization": f"Bearer {bearer_token}"}

        request = requests.get(artist_api, headers=headers, timeout=5)
        artist_info = MetadataArtist(**json.loads(request.content))

        self.cache_db.insert_replace_artist(artist_id, artist_info)

        return artist_info

    def get_artist_albums(self, artist_id: str) -> list[str]:
        """Get all the albums for an artist."""
        artist_albums = []
        artist_albums_api = f"{API_URL}/artists/{artist_id}/albums?limit=50"
        bearer_token = self.session.tokens().get("user-library-read")
        headers = {"Authorization": f"Bearer {bearer_token}"}

        while True:  # We need to go through pages
            response = requests.get(artist_albums_api, headers=headers, timeout=5)
            artist_albums_info: AlbumListResult = AlbumListResult(**json.loads(response.content))

            for album_result in artist_albums_info.items:
                album_id = album_result.album.id
                artist_albums.append(album_id)

            if not artist_albums_info.next:
                break

            artist_albums_api = artist_albums_info.next + "&limit=50"

        return artist_albums

    def get_playlist_name_from_id(self, playlist_id: str) -> str:
        """Get the playlist name from the playlist ID."""
        playlist_api = f"{API_URL}/playlists/{playlist_id}"
        bearer_token = self.session.tokens().get("playlist-read-private")
        headers = {"Authorization": f"Bearer {bearer_token}"}

        request = requests.get(playlist_api, headers=headers, timeout=5)
        playlist_info = MetadataPlaylist(**json.loads(request.content))

        return playlist_info.name

    # This doesn't seem to give much extra metadata
    def get_track_from_id(self, track_id: str) -> MetadataTrack:
        """Get the track information from the track ID."""
        track_cache = self.cache_db.get_track_from_id(track_id)
        if track_cache:
            return track_cache

        track_api = f"{API_URL}/tracks/{track_id}"
        bearer_token = self.session.tokens().get("user-library-read")
        headers = {"Authorization": f"Bearer {bearer_token}"}

        response = requests.get(track_api, headers=headers, timeout=5)

        logger.info(json.dumps(response.json()))

        track_info = MetadataTrack(**json.loads(response.content))

        self.cache_db.insert_replace_track(track_id, track_info)

        logger.info(track_info.model_dump_json(indent=4))

        return track_info

    def like_album_list(self, liked_album_list: list[str]) -> None:
        """Like the albums in the list."""
        for album_id in liked_album_list:
            self.like_album(album_id)

    def like_album(self, album_id: str) -> None:
        """Like the album."""
        album = self.get_album_from_id(album_id)
        logger.info("Liking album: %s by %s", album.name, album.get_first_album_artist_str())

        like_album_api = f"{API_URL}/me/albums?ids={album_id}"
        bearer_token = self.session.tokens().get("user-library-modify")
        headers = {"Authorization": f"Bearer {bearer_token}"}

        requests.put(like_album_api, headers=headers, timeout=5)

    def print_liked_albums(self) -> None:
        """Print the liked album cache."""
        liked_album_cache = self.cache_db.get_liked_album_list_from_user_id(self.session.username())

        if not liked_album_cache:
            logger.error("No liked albums found in cache")
            return

        logger.info("Albums liked by user: %s", self.session.username())
        for album_id in liked_album_cache:
            album = self.get_album_from_id(album_id)
            logger.info(" %s by %s", album.name, album.get_first_album_artist_str())

        cli_newline()
        logger.info("Total liked albums: %s", len(liked_album_cache))
