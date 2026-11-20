# Weekly SEO run — playbook

This is the procedure the scheduled Claude task follows every Monday. It is
written to be executed without any memory of the conversation that created it.

**Repo:** `/Volumes/Bilal Sher/Claude Marketing agency/nextstep3pl-website`
**Publishes to:** `main` → Hostinger native Git auto-deploy → `public_html` (live in ~30s–2 min).
There is no GitHub Actions workflow — do not look for one and do not treat its absence as a broken deploy.

Because this publishes straight to the live site with no human review, the audit
gate in step 6 is not optional. **If `tools/seo_audit.py` exits non-zero, fix the
errors or abandon the run — never commit past a failing audit.**

---

## 0. Orient

```bash
cd "/Volumes/Bilal Sher/Claude Marketing agency/nextstep3pl-website"
git pull --rebase
python3 tools/seo_audit.py
```

If the audit reports errors *before* you have changed anything, something upstream
broke. Fix that first and skip the content work this week.

## 1. Health check

- Confirm the live site responds: `curl -sI https://nextstep3pl.com | head -1`
- Confirm the deploy chain works by comparing a live URL against the repo file, e.g.
  `curl -s https://nextstep3pl.com/robots.txt | md5 -q` against `md5 -q robots.txt`.
  If they differ with no commit pending, auto-deploy is stuck — say so in the report
  before publishing more, otherwise this week's work silently never goes live.

## 2. Rankings

The site owner has Google Search Console verified and collecting. GSC cannot be
queried from here without credentials, so either:

- **Preferred:** ask the owner to export *Performance → Queries → last 28 days* as
  CSV and drop it at `seo/gsc-latest.csv` (gitignored). If that file exists and is
  recent, read it and update `"position"` for each target in `seo/keywords.json`.
- **Otherwise:** leave positions untouched and note in the summary that no fresh
  GSC data was available. Do not invent numbers, and do not substitute a live
  Google search — scraped SERPs are personalised and location-skewed, so they are
  not a rank measurement.

Flag in the summary: any target that moved more than 3 positions, anything that
dropped off page 1, and any query in the CSV with impressions but no matching page
(that is a content gap worth a post).

## 3. Fix before you add

Work through anything the audit flagged as WARN, in this order:
1. Broken links and orphan pages (they waste crawl budget).
2. Missing or duplicate titles / descriptions.
3. Over-length titles (>60) and descriptions (>160).
4. Pages with no target keyword in `seo/keywords.json`.

Existing pages that already rank are worth more than new ones. Improving a page
sitting at position 11 beats publishing a new post almost every time.

## 4. One post

Pick the next topic from `opportunities` in `seo/keywords.json`. Before writing,
confirm the primary keyword is not already claimed by another URL in `targets` —
two pages chasing one term cannibalise each other.

```bash
python3 tools/blog.py new \
  --slug "<kebab-case-slug>" \
  --title "<under 60 chars>" \
  --description "<120-160 chars>" \
  --lead "<one sentence>" \
  --eyebrow "<short label>" \
  --keyword "<primary keyword>" \
  --body "$(cat /tmp/body.html)"
```

Quality bar — this is a real business's public site, not a content farm:

- **900–1,500 words.** Long enough to be useful, short enough to be read.
- **Answer the question in the first two sentences.** Then earn the rest.
- **Concrete and specific to this business.** Houston, the Port, real numbers from
  the site (2 PM Central cut-off, ~$18/pallet, 60% of the US in two days, 120+
  integrations, 99.8% pick accuracy). Generic advice ranks nowhere.
- **2–4 internal links** to relevant service pages or guides, in natural prose.
- **No invented facts.** No fake statistics, no invented client stories, no made-up
  quotes or case studies. If a claim cannot be supported from the site's existing
  content, leave it out.
- **No filler.** No "in today's fast-paced world", no restating the title, no
  padding to hit a word count.

Then move the topic out of `opportunities` and add the new URL to `targets`.

## 5. Rebuild

```bash
python3 tools/blog.py index      # refresh /blog/ listing
python3 tools/build_sitemap.py   # sitemap + lastmod from git dates
```

If the post's topic overlaps an existing page, add a link *from* that page *to*
the new post as well. Internal links only help if they point both ways.

## 6. Gate

```bash
python3 tools/seo_audit.py
```

**Exit code must be 0.** Errors mean broken links, invalid schema, a page missing
from the sitemap, or keyword cannibalisation. None of those should reach the live
site. Warnings are advisory — judge them.

## 7. Publish

```bash
git add -A
git commit -m "Weekly SEO: <what changed>"
git push
```

Then confirm it is actually live. Poll the new or changed URL until it returns the
new content (usually under 2 minutes):

```bash
curl -s https://nextstep3pl.com/<new-path>/ | md5 -q      # compare with: md5 -q <new-path>/index.html
```

Do not report success until the live page matches the repo. A pushed commit that
never deployed means nothing changed for real visitors.

Once live, notify Bing and other IndexNow engines (Bing's index feeds Copilot and
parts of ChatGPT search, so an unseen page is a page assistants are less likely to
cite). Google is covered by the sitemap, which Search Console re-reads on its own:

```bash
python3 tools/indexnow.py --changed
```

Exit 0 means accepted. A non-zero exit because the key file is not yet reachable
just means the deploy has not finished — wait and retry; do not treat it as a failure
of the run.

## 8. Report

Write a short summary for the owner:
- What was published, with the live URL.
- Ranking movement (or that no GSC export was available).
- What the audit flagged and what was fixed.
- Anything needing a human: a directory listing to submit, a factual claim to
  confirm, a decision about scope.

Keep it to what changed and what needs them. No filler.

---

## Standing rules

- **Never invent facts about the business.** Pricing, capabilities, client names,
  volumes, certifications — if it is not already on the site or in
  `seo/business.json`, do not publish it. Ask instead.
- **Never submit directory listings or create accounts.** Prepare the copy in
  `seo/directories.md` and let the owner submit.
- **Never publish more than one post per run.** Google's spam policy targets
  scaled content abuse; a steady weekly cadence of genuinely useful pages is the
  entire strategy. Volume is the failure mode, not the goal.
- **NAP consistency:** any change to name, address or phone must be made in
  `seo/business.json` first, then propagated to every page's JSON-LD, `llms.txt`,
  the footer, and every live directory listing.
- **Keep `llms.txt` current.** When services or terms change, update it — it is
  what AI assistants read when someone asks them to recommend a Houston 3PL.
