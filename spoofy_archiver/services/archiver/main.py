"""Archiver module for Spoofy Archiver."""

import time
from pathlib import Path

import requests
from librespot.core import Session
from pathvalidate import sanitize_filepath
from requests import RequestException

from spoofy_archiver.services.api.main import SpoofyAPISession
from spoofy_archiver.services.metadata import MetadataAlbum, MetadataArtist
from spoofy_archiver.services.track_downloader.main import SpoofyTrackDownloader
from spoofy_archiver.utils import DownloadDelayer, cli_newline
from spoofy_archiver.utils.logger import get_logger

from .constants import DOWNLOAD_URL

logger = get_logger(__name__)


class SpoofyArchiver(SpoofyAPISession):
    """Spoofy Archiver object, downloads tracks from Spoofy."""

    def __init__(self, session: Session, output_directory: str | Path, download_delay: int = 30) -> None:
        """Initialise the Spoofy Archiver."""
        self.download_delay = download_delay
        self.delayer = DownloadDelayer(download_delay)

        if isinstance(output_directory, str):
            output_directory = Path(output_directory)

        self.output_directory = output_directory

        # Configure the track downloader class
        SpoofyTrackDownloader.configure(session, download_delay)

        super().__init__(session, output_directory)

    def download_album(self, album_id: str) -> None:
        """Download one album."""
        self.download_albums([album_id])

    def download_albums(self, album_list: list[str]) -> None:
        """Download albums from a list of album IDs."""
        if len(album_list) == 1:
            logger.info("Downloading album: %s", album_list[0])
        else:
            logger.info(f"Downloading from list of {len(album_list)} albums")  # noqa: G004

        for album_id in album_list:
            album = self.get_album_from_id(album_id)
            album_artist = self.get_artist_from_id(album.get_first_artist_id())

            artist_file_path = self.output_directory / album.get_first_album_artist_str()
            self.download_artist_image(artist_file_path, album_artist)

            dest_dir = self.output_directory / album.get_first_album_artist_str() / album.name
            self.download_cover_art(dest_dir, album)

            for track in album.tracks.items:
                downloader = SpoofyTrackDownloader(dest_dir, track, album, album_artist)
                downloader.download()

        logger.info("Finished downloading albums")

        self.print_failed_downloads()

    def _requests_get(self, url: str) -> requests.Response | None:
        """Make a requests get with retries."""
        attempts = 5
        for _ in range(attempts):
            try:
                return requests.get(url, timeout=5)
            except RequestException:
                self.delayer.delay()

        return None

    def download_artist_image(self, dest_dir: Path, artist: MetadataArtist) -> None:
        """Download the artist image."""
        dest_dir = sanitize_filepath(dest_dir)
        artist_image_path = dest_dir / "artist.jpg"
        artist_image_path_current_year = dest_dir / f"artist_{time.localtime().tm_year!s}.jpg"

        if artist_image_path_current_year.exists():
            return

        logger.info("Downloading artist image for: %s", artist.name)

        artist_image = self._requests_get(artist.get_artist_image_url())
        artist_image_path.parent.mkdir(parents=True, exist_ok=True)

        if not artist_image:
            logger.warning("Failed to download artist image for: %s", artist.name)
            return

        for path in [artist_image_path, artist_image_path_current_year]:
            with path.open("wb") as f:
                f.write(artist_image.content)

    def download_cover_art(self, dest_dir: Path, album: MetadataAlbum) -> None:
        """Download the cover art for an album."""
        dest_dir = sanitize_filepath(dest_dir)
        cover_art_path = dest_dir / "cover.jpg"
        if cover_art_path.exists():
            return

        logger.info("Downloading cover art for: %s - %s", album.get_first_album_artist_str(), album.name)

        cover_art = self._requests_get(album.get_cover_art_url())

        if not cover_art:
            logger.warning("Failed to download cover art for: %s - %s", album.get_first_album_artist_str(), album.name)
            return

        cover_art_path.parent.mkdir(parents=True, exist_ok=True)
        with cover_art_path.open("wb") as f:
            f.write(cover_art.content)

    def print_liked_album_cache_summary(self) -> None:
        """Print the liked album cache."""
        liked_album_cache_summary = self.cache_db.get_liked_album_cache_summary()

        cli_newline()
        logger.info("Current user: %s", self.session.username())

        for cache_entry in liked_album_cache_summary:
            logger.info("\n%s", cache_entry)

        cli_newline()

    def get_liked_album_cache(self, user_id: str) -> list[str] | None:
        """Get the liked album cache."""
        return self.cache_db.get_liked_album_list_from_user_id(user_id, stale_cache_okay=True)

    def print_failed_downloads(self) -> None:
        """Print failed downloads."""
        failed_downloads = self.find_failed_downloads()

        if not failed_downloads:
            logger.info("No failed downloads found.")
            return

        msg = "Failed downloads: >>>"
        failed_downloads_file = ""
        for path in failed_downloads:
            msg += f"\n - {path}"
            failed_downloads_file += f"{path}\n"

        with self.output_directory.joinpath("spoofy-archiver_failed_downloads.txt").open("w") as f:
            f.write(failed_downloads_file)

        logger.error(msg)

    def find_failed_downloads(self) -> list[Path]:
        """Find failed downloads."""
        failed_downloads = list(self.output_directory.rglob("*.ogg.unavailable"))
        failed_downloads.sort()
        return failed_downloads

    def download_playlist(self, playlist_id: str) -> None:
        """Download a playlist."""
        playlist_tracks = self.get_playlist_tracks(playlist_id)
        playlist_name = self.get_playlist_name_from_id(playlist_id)
        logger.info("Downloading playlist: %s", playlist_name)
        self.download_tracks(playlist_tracks, playlist_name)

    def download_artist_albums(self, artist_id: str) -> None:
        """Download an artists albums."""
        artist_metadata = self.get_artist_from_id(artist_id)
        logger.info("Downloading albums for artist: %s", artist_metadata.name)
        artist_albums = self.get_artist_albums(artist_metadata.id)
        self.download_albums(artist_albums)

    def download_track(self, track_id: str) -> None:
        """Download a single track."""
        self.download_tracks([track_id])

    def download_tracks(self, track_list: list[str], playlist_name: str | None = None) -> None:
        """Download a list of tracks."""
        if len(track_list) == 1:
            logger.info("Downloading single track")
        else:
            logger.info(f"Downloading from list of {len(track_list)} tracks")  # noqa: G004
        playlist_local_items = []
        for track_id in track_list:
            track = self.get_track_from_id(track_id=track_id)

            track_metadata = self.get_track_from_id(track_id=track_id)

            album = self.get_album_from_id(track.album.id)
            album_artist = self.get_artist_from_id(album.get_first_artist_id())

            artist_file_path = self.output_directory / album_artist.name
            self.download_artist_image(artist_file_path, album_artist)

            dest_dir = self.output_directory / album_artist.name / album.name
            self.download_cover_art(dest_dir, album)

            downloader = SpoofyTrackDownloader(dest_dir, track_metadata, album, album_artist)
            if playlist_name:
                playlist_local_items.append(downloader.file_path)
            downloader.download()

        if playlist_name:
            self.create_playlist_m3u(playlist_name, playlist_local_items)

        self.print_failed_downloads()

    def create_playlist_m3u(self, playlist_name: str, playlist_local_items: list[Path]) -> None:
        """Create an M3U playlist."""
        playlist_path = self.output_directory / f"{playlist_name}.m3u"

        with playlist_path.open("w") as f:
            for item in playlist_local_items:
                f.write(f"{item}\n")

    def download_url(self, url: str) -> None:
        """Download based on a URL."""
        cli_newline()
        spoofy_url_expected_segments = 5

        # Define mapping of URL types to download methods within the function
        spoofy_supported_types = {
            "album": self.download_album,
            "track": self.download_track,
            "playlist": self.download_playlist,
            "artist": self.download_artist_albums,
        }

        # Cleanup url
        # Remove everything after ?
        url = url.split("?")[0]
        split_url = url.split("/")
        if len(split_url) != spoofy_url_expected_segments:
            msg = f"URL not in correct format, should be: {DOWNLOAD_URL}/<whatever>/<id>"
            raise ValueError(msg)

        spoofy_item_type = url.split("/")[3]
        media_id = url.split("/")[-1]

        if spoofy_item_type not in spoofy_supported_types:
            supported_types_str = ", ".join(spoofy_supported_types.keys())
            msg = f"URL type not supported: {spoofy_item_type}, supported types: {supported_types_str}"
            raise ValueError(msg)

        # Call the appropriate method directly from the dictionary
        spoofy_supported_types[spoofy_item_type](media_id)
