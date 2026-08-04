#!/usr/bin/env python3
"""Build an exact-order Spotify playlist from a fixed track list.

Unlike the generative playlist endpoint, this adds precisely the tracks named
below, in order. Two steps:

    python3 spotify_playlist.py auth     --client-id <ID>
    python3 spotify_playlist.py exchange --url '<redirect URL from browser>'
    python3 spotify_playlist.py build    --name "Electro"

Setup (once, ~2 min):
  1. https://developer.spotify.com/dashboard -> Create app
  2. Redirect URI: http://127.0.0.1:8888/callback  (must match exactly)
  3. Copy the Client ID. No client secret needed - this uses PKCE.

The auth step prints a URL. Open it, approve, and your browser lands on a
127.0.0.1 page that fails to load - that is expected. Copy the full URL from
the address bar and paste it back. The token is cached in .spotify_token.json.
"""

import argparse
import base64
import hashlib
import json
import os
import secrets
import sys
import time
import urllib.parse
import urllib.request

_HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(_HERE, ".spotify_token.json")
PENDING_FILE = os.path.join(_HERE, ".spotify_pending.json")
REDIRECT_URI = "http://127.0.0.1:8888/callback"
SCOPES = "playlist-modify-private playlist-modify-public"

# (title, artist, track_id_or_None). None -> resolved via search at build time.
TRACKS = [
    ("Planet Rock", "Afrika Bambaataa & The Soulsonic Force", "47oKxR5GOvACBjbGs3NNU5"),
    ("Clear", "Cybotron", None),
    ("Numbers", "Kraftwerk", "7l6zV8bdJs6LtYMdjAn2BJ"),
    ("Al-Naafiysh (The Soul)", "Hashim", "6nDk4QT1fDe0S86PxijTUE"),
    ("Bubble Metropolis", "Drexciya", "1fdDasmoFSBRdsuCLL3ger"),
    ("Egypt, Egypt", "Egyptian Lover", "0ALrGhYXdECH0nlCb7YuDw"),
    ("Hip Hop, Be Bop (Don't Stop)", "Man Parrish", "1vecbPvZamZvpq6cVJJ13G"),
    ("Pornoactress", "Dopplereffekt", "3w4GMecB6E8NXkzBfpDuiP"),
    ("Sex With The Machines", "Anthony Rother", None),
    ("Jam On It", "Newcleus", "1lB2kyB5h9ceZ388GBfC9L"),
    ("Andreaen Sand Dunes", "Drexciya", "5vcCF1Q328JhaZj4MS6XqO"),
    ("Scientist", "Dopplereffekt", "6u7uzFcfZXL9AeV7KWorJ9"),
    ("Hypervigilance", "DJ Stingray", None),
    ("Red Light District", "Anthony Rother", "6r9w4SQ3FpsYlUsUZi2ouM"),
    ("My A.U.X. Mind", "Aux 88", None),
    ("Wireless Internet", "Arpanet", "5OBdE4Tt5jXvMTRHy62QlU"),
    ("Subsonic", "Ectomorph", None),
    ("Nostalgia of Insanity", "Umwelt", None),
    ("Sworn to Secrecy Pt. II", "Helena Hauff", "1vnm5K1joDjpN674ooHvmV"),
    ("Point Blank", "Jensen Interceptor & Assembler Code", None),
    ("Submit X", "Gesloten Cirkel", "4E6Cq3mwPnPin3WIGu5msC"),
    ("Molecular Level Solutions", "DJ Stingray 313", None),
    ("Qualm", "Helena Hauff", "3luBPeJwqRYXk0DXInjfgz"),
    ("Inside", "VC-118A", "6A15XeFmy4IsAlfTyqOWOP"),
    ("Rev8617", "Skee Mask", None),
    ("Maintain the Golden Ratio", "Cybotron", None),
    ("Sentient", "Jensen Interceptor & Assembler Code", None),
    ("Rotary", "Silicon Scally", None),
    ("Nocturnal Cities", "Umwelt", None),
    ("The Truth", "The Exaltics", "4dtT9jAPPpgePCJ8eblDV2"),
]


def request(url, method="GET", token=None, data=None, form=None):
    headers = {}
    body = None
    if token:
        headers["Authorization"] = "Bearer " + token
    if form is not None:
        body = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        raise SystemExit("HTTP {} on {} {}\n{}".format(e.code, method, url, detail))


def cmd_auth(args):
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).decode().rstrip("=")
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")

    params = {
        "client_id": args.client_id,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "code_challenge_method": "S256",
        "code_challenge": challenge,
    }
    print("\nOpen this URL and approve:\n")
    print("https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params))
    print("\nYour browser will land on a 127.0.0.1 page that fails to load.")
    print("That is expected - copy the full URL from the address bar, then run:")
    print("  python3 {} exchange --url '<pasted URL>'\n".format(os.path.basename(__file__)))

    with open(PENDING_FILE, "w") as fh:
        json.dump({"verifier": verifier, "client_id": args.client_id}, fh)
    os.chmod(PENDING_FILE, 0o600)


def cmd_exchange(args):
    if not os.path.exists(PENDING_FILE):
        raise SystemExit("No pending auth. Run the 'auth' step first.")
    with open(PENDING_FILE) as fh:
        pending = json.load(fh)

    query = urllib.parse.urlparse(args.url).query
    parsed = urllib.parse.parse_qs(query)
    if "error" in parsed:
        raise SystemExit("Spotify returned an error: " + parsed["error"][0])
    code = parsed.get("code", [None])[0]
    if not code:
        raise SystemExit("No ?code= found in that URL.")

    tok = request(
        "https://accounts.spotify.com/api/token",
        method="POST",
        form={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": pending["client_id"],
            "code_verifier": pending["verifier"],
        },
    )
    os.remove(PENDING_FILE)
    tok["client_id"] = pending["client_id"]
    tok["expires_at"] = time.time() + tok.get("expires_in", 3600)
    with open(TOKEN_FILE, "w") as fh:
        json.dump(tok, fh)
    os.chmod(TOKEN_FILE, 0o600)
    print("\nToken saved to {}. Now run:\n  python3 {} build".format(
        TOKEN_FILE, os.path.basename(__file__)))


def load_token():
    if not os.path.exists(TOKEN_FILE):
        raise SystemExit("No token. Run the 'auth' step first.")
    with open(TOKEN_FILE) as fh:
        tok = json.load(fh)
    if tok.get("expires_at", 0) > time.time() + 60:
        return tok["access_token"]
    fresh = request(
        "https://accounts.spotify.com/api/token",
        method="POST",
        form={
            "grant_type": "refresh_token",
            "refresh_token": tok["refresh_token"],
            "client_id": tok["client_id"],
        },
    )
    tok.update(fresh)
    tok["expires_at"] = time.time() + fresh.get("expires_in", 3600)
    with open(TOKEN_FILE, "w") as fh:
        json.dump(tok, fh)
    return tok["access_token"]


def _norm(s):
    return "".join(c for c in s.lower() if c.isalnum())


REMIX_WORDS = ("remix", "rework", "edit", "version", "mix", "remaster", "re-edit")


def _artist_parts(artist):
    cleaned = artist.replace("&", ",").replace(" and ", ",")
    return [p.strip() for p in cleaned.split(",") if p.strip()]


def _score(hit, title, artist):
    """Rank a candidate. None means reject outright.

    Spotify always returns something and always looks confident, so both the
    artist and the title have to earn their match. Substring matching alone is
    too loose - it let 'Coki' match 'Anas Cokie' and 'Break' match
    'Heaven Break'.
    """
    got_names = [_norm(a["name"]) for a in hit["artists"]]
    want_words = {w for n in _artist_parts(artist) for w in _norm(n).split()}

    # Match whole names, or every word of the query name appearing in a credit.
    # Bare substrings are too permissive: they make ARTBAT match "Artbattle".
    name_words = [{_norm(w) for w in a["name"].split()} for a in hit["artists"]]
    artist_pts = 0
    for part in _artist_parts(artist):
        np, words = _norm(part), {_norm(w) for w in part.split()}
        if not np:
            continue
        if np in got_names:
            artist_pts = max(artist_pts, 4)
        elif any(words and words <= nw for nw in name_words):
            artist_pts = max(artist_pts, 3)
    if not artist_pts:
        return None

    got_title, want_title = _norm(hit["name"]), _norm(title)
    if got_title == want_title:
        title_pts = 5
    elif got_title.startswith(want_title):
        title_pts = 3
    elif want_title in got_title or got_title in want_title:
        title_pts = 1
    else:
        return None

    score = artist_pts + title_pts
    raw_title = hit["name"].lower()
    if any(w in raw_title for w in REMIX_WORDS) and not any(
            w in title.lower() for w in REMIX_WORDS):
        score -= 3
    # A remixer credited as an artist means this is somebody else's take.
    if len(got_names) > len(want_words) and "remix" in raw_title:
        score -= 1
    return score


def find_track(token, title, artist):
    """Search twice, score every candidate, keep the best."""
    attempts = [
        'track:"{}" artist:"{}"'.format(title, artist),
        "{} {}".format(title, artist),
    ]
    best, best_score = None, None
    for q in attempts:
        url = "https://api.spotify.com/v1/search?" + urllib.parse.urlencode(
            {"q": q, "type": "track", "limit": 10})  # 10 is the cap here
        for hit in request(url, token=token).get("tracks", {}).get("items", []):
            s = _score(hit, title, artist)
            if s is not None and (best_score is None or s > best_score):
                best, best_score = hit, s
        if best_score is not None and best_score >= 9:
            break  # exact artist + exact title; nothing will beat it
    return best


def load_track_file(path):
    """Read 'Artist - Title' lines. Blank lines and # comments are skipped."""
    out = []
    with open(path) as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if " - " not in line:
                raise SystemExit("{}:{}: expected 'Artist - Title', got: {}".format(
                    path, lineno, line))
            artist, title = line.split(" - ", 1)
            out.append((title.strip(), artist.strip(), None))
    return out


def cmd_build(args):
    token = load_token()
    tracks = load_track_file(args.file) if args.file else TRACKS

    uris, missing = [], []
    for title, artist, track_id in tracks:
        if track_id:
            uris.append("spotify:track:" + track_id)
            continue
        hit = find_track(token, title, artist)
        if hit:
            names = ", ".join(a["name"] for a in hit["artists"])
            got = "{} - {}".format(names, hit["name"])
            want = "{} - {}".format(artist, title)
            if _norm(got) != _norm(want):
                print("  variant: {}  ->  {}".format(want, got))
            uris.append(hit["uri"])
        else:
            missing.append("{} - {}".format(artist, title))

    # /v1/users/{id}/playlists is deprecated and now returns a bare 403.
    playlist = request(
        "https://api.spotify.com/v1/me/playlists",
        method="POST",
        token=token,
        data={"name": args.name, "public": False, "description": args.description},
    )
    # Must be /items, not /tracks. /tracks was renamed and now answers 403
    # Forbidden rather than 404, which reads like a permissions problem.
    for i in range(0, len(uris), 100):
        request(
            "https://api.spotify.com/v1/playlists/{}/items".format(playlist["id"]),
            method="POST", token=token, data={"uris": uris[i:i + 100]},
        )

    print("\nCreated '{}' with {} tracks:".format(args.name, len(uris)))
    print(playlist["external_urls"]["spotify"])
    if missing:
        print("\nNot found on Spotify ({}):".format(len(missing)))
        for m in missing:
            print("  - " + m)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_auth = sub.add_parser("auth", help="step 1: print the authorize URL")
    p_auth.add_argument("--client-id", required=True)
    p_auth.set_defaults(func=cmd_auth)

    p_exch = sub.add_parser("exchange", help="step 2: trade the redirect URL for a token")
    p_exch.add_argument("--url", required=True, help="full redirect URL from your browser")
    p_exch.set_defaults(func=cmd_exchange)

    p_build = sub.add_parser("build", help="create the playlist")
    p_build.add_argument("--name", default="Electro")
    p_build.add_argument("--file", help="track list; 'Artist - Title' per line")
    p_build.add_argument("--description", default="")
    p_build.set_defaults(func=cmd_build)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
