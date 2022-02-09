from pathlib import Path
import time
from typing import Tuple
import yaml
from io import BytesIO

import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import numpy as np
from PIL import Image


def load_secrets(path: Path = Path("./secret.yaml")) -> Tuple[str, str]:
    """Get the spotify API secrets.

    Args:
        path (Path, optional): The path of the secret yaml file. Defaults to Path("./secret.yaml"))

    Returns:
        Tuple([str, str]): Tuple of ID, secret
    """
    with open(path) as f:
        loaded = yaml.safe_load(f)
        return loaded['ID'], loaded['Secret']


def get_last_saved_track(sp: spotipy.Spotify) -> dict:
    """ Get a dict with information about the user's last saved track.

    Args:
        sp (spotipy.Spotify): A spotipy session

    Returns:
        dict: track
    """
    results = sp.current_user_saved_tracks(limit=1)
    return results['items'][0]['track']


def get_track_image(track: dict):
    url = track['album']['images'][0]['url']
    res = requests.get(url)
    img_arr = np.array(Image.open(BytesIO(res.content)))
    return img_arr


if __name__ == "__main__":
    app_id, app_secret = load_secrets()

    scope = "user-library-read"
    uri = "http://localhost:8888/callback"

    # sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=app_id, client_secret=app_secret))
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        scope=scope, redirect_uri=uri, client_id=app_id, client_secret=app_secret))

    first_scan = time.time()
    last_scan = time.time()
    while True:
        track = get_last_saved_track(sp)
        print(f"{track['artists'][0]['name']}  -  {track['name']}  - {track['album']['images'][0]['url']} ")
        print(f"{(last_scan - first_scan )//60} Minutes Elapsed")
        print()

        while time.time() - last_scan < 60:
            time.sleep(0.1)
            pass
        last_scan = time.time()
