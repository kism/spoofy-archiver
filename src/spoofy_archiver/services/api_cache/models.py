"""Models for the API cache service."""

from pydantic import BaseModel


class AlbumCacheSummary(BaseModel):
    """Summary of albums in the cache."""

    user_id: str
    last_updated: str
    n_albums: int
    first_album_listed_name: str

    def __str__(self) -> str:
        """String representation of the album cache summary."""
        return (
            f"User ID: {self.user_id}, "
            f" Last Updated: {self.last_updated}, "
            f" Number of Albums: {self.n_albums}, "
            f" Top of list: {self.first_album_listed_name}"
        )
