#!/usr/bin/env python3
"""
Tell Bing (and every other IndexNow search engine) that URLs changed.

    python3 tools/indexnow.py --changed                 # html pages changed in the last commit
    python3 tools/indexnow.py https://nextstep3pl.com/blog/new-post/ ...
    python3 tools/indexnow.py --all                     # every URL in sitemap.xml

IndexNow is an open protocol (Bing, Yandex, Naver, Seznam and others share
submissions). Ownership is proven by a key file at the site root, so the file
<key>.txt next to index.html must be live BEFORE this runs — run it only after
the deploy has finished. Google does not use IndexNow; it relies on the sitemap
and Search Console.

Why it matters here: Bing's index feeds Copilot and parts of ChatGPT search, so
a page Bing has not seen is a page those assistants are less likely to cite.

Exit 0 on accepted (200/202), non-zero otherwise.
"""

import json
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
HOST = "nextstep3pl.com"
BASE = f"https://{HOST}"
ENDPOINT = "https://api.indexnow.org/indexnow"
KEY = (ROOT / "seo" / "indexnow.key").read_text().strip()
SKIP = {"seo", "tools", ".github", ".git"}


def url_for(rel: str) -> str:
    if rel == "index.html":
        return BASE + "/"
    if rel.endswith("/index.html"):
        return BASE + "/" + rel[: -len("index.html")]
    return BASE + "/" + rel


def changed_urls() -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()
    urls = []
    for f in out:
        if f.endswith(".html") and not (set(pathlib.Path(f).parts) & SKIP) and f != "404.html":
            if (ROOT / f).exists():
                urls.append(url_for(f))
    if "sitemap.xml" in out:
        urls.append(BASE + "/sitemap.xml")
    return urls


def all_urls() -> list[str]:
    return re.findall(r"<loc>(.*?)</loc>", (ROOT / "sitemap.xml").read_text(encoding="utf-8"))


def main(argv: list[str]) -> int:
    if "--changed" in argv:
        urls = changed_urls()
    elif "--all" in argv:
        urls = all_urls()
    else:
        urls = [a for a in argv if a.startswith("http")]
    urls = sorted(set(u for u in urls if u.startswith(BASE)))
    if not urls:
        print("nothing to submit")
        return 0

    # The key file must already be reachable, or IndexNow rejects the batch (403).
    try:
        with urllib.request.urlopen(f"{BASE}/{KEY}.txt", timeout=15) as r:
            if r.read().decode().strip() != KEY:
                print("key file is live but its contents do not match — deploy not finished?")
                return 2
    except Exception as e:
        print(f"key file {BASE}/{KEY}.txt not reachable yet ({e}). Wait for the deploy, then retry.")
        return 2

    body = json.dumps({"host": HOST, "key": KEY, "keyLocation": f"{BASE}/{KEY}.txt", "urlList": urls}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            code = r.status
    except urllib.error.HTTPError as e:
        code = e.code
    print(f"IndexNow: HTTP {code} for {len(urls)} URL(s)")
    for u in urls:
        print("  ", u)
    # 200 OK, 202 Accepted (key validation pending) are both success.
    return 0 if code in (200, 202) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
