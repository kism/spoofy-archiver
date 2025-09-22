"""Track downloader module for Spoofy Archiver."""

import time
from pathlib import Path
from typing import ClassVar

from pathvalidate import sanitize_filename, sanitize_filepath
from tqdm import tqdm

import mutagen
from librespot.audio.decoders import AudioQuality, VorbisOnlyAudioQuality
from librespot.core import Session
from librespot.metadata import TrackId
from spoofy_archiver.services.metadata import (
    MetadataAlbum,
    MetadataArtist,
    MetadataTrack,
    MetadataTrackFile,
    MetadataTrackSummary,
)
from spoofy_archiver.utils import SERVICE_NAME, DownloadDelayer, cli_newline, get_logger

logger = get_logger(__name__)

QUALITY_OPTIONS = [AudioQuality.VERY_HIGH, AudioQuality.HIGH, AudioQuality.NORMAL]

SERVICE_NAME_LOWER = SERVICE_NAME.lower()


class SpoofyTrackDownloader:
    """Class responsible for downloading and processing a specific Spoofy track."""

    # Class variables shared across all instances
    session: ClassVar[Session]
    delayer: ClassVar[DownloadDelayer]

    @classmethod
    def configure(cls, session: Session, download_delay: int = 30) -> None:
        """Configure the track downloader class with session and delay settings.

        Args:
            session: The Spoofy session
            download_delay: Delay between downloads in seconds
        """
        cls.session = session
        cls.delayer = DownloadDelayer(download_delay)

    def __init__(
        self,
        dest_dir: Path,
        track: MetadataTrack | MetadataTrackSummary,
        album: MetadataAlbum,
        album_artist: MetadataArtist,
    ) -> None:
        """Initialize the track downloader for a specific track.

        Args:
            dest_dir: The destination directory
            track: The track to download
            album: The album the track is from
            album_artist: The artist of the album
        """
        if SpoofyTrackDownloader.session is None or SpoofyTrackDownloader.delayer is None:
            msg = "SpoofyTrackDownloader.configure() must be called before instantiation"
            raise ValueError(msg)

        self.dest_dir = sanitize_filepath(dest_dir)
        self.track = track
        self.album = album
        self.album_artist = album_artist

        self.file_name = self._build_track_file_name()

        self.file_path = self.dest_dir / self.file_name
        self.file_path_temp = self.dest_dir / f"{self.file_name}.download"
        self.file_path_unavailable = self.dest_dir / f"{self.file_name}.unavailable"

    def download(self) -> None:
        """Download the track."""
        quality = QUALITY_OPTIONS[0]
        backoff = 30
        attempts = 5
        download_failed = True
        download_was_required = False

        for i in range(attempts):
            try:
                download_was_required = self._download_track(quality)
                download_failed = False
                break
            except RuntimeError as e:
                if "Cannot get alternative track" in str(e):
                    if i != len(QUALITY_OPTIONS) - 1:
                        new_quality = QUALITY_OPTIONS[i + 1]
                    else:
                        logger.warning("Failed to download track with any quality, continuing")
                        break
                    logger.warning("Failed to download track with quality %s, trying %s", quality, new_quality)
                    quality = new_quality
                    time.sleep(1)
            except Exception:
                backoff = backoff * 2  # 30, 60, 120, 240, 480
                logger.exception("Exception:")
                logger.exception("Backing off and trying again in %s seconds + random delay", backoff)
                self.delayer.delay(additional_delay=backoff)

        if download_failed:
            msg = (
                f"Failed to download: "
                f"'{self.album.name} {self.album_artist.name} {self.track.name}'"
                f" after {i + 1} attempts"
            )
            with self.file_path_unavailable.open("w") as f:
                f.write(msg)
            logger.error(msg)
            cli_newline()

        if download_was_required:  # If we actually downloaded a file from Spoofy
            self.delayer.delay()

    def _build_track_file_name(self) -> str:
        """Build the track file name.

        Returns:
            The sanitized filename
        """
        track_num_digits = 2
        if len(str(self.album.total_tracks)) > 1:
            track_num_digits = len(str(self.album.total_tracks))

        disc_indicator_str = ""
        total_discs = self.album.get_total_discs()
        if total_discs > 1:
            disc_num_digits = len(str(total_discs))
            disc_indicator_str = f"{str(self.track.disc_number).zfill(disc_num_digits)}-"

        track_number_str = str(self.track.track_number).zfill(track_num_digits)
        track_indicator_str = f"{disc_indicator_str}{track_number_str}"

        file_name_original = f"{track_indicator_str} {self.album_artist.name} - {self.track.name}.ogg"
        file_name = sanitize_filename(file_name_original)

        if file_name_original != file_name:
            logger.debug(
                "Sanitized filename '%s' to '%s'",
                file_name_original,
                file_name,
            )

        return file_name

    def _download_track(self, quality: AudioQuality = AudioQuality.VERY_HIGH) -> bool:
        """Download the track.

        Args:
            quality: The audio quality to download

        Returns:
            bool: Whether a download was required
        """
        self.dest_dir.mkdir(parents=True, exist_ok=True)

        # Remove old temp file if it exists
        if self.file_path_temp.exists():
            self.file_path_temp.unlink()

        if self.file_path_unavailable.exists():
            self.file_path_unavailable.unlink()

        # This is where the magic happens
        download_required = not self.file_path.exists()

        if download_required:
            # Prepare the stream
            logger.info(
                "Archiving: %s - %s - %s \n %s",
                self.album_artist.name,
                self.album.name,
                self.track.name,
                self.file_path,
            )
            track_id_real = TrackId.from_base62(self.track.id)
            stream = self.session.content_feeder().load(
                track_id_real, VorbisOnlyAudioQuality(quality), preload=False, halt_listener=None
            )

            # We don't know the file size, so we estimate it
            if quality == AudioQuality.VERY_HIGH:
                estimated_size = int(self.track.duration_ms * 0.320 * 128)
            elif quality == AudioQuality.HIGH:
                estimated_size = int(self.track.duration_ms * 0.160 * 128)
            else:  # quality == AudioQuality.NORMAL:
                estimated_size = int(self.track.duration_ms * 0.096 * 128)

            total_size = 0
            with self.file_path_temp.open("wb") as f:
                buffer_size = 8192
                with tqdm(leave=False, total=estimated_size, unit="B", unit_scale=True) as pbar:
                    while True:
                        buffer_stream = stream.input_stream.stream()
                        buffer = buffer_stream.read(buffer_size)
                        if not buffer:
                            buffer_stream.close()
                            # Manually set the total size if the pbar since we know it now
                            pbar.total = total_size
                            pbar.update(total_size - pbar.n)  # Fill the progress bar
                            pbar.refresh()
                            self.delayer.delay_short()
                            break
                        f.write(buffer)
                        buffer_size = len(buffer)
                        total_size += buffer_size
                        pbar.update(buffer_size)

            self.set_metadata(self.file_path_temp)
            self.check_file_duration(self.file_path_temp)
            Path(self.file_path_temp).rename(self.file_path)
        else:
            logger.trace("Track: %s already downloaded", self.track.name)
            self.set_metadata(self.file_path)
            self.check_file_duration(self.file_path)

        return download_required

    def set_metadata(self, file_path: Path) -> None:
        """Set the metadata for the file.

        Args:
            file_path: The path to the file
        """
        logger.debug("Setting Metadata for: %s", file_path)
        audio = mutagen.File(file_path)  # type: ignore[attr-defined]

        existing_file_metadata = MetadataTrackFile(**audio)
        new_track_metadata = MetadataTrackFile()

        new_track_metadata.artist = self.album.get_track_artist()
        new_track_metadata.album = self.album.name
        new_track_metadata.title = self.track.name
        new_track_metadata.tracknumber = str(self.track.track_number)
        new_track_metadata.discnumber = str(self.track.disc_number)
        new_track_metadata.date = self.album.release_date
        new_track_metadata.albumartist = self.album.get_first_album_artist_str()
        new_track_metadata.totaldiscs = str(self.album.get_total_discs())
        new_track_metadata.totaltracks = str(self.album.total_tracks)

        if hasattr(self.album, "genre"):
            new_track_metadata.genre = self.album.genre
        elif hasattr(self.album_artist, "genre"):
            new_track_metadata.genre = self.album_artist.genre

        def capitailise_all_words(string: str) -> str:
            return " ".join([word.capitalize() for word in string.split()])

        if self.album.genres != []:
            new_track_metadata.genres = ", ".join([capitailise_all_words(genre) for genre in self.album.genres])
        elif self.album_artist.genres != []:
            new_track_metadata.genres = ", ".join([capitailise_all_words(genre) for genre in self.album_artist.genres])

        if hasattr(self.album, "upc"):
            new_track_metadata.upc = self.album.upc

        if existing_file_metadata == new_track_metadata:
            logger.trace("Metadata is already correct, no update required")
            return

        logger.debug("Setting metadata")

        # Set all non-None fields from new metadata to audio file
        for field_name, field_value in new_track_metadata.model_dump().items():
            if field_value is not None:  # Only set non-None values
                audio[field_name] = field_value

        audio[f"{SERVICE_NAME_LOWER}albumid"] = self.album.id
        audio[f"{SERVICE_NAME_LOWER}trackid"] = self.track.id
        audio[f"{SERVICE_NAME_LOWER}artistid"] = self.album_artist.id

        audio.save()

    def check_file_duration(self, file_path: Path) -> None:
        """Check the file duration.

        Args:
            file_path: The path to the file
        """
        max_diff_ms = 1001  # 1001 + 1ms for rounding errors, assumes Spoofy rounds nearly well.

        spoofy_reported_duration_ms = self.track.duration_ms
        audio = mutagen.File(file_path)  # type: ignore[attr-defined]

        try:
            audio_duration_ms = int(audio.info.length * 1000)
        except AttributeError:
            audio_duration_ms = 0

        # We don't care if the file is longer than reported, since sometimes they don't consider added silence.
        song_length_diff = spoofy_reported_duration_ms - audio_duration_ms
        if song_length_diff > max_diff_ms:
            logger.warning(
                "File duration mismatch with %s metadata: %s: %s != %s, diff: %s",
                SERVICE_NAME,
                self.file_path,
                audio_duration_ms,
                spoofy_reported_duration_ms,
                song_length_diff,
            )
