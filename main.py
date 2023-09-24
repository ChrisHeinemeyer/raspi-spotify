import json
import logging
import platform
from dataclasses import asdict
from io import BytesIO
from typing import Dict, List, Tuple

import numpy as np
import requests
import spotipy
import yaml
from dacite import from_dict
from PIL import Image
from spotipy.oauth2 import SpotifyOAuth

from track import Album, Track

SECRETS_FILE = "secrets.yaml"  # pragma: allowlist secret
CONFIG_FILE = "config.yaml"
LOG_FILE = "log.log"
ALBUM_INFO_FILE = "album_info.json"
HEIGHT_PX = 448
WIDTH_PX = 600


def get_most_played_album() -> Album:
    logger = logging.getLogger(__name__)
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
    logger.debug([f"{a.artists[0].name} -  {a.name}: {c}" for a, c in counts])
    most_played_album = counts[0][0]
    logger.debug(f"Most played album: {most_played_album.name}")
    return counts[0][0]


def get_image_from_album(album: Album) -> Image:
    #   TODO find best sized image
    logger = logging.getLogger(__name__)
    logger.debug(f"Using image {asdict(album.images[0])}")
    url = album.images[0].url
    raw_img = requests.get(url)
    return Image.open(BytesIO(raw_img.content))


def resize_img(im: Image, height_px: int, width_px: int) -> Image:
    #  TODO remove assumption height is smaller than width
    logger = logging.getLogger(__name__)
    im = im.resize((height_px, height_px))
    bar_width_px = (width_px - height_px) // 2
    base_img = Image.new("RGB", (width_px, height_px), (0, 0, 0))
    base_img.paste(im, (bar_width_px, 0))
    logger.debug(f"Resized image to size {base_img.size}")
    return base_img


def main(config):
    logger = logging.getLogger(__name__)

    logger.debug("Starting")
    logger.debug(f"Using config {config}")
    try:
        with open(ALBUM_INFO_FILE, "r") as f:
            info = json.loads(f.read())
            previous_album = from_dict(Album, info)
        logger.debug(
            f"Previous record {previous_album.artists[0].name} - {previous_album.name} found"
        )
    except FileNotFoundError:
        logger.info(f"No previous record found")
        info = None

    album = get_most_played_album()
    need_update = True
    if info and info["uri"] == album.uri:
        logger.debug("Previous album matches current album")
        need_update = False

    if need_update or config["force_reload"]:
        logger.debug("Proceeding to get image")
        img = get_image_from_album(album)
        img = resize_img(img, HEIGHT_PX, WIDTH_PX)
        img.save("img.png")
        with open(ALBUM_INFO_FILE, "w") as f:
            f.write(json.dumps(asdict(album)))

        if platform.system() == "Linux":
            logger.debug(f"Setting display with saturation {config['saturation']}")
            from inky.auto import auto

            display = auto()
            display.set_image(img, saturation=config["saturation"])
            print(display.buf)
            buf = display.buf.copy()
            np.save("buf", buf)
            display.show()
            logger.debug("Done setting display")
        else:
            logger.debug(f"Can't set display on platform {platform.system()}")
    else:
        logger.debug("Not going to get or set image")

    logger.debug("Finished")


if __name__ == "__main__":
    with open(CONFIG_FILE) as f:
        config = yaml.safe_load(f)
    logging.basicConfig(
        filename=LOG_FILE,
        filemode="a",
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s: %(message)s",
    )
    logging.getLogger().addHandler(logging.StreamHandler())

    logging.getLogger("spotipy").setLevel(logging.INFO)
    logging.getLogger("requests").setLevel(logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.INFO)
    main(config)
