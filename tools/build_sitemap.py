#!/usr/bin/env python3
"""
Regenerate sitemap.xml from what is actually on disk.

    python3 tools/build_sitemap.py

Every indexable page is included, noindex pages are skipped, and <lastmod> is
taken from the file's git commit date (falling back to mtime) so it reflects a
real edit rather than "whenever the script last ran". Search engines discount
sitemaps whose lastmod values all change on every build.

Priorities are assigned by depth/section, not hand-maintained — the homepage
outranks service pages, which outrank city pages, which outrank guides and blog
posts. Run this after adding or removing any page; the audit will fail if the
sitemap and the filesystem disagree.
"""

import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://nextstep3pl.com"
SKIP_DIRS = {"seo", "tools", ".github", ".git", "node_modules"}


def priority(url: str) -> str:
    if url == "/":
        return "1.0"
    if url.startswith("/blog/") and url != "/blog/":
        return "0.6"
    if url in ("/blog/", "/guides/"):
        return "0.7"
    if url.startswith("/guides/"):
        return "0.6"
    if re.match(r"^/3pl-fulfillment-[a-z-]+-tx/$", url):
        return "0.7"
    return "0.8"


def changefreq(url: str) -> str:
    if url == "/":
        return "weekly"
    if url in ("/blog/", "/guides/"):
        return "weekly"
    return "monthly"


def lastmod(path: pathlib.Path) -> str:
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", str(path.relative_to(ROOT))],
            cwd=ROOT, capture_output=True, text=True, timeout=10,
        )
        d = out.stdout.strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
            return d
    except Exception:
        pass
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).strftime("%Y-%m-%d")


def url_for(rel: pathlib.Path) -> str:
    s = str(rel)
    if s == "index.html":
        return "/"
    if s.endswith("/index.html"):
        return "/" + s[: -len("index.html")]
    return "/" + s


def main():
    entries = []
    for p in sorted(ROOT.rglob("*.html")):
        rel = p.relative_to(ROOT)
        if set(rel.parts) & SKIP_DIRS:
            continue
        h = p.read_text(encoding="utf-8")
        if 'name="robots" content="noindex' in h:
            continue
        u = url_for(rel)
        entries.append((u, lastmod(p)))

    # Homepage first, then by descending priority, then alphabetically —
    # purely for human readability of the file.
    entries.sort(key=lambda e: (e[0] != "/", -float(priority(e[0])), e[0]))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, lm in entries:
        lines.append(
            f"  <url><loc>{BASE}{u}</loc><lastmod>{lm}</lastmod>"
            f"<changefreq>{changefreq(u)}</changefreq>"
            f"<priority>{priority(u)}</priority></url>"
        )
    lines.append("</urlset>")

    (ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"sitemap.xml rebuilt — {len(entries)} URLs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
