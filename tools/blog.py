#!/usr/bin/env python3
"""
Blog tooling for the Next Step 3PL site.

    python3 tools/blog.py new  --slug how-to-choose-a-3pl \
                               --title "How to Choose a 3PL" \
                               --description "..." --lead "..." --keyword "how to choose a 3pl"
    python3 tools/blog.py index          # rebuild /blog/ from the posts on disk

Design note — why there is no posts.json:

The post HTML files ARE the database. `index` walks /blog/*/index.html and reads
each post's <title>, meta description and datePublished back out of the page
itself. A separate registry would be a second source of truth, and the two would
drift the first time someone edited a post by hand.

Page chrome (topbar, nav, footer, floating WhatsApp button, script tags) is not
hard-coded here either — it is lifted at build time from an existing page. Edit
the footer once on the real pages, re-run this, and the blog follows. CHROME_DONOR
must therefore always be a page that is currently correct.
"""

import argparse
import html
import json
import pathlib
import re
import sys
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"
BASE = "https://nextstep3pl.com"
CHROME_DONOR = ROOT / "guides" / "index.html"
DEFAULT_OG = "/assets/img/warehousing.jpg"

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com" />\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />\n'
    '<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;700;800;900'
    '&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet" />\n'
)
FAVICON = (
    '<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' '
    "viewBox='0 0 120 120'%3E%3Cpath d='M14 40 60 14 106 40 106 86 88 76 88 50 60 36 38 50Z' fill='%23EE7D28'/%3E"
    "%3Cpath d='M106 80 60 106 14 80 14 34 32 44 32 70 60 84 82 70Z' fill='%2316305A'/%3E%3C/svg%3E\" />\n"
)
CTA = (
    '<section class="cta-band"><div class="wrap cta-band-inner">\n'
    "  <div><h2>Ready to ship smarter from Houston?</h2><p>Get a quote in 24 hours. "
    "No setup fees, no long-term contracts.</p></div>\n"
    '  <a href="/#quote" class="btn btn-dark btn-lg">Get Your Quote →</a>\n'
    "</div></section>\n"
)


def chrome():
    """(header, footer) lifted from a live page so the blog always matches the site."""
    h = CHROME_DONOR.read_text(encoding="utf-8")
    head = h.split("<body>", 1)[1].split("<main>", 1)[0]
    foot = h.split("</main>", 1)[1]
    return head, foot


def page(title, description, canonical, body, extra_ld=(), og_image=DEFAULT_OG):
    head, foot = chrome()
    ld = "".join(
        f'<script type="application/ld+json">{json.dumps(o, ensure_ascii=False, separators=(",", ":"))}</script>\n'
        for o in extra_ld
    )
    e = html.escape
    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        '<meta charset="UTF-8" />\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'
        f"<title>{e(title)}</title>\n"
        f'<meta name="description" content="{e(description)}" />\n'
        f'<link rel="canonical" href="{BASE}{canonical}" />\n'
        f'<meta property="og:title" content="{e(title)}" />\n'
        f'<meta property="og:description" content="{e(description)}" />\n'
        f'<meta property="og:type" content="article" />\n'
        f'<meta property="og:url" content="{BASE}{canonical}" />\n'
        f'<meta property="og:site_name" content="Next Step 3PL" />\n'
        f'<meta property="og:image" content="{BASE}{og_image}" />\n'
        '<meta property="og:image:width" content="1500" />\n'
        '<meta property="og:image:height" content="792" />\n'
        '<meta name="twitter:card" content="summary_large_image" />\n'
        f'<meta name="twitter:image" content="{BASE}{og_image}" />\n'
        + FAVICON + FONTS +
        '<link rel="stylesheet" href="/assets/style.css" />\n'
        + ld +
        "</head>\n<body>" + head + "<main>\n" + body + "</main>" + foot
    )


def reading_time(body_html):
    words = len(re.sub(r"<[^>]+>", " ", body_html).split())
    return max(1, round(words / 220))


def cmd_new(a):
    slug = re.sub(r"[^a-z0-9-]", "", a.slug.lower())
    d = BLOG / slug
    if d.exists() and not a.force:
        sys.exit(f"{d} already exists (use --force to overwrite)")
    d.mkdir(parents=True, exist_ok=True)

    published = a.date or date.today().isoformat()
    url = f"/blog/{slug}/"
    e = html.escape

    body_inner = a.body or (
        "  <p>Opening paragraph — answer the reader's question in the first two "
        "sentences, then earn the rest of their attention.</p>\n"
        "  <h2>First section</h2>\n  <p>…</p>\n"
    )
    body = (
        '<section class="page-hero"><div class="wrap">\n'
        f'  <div class="breadcrumb"><a href="/">Home</a><span>›</span><a href="/blog/">Blog</a>'
        f"<span>›</span>{e(a.title)}</div>\n"
        f'  <span class="eyebrow">{e(a.eyebrow)}</span>\n'
        f"  <h1>{e(a.title)}</h1>\n"
        f'  <p class="lead">{e(a.lead)}</p>\n'
        f'  <div class="ph-meta">Published {published} · {reading_time(body_inner)} min read</div>\n'
        "</div></section>\n"
        '<section class="section"><div class="wrap prose reveal">\n'
        f"{body_inner}"
        "</div></section>\n"
        + CTA
    )

    article = {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": a.title, "description": a.description,
        "datePublished": published, "dateModified": published,
        "mainEntityOfPage": {"@type": "WebPage", "@id": BASE + url},
        "image": BASE + DEFAULT_OG,
        "author": {"@type": "Organization", "name": "Next Step 3PL", "url": BASE + "/"},
        "publisher": {"@type": "Organization", "name": "Next Step 3PL", "url": BASE + "/"},
    }
    crumbs = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": BASE + "/blog/"},
            {"@type": "ListItem", "position": 3, "name": a.title, "item": BASE + url},
        ],
    }

    (d / "index.html").write_text(
        page(a.title, a.description, url, body, [article, crumbs]), encoding="utf-8")
    print(f"created blog/{slug}/index.html")
    cmd_index(a)


def posts():
    """Read every post back out of its own HTML — the files are the database."""
    out = []
    for p in sorted(BLOG.glob("*/index.html")):
        h = p.read_text(encoding="utf-8")
        t = re.search(r"<title>(.*?)</title>", h, re.S)
        d = re.search(r'<meta name="description" content="(.*?)"', h, re.S)
        dt = re.search(r'"datePublished":"(\d{4}-\d{2}-\d{2})"', h)
        h1 = re.search(r"<h1>(.*?)</h1>", h, re.S)
        out.append({
            "slug": p.parent.name,
            "url": f"/blog/{p.parent.name}/",
            "title": html.unescape(re.sub(r"<[^>]+>", "", h1.group(1))) if h1
                     else (t.group(1).split(" | ")[0] if t else p.parent.name),
            "description": html.unescape(d.group(1)) if d else "",
            "date": dt.group(1) if dt else "1970-01-01",
        })
    out.sort(key=lambda x: x["date"], reverse=True)
    return out


def cmd_index(_a=None):
    BLOG.mkdir(exist_ok=True)
    ps = posts()
    e = html.escape
    cards = "".join(
        f'<a class="rel-card reveal" href="{p["url"]}"><h3>{e(p["title"])}</h3>'
        f'<span>{e(p["description"])}</span><br>'
        f'<span class="go">Read the post →</span></a>'
        for p in ps
    ) or '<p class="lead">The first post is on its way.</p>'

    body = (
        '<section class="page-hero"><div class="wrap">\n'
        '  <div class="breadcrumb"><a href="/">Home</a><span>›</span>Blog</div>\n'
        '  <span class="eyebrow">Blog</span>\n'
        "  <h1>Fulfillment &amp; logistics, explained</h1>\n"
        '  <p class="lead">Notes from the warehouse floor on shipping, storage, importing '
        "through the Port of Houston, and running a leaner supply chain.</p>\n"
        "</div></section>\n"
        f'<section class="section"><div class="wrap">\n  <div class="related-grid">{cards}</div>\n</div></section>\n'
        + CTA
    )
    ld = [{
        "@context": "https://schema.org", "@type": "Blog",
        "name": "Next Step 3PL Blog", "url": BASE + "/blog/",
        "description": "Fulfillment, warehousing and Port of Houston logistics explained.",
        "blogPost": [{"@type": "BlogPosting", "headline": p["title"],
                      "url": BASE + p["url"], "datePublished": p["date"]} for p in ps],
    }, {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": BASE + "/blog/"}],
    }]
    (BLOG / "index.html").write_text(
        page("Fulfillment & Logistics Blog | Next Step 3PL",
             "Practical writing on e-commerce fulfillment, warehousing, Amazon prep and "
             "importing through the Port of Houston.",
             "/blog/", body, ld), encoding="utf-8")
    print(f"blog/index.html rebuilt — {len(ps)} post(s)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new", help="scaffold a new post")
    n.add_argument("--slug", required=True)
    n.add_argument("--title", required=True)
    n.add_argument("--description", required=True, help="meta description, aim for 120-160 chars")
    n.add_argument("--lead", required=True, help="one-sentence standfirst under the H1")
    n.add_argument("--eyebrow", default="Guide")
    n.add_argument("--keyword", default="", help="primary target keyword (for your own records)")
    n.add_argument("--body", default="", help="inner HTML of the article")
    n.add_argument("--date", default="")
    n.add_argument("--force", action="store_true")
    n.set_defaults(func=cmd_new)
    i = sub.add_parser("index", help="rebuild /blog/ from posts on disk")
    i.set_defaults(func=cmd_index)
    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
