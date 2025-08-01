"""Model for Tracks."""

from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from spoofy_archiver.utils import (
    get_logger,  # It's best to replace slashes here to un-confuse pathlib  # Replace slashes to un-confuse pathlib
    replace_slashes,  # It's best to replace slashes here to un-confuse pathlib
)

logger = get_logger(__name__)


# region Image
class MetadataImage(BaseModel):
    """Metadata for a Spoofy Artist Image."""

    model_config = ConfigDict(
        extra="ignore",
    )

    url: str
    height: int
    width: int


# region Artist
class MetadataArtist(BaseModel):
    """Metadata for a Spoofy Artist."""

    model_config = ConfigDict(
        extra="ignore",
    )

    id: str
    name: str
    genres: list[str] = []
    images: list[MetadataImage] = []

    @model_validator(mode="after")
    def validate_name(self) -> Self:
        """Validate the artist name."""
        self.name = replace_slashes(self.name)
        return self

    def get_artist_image_url(self) -> str:
        """Get the URL of the artist's image."""
        if self.images:
            return self.images[0].url
        return ""

    def get_genre(self) -> str:
        """Get the primary genre of the artist."""
        if self.genres:
            return self.genres[0].capitalize()
        return ""


# region Album Summary
class MetadataAlbumSummary(BaseModel):
    """Metadata for an album summary."""

    model_config = ConfigDict(
        extra="ignore",
    )

    artists: list[MetadataArtist]
    id: str
    name: str
    release_date: str
    total_tracks: int
    external_ids: dict[str, str] = {}
    images: list[MetadataImage] = []


# region Track Summary
class MetadataTrackSummary(BaseModel):
    """Metadata for a track, minus the album."""

    model_config = ConfigDict(
        extra="ignore",
    )

    id: str
    name: str
    artists: list[MetadataArtist]
    track_number: int
    disc_number: int
    duration_ms: int

    @model_validator(mode="after")
    def validate_name(self) -> Self:
        """Validate the track name."""
        self.name = replace_slashes(self.name)
        return self

    def get_artists_string(self) -> str:
        """Get a string of artist names."""
        return ", ".join([artist.name for artist in self.artists])


# region Track
class MetadataTrack(BaseModel):
    """Metadata for a track."""

    model_config = ConfigDict(
        extra="ignore",
    )

    id: str
    name: str
    artists: list[MetadataArtist]
    track_number: int
    disc_number: int
    duration_ms: int
    album: MetadataAlbumSummary

    @model_validator(mode="after")
    def validate_name(self) -> Self:
        """Validate the track name."""
        self.name = replace_slashes(self.name)
        return self

    def get_artists_string(self) -> str:
        """Get a string of artist names."""
        return ", ".join([artist.name for artist in self.artists])


class MetadataTrackList(BaseModel):
    """Metadata for a list of tracks."""

    model_config = ConfigDict(
        extra="ignore",
    )

    items: list[MetadataTrackSummary] = []
    next: str | None = None


# region Playlist
class MetadataPlaylist(BaseModel):
    """Metadata for a playlist."""

    model_config = ConfigDict(
        extra="ignore",
    )

    name: str

    @model_validator(mode="after")
    def validate_name(self) -> Self:
        """Validate the playlist name."""
        self.name = replace_slashes(self.name)
        return self


# region Album
class MetadataAlbum(BaseModel):
    """Metadata for an album."""

    model_config = ConfigDict(
        extra="ignore",
    )

    artists: list[MetadataArtist]
    id: str
    name: str
    release_date: str
    label: str
    genres: list[str] = []
    total_tracks: int
    tracks: MetadataTrackList
    external_ids: dict[str, str] = {}
    images: list[MetadataImage] = []

    def get_total_discs(self) -> int:
        """Get the total number of discs in the album."""
        return max(track.disc_number for track in self.tracks.items)

    def get_upc(self) -> str:
        """Get the UPC of the album."""
        return self.external_ids.get("upc", "")

    def get_track_artist(self) -> str:
        """Get a string of all artists in the album."""
        return ", ".join(artist.name for artist in self.artists)

    def get_first_artist_id(self) -> str:
        """Get the ID of the first artist in the album."""
        if len(self.artists) > 0:
            return self.artists[0].id
        return ""

    def get_first_album_artist_str(self) -> str:
        """Get the first artist in the album."""
        if len(self.artists) > 0:
            return self.artists[0].name
        return ""

    def get_cover_art_url(self) -> str:
        """Get the URL of the album's cover art."""
        if self.images:
            return self.images[0].url
        return ""


class AlbumListResult(BaseModel):
    """Result of an album list query."""

    class AlbumItems(BaseModel):
        """Items in the album list."""

        model_config = ConfigDict(
            extra="ignore",
        )

        added_at: str
        album: MetadataAlbum

    model_config = ConfigDict(
        extra="ignore",
    )

    next: str | None = None
    items: list[AlbumItems] = []
