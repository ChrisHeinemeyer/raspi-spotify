from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Track:
    uri: str
    album: Album
    artists: List[Artist]


@dataclass
class Artist:
    id: str
    name: str
    uri: str


@dataclass
class Album:
    album_type: str
    total_tracks: int
    id: str
    images: List[Image]
    name: str
    uri: str
    artists: List[Artist]


@dataclass
class Image:
    url: str
    height: int
    width: int
