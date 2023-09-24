from pprint import pprint
from typing import Dict, List, Tuple

import spotipy
import yaml
from dacite import from_dict
from spotipy.oauth2 import SpotifyOAuth

from track import Album, Track

SECRETS_FILE = "secrets.yaml"  # pragma: allowlist secret


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
    pprint(results, indent=2)
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


if __name__ == "__main__":
    print(get_most_played_album())
