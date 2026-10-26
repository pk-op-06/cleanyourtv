"""Download the app logos from Wikimedia Commons as PNG renders into <folder> (make_white_hq.py reads them).

Usage: python3 -I themes/batman/make/fetch.py <folder>
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

UA = "papa-tv-setup/1.0 (personal TV launcher; contact: local)"
FILES = {
    "netflix_n": "File:Netflix 2016 N logo.svg",
    "netflix": "File:Netflix 2015 logo.svg",
    "prime": "File:Prime Video logo (2024).svg",
    "hotstar": "File:JioHotstar 2025.png",
    "youtube": "File:YouTube Logo 2017.svg",
    "sonyliv": "File:SonyLIV 2020.png",
    "zee5": "File:ZEE5 2025.svg",
    "vlc": "File:VLC Icon.svg",
}
out_dir = sys.argv[1]


def get(url):
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read()
            if body:
                return body
        except Exception as e:  # noqa: BLE001 - report and retry
            print(f"  retry {attempt + 1}: {e}")
        time.sleep(3 + attempt * 3)
    raise RuntimeError(f"failed: {url}")


# make_white_hq.py reads src/<name>.png (900 px) for JioHotstar, and hq/<name>.png (2400 px) for the vector logos.
HQ = {"netflix_n", "prime", "youtube", "zee5", "vlc"}
jobs = [("src", name, title, "900") for name, title in FILES.items()]
jobs += [("hq", name, title, "2400") for name, title in FILES.items() if name in HQ]
for sub, name, title, width in jobs:
    os.makedirs(os.path.join(out_dir, sub), exist_ok=True)
    dest = os.path.join(out_dir, sub, name + ".png")
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        print(f"{name}: already have it")
        continue
    q = urllib.parse.urlencode({"action": "query", "prop": "imageinfo", "iiprop": "url|mime",
                                "iiurlwidth": width, "format": "json", "titles": title})
    info = json.loads(get("https://commons.wikimedia.org/w/api.php?" + q))
    ii = list(info["query"]["pages"].values())[0]["imageinfo"][0]
    url = ii.get("thumburl") or ii["url"]
    time.sleep(2)
    data = get(url)
    with open(dest, "wb") as f:
        f.write(data)
    print(f"{name}: {len(data)} bytes from {title}")
    time.sleep(3)
