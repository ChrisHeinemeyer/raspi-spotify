from io import BytesIO
from typing import Dict, List, Tuple

import requests
import spotipy
import yaml
from dacite import from_dict
from PIL import Image
from spotipy.oauth2 import SpotifyOAuth

from track import Album, Track

SECRETS_FILE = "secrets.yaml"  # pragma: allowlist secret
HEIGHT_PX = 448
WIDTH_PX = 600


def get_most_played_album() -> Album:
    with open(SECRETS_FILE) as f:
        secrets = yaml.safe_load(f)

    scope = "user-read-recently-played"
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=secrets["spotify"]["client_id"],
            client_secret=secrets["spotify"]["client_secret"],
            redirect_uri="http://localhost:8888/callback",
            scope=scope,
        )
    )
    tracks = []
    results = sp.current_user_recently_played()
    for idx, item in enumerate(results["items"]):
        track = from_dict(Track, item["track"])
        tracks.append(track)

    albums: Dict[str, Album] = {t.album.uri: t.album for t in tracks}
    uris = [t.album.uri for t in tracks]
    counts: List[Tuple[Album, int]] = []
    for uri in set(uris):
        count = uris.count(uri)
        counts.append((albums[uri], count))

    counts = sorted(counts, key=lambda x: x[1], reverse=True)
    return counts[0][0]


def get_image_from_album(album: Album) -> Image:
    #   TODO find best sized image
    url = album.images[0].url
    raw_img = requests.get(url)
    return Image.open(BytesIO(raw_img.content))


def resize_img(im: Image, height_px: int, width_px: int) -> Image:
    #  TODO remove assumption height is smaller than width

    im = im.resize((height_px, height_px))
    bar_width_px = (width_px - height_px) // 2
    base_img = Image.new("RGB", (width_px, height_px), (0, 0, 0))
    base_img.paste(im, (bar_width_px, 0))
    return base_img


if __name__ == "__main__":
    album = get_most_played_album()
    img = get_image_from_album(album)
    img = resize_img(img, HEIGHT_PX, WIDTH_PX)
