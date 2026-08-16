#!/usr/bin/env python3
"""
On-page SEO + integrity audit for the Next Step 3PL site.

Run from the repo root:      python3 tools/seo_audit.py
Machine-readable output:     python3 tools/seo_audit.py --json

Exit codes:
    0  no errors (warnings may still be present)
    1  at least one ERROR

This is the gate for the weekly automated run. Because content is published
straight to main and auto-deploys, nothing should be committed while this
script exits non-zero — an ERROR here means something is broken for real
users or search engines (a dead link, invalid schema, a page unreachable
from anywhere else on the site), not merely suboptimal.
"""

import json
import pathlib
import re
import sys
import urllib.parse
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://nextstep3pl.com"

# Google truncates around these lengths in desktop SERPs. Over-length is a
# display/CTR problem, not a ranking penalty, so these are warnings.
TITLE_MAX, TITLE_MIN = 60, 25
DESC_MAX, DESC_MIN = 160, 70

# Files that live in the repo but are never deployed / never indexed.
SKIP_DIRS = {"seo", "tools", ".github", ".git", "node_modules"}

errors, warnings, notes = [], [], []


def err(page, msg):
    errors.append({"page": str(page), "issue": msg})


def warn(page, msg):
    warnings.append({"page": str(page), "issue": msg})


def note(page, msg):
    notes.append({"page": str(page), "issue": msg})


def pages():
    for p in sorted(ROOT.rglob("*.html")):
        rel = p.relative_to(ROOT)
        if set(rel.parts) & SKIP_DIRS:
            continue
        yield rel, p.read_text(encoding="utf-8")


def url_for(rel):
    """Repo path -> site URL. index.html files become clean folder URLs."""
    s = str(rel)
    if s == "index.html":
        return "/"
    if s.endswith("/index.html"):
        return "/" + s[: -len("index.html")]
    return "/" + s


def check_head(rel, h):
    indexable = 'name="robots" content="noindex' not in h

    m = re.search(r"<title>(.*?)</title>", h, re.S)
    if not m or not m.group(1).strip():
        err(rel, "missing <title>")
    else:
        t = m.group(1).strip()
        if len(t) > TITLE_MAX:
            warn(rel, f"title is {len(t)} chars, truncates in SERPs above ~{TITLE_MAX}")
        if len(t) < TITLE_MIN:
            warn(rel, f"title is only {len(t)} chars — thin")

    m = re.search(r'<meta name="description" content="(.*?)"', h, re.S)
    if not m or not m.group(1).strip():
        err(rel, "missing meta description")
    else:
        d = m.group(1).strip()
        if len(d) > DESC_MAX:
            warn(rel, f"meta description is {len(d)} chars, truncates above ~{DESC_MAX}")
        if len(d) < DESC_MIN:
            warn(rel, f"meta description is only {len(d)} chars — thin")

    n_h1 = len(re.findall(r"<h1[\s>]", h))
    if n_h1 == 0:
        err(rel, "no <h1>")
    elif n_h1 > 1:
        warn(rel, f"{n_h1} <h1> tags — should be exactly one")

    if indexable:
        c = re.search(r'rel="canonical" href="(.*?)"', h)
        if not c:
            err(rel, "missing rel=canonical")
        else:
            expect = BASE + url_for(rel)
            if c.group(1) != expect:
                err(rel, f"canonical is {c.group(1)}, expected {expect}")

        for prop in ("og:title", "og:description", "og:image", "og:url"):
            if f'property="{prop}"' not in h:
                warn(rel, f"missing {prop}")

    for img in re.findall(r"<img[^>]*>", h):
        if "alt=" not in img:
            err(rel, "an <img> has no alt attribute")
        if "width=" not in img or "height=" not in img:
            note(rel, "an <img> has no width/height — can cause layout shift (CLS)")


def check_jsonld(rel, h):
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        try:
            data = json.loads(block)
        except json.JSONDecodeError as e:
            err(rel, f"invalid JSON-LD: {e}")
            continue
        for obj in data if isinstance(data, list) else [data]:
            if not isinstance(obj, dict):
                continue
            if "@context" not in obj:
                err(rel, "JSON-LD block has no @context")
            if "@type" not in obj:
                err(rel, "JSON-LD block has no @type")


def check_links(all_pages):
    """Internal links must resolve to a real file or a directory with an index."""
    inbound = defaultdict(set)
    for rel, h in all_pages:
        for href in re.findall(r'(?:href|src)="(/[^"#?]*)"', h):
            target = urllib.parse.unquote(href).lstrip("/")
            fs = ROOT / target
            ok = href == "/" or fs.is_file() or (fs.is_dir() and (fs / "index.html").is_file())
            if not ok:
                err(rel, f"broken internal link -> {href}")
            elif href.endswith("/") or href == "/":
                inbound[href].add(url_for(rel))

    # Orphan check: an indexable page nothing links to is invisible to crawlers.
    for rel, h in all_pages:
        if 'name="robots" content="noindex' in h:
            continue
        u = url_for(rel)
        if u == "/":
            continue
        if not (inbound[u] - {u}):
            warn(rel, "orphan page — no other page links to it")


def check_sitemap(all_pages):
    sm = ROOT / "sitemap.xml"
    if not sm.exists():
        err("sitemap.xml", "missing")
        return
    listed = set(re.findall(r"<loc>(.*?)</loc>", sm.read_text(encoding="utf-8")))
    listed_paths = {u.replace(BASE, "") or "/" for u in listed}

    live = set()
    for rel, h in all_pages:
        if 'name="robots" content="noindex' in h:
            continue
        live.add(url_for(rel))

    for missing in sorted(live - listed_paths):
        err("sitemap.xml", f"indexable page not in sitemap: {missing}")
    for stale in sorted(listed_paths - live):
        err("sitemap.xml", f"sitemap lists a page that no longer exists: {stale}")


def check_keyword_map(all_pages):
    kf = ROOT / "seo" / "keywords.json"
    if not kf.exists():
        return
    data = json.loads(kf.read_text(encoding="utf-8"))
    live = {url_for(rel) for rel, h in all_pages if 'content="noindex' not in h}

    seen = {}
    for t in data.get("targets", []):
        kw = t["primary"].lower()
        if kw in seen:
            err("seo/keywords.json",
                f"keyword cannibalisation: '{t['primary']}' targeted by both {seen[kw]} and {t['url']}")
        seen[kw] = t["url"]
        if t["url"] not in live:
            err("seo/keywords.json", f"targets a URL that does not exist: {t['url']}")

    for u in sorted(live - set(seen.values())):
        note("seo/keywords.json", f"live page has no target keyword assigned: {u}")


def main():
    all_pages = list(pages())
    for rel, h in all_pages:
        check_head(rel, h)
        check_jsonld(rel, h)
    check_links(all_pages)
    check_sitemap(all_pages)
    check_keyword_map(all_pages)

    if "--json" in sys.argv:
        print(json.dumps({"pages": len(all_pages), "errors": errors,
                          "warnings": warnings, "notes": notes}, indent=2))
    else:
        print(f"Audited {len(all_pages)} pages\n")
        for label, items in (("ERROR", errors), ("WARN", warnings), ("NOTE", notes)):
            if not items:
                continue
            print(f"--- {label} ({len(items)}) ---")
            for i in items:
                print(f"  {i['page']}: {i['issue']}")
            print()
        if not errors:
            print("No errors. Safe to commit." if not warnings
                  else "No errors (warnings above are advisory). Safe to commit.")
        else:
            print(f"{len(errors)} ERROR(S) — do not commit until these are fixed.")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
