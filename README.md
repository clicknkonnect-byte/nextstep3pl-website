# Next Step 3PL — nextstep3pl.com

Static marketing site for Next Step 3PL (Houston 3PL: fulfillment, warehousing,
container drayage, FBA prep, kitting). Plain HTML, CSS and vanilla JS —
no build step, no framework, no server-side code.

Previously hosted on Cloudflare Pages, now configured for **Hostinger shared hosting**.

---

## Structure

```
/                                   index.html — homepage (calculators, quote form)
/404.html                           custom not-found page
/.htaccess                          Hostinger/Apache config — see below
/assets/style.css                   all styles
/assets/app.js                      nav, scroll reveal, FAQ, calculators, quote form
/assets/img/*.jpg                   service card photos (Pexels — see below)
/<service>-houston/                 7 service pages
/3pl-fulfillment-<city>-tx/         4 city pages
/guides/                            guides index + 3 long-form guides
/sitemap.xml, /robots.txt           SEO
```

Every page is a folder with an `index.html`, so URLs stay clean (`/guides/` →
`/guides/index.html`). All internal links are root-relative (`/assets/...`),
which means **the site must be deployed at the domain root** (`public_html/`),
not inside a subfolder.

---

## What changed for the Hostinger move

Cloudflare Pages handled several things automatically that Apache needs told:

| Added | Why |
|---|---|
| `.htaccess` | HTTPS + non-www redirect, gzip, cache headers, security headers, 404 routing |
| `404.html` | Cloudflare served its own 404 page; Apache needs a real file |
| `.github/workflows/deploy.yml` | Replaces the Cloudflare Pages git integration |

Also fixed: a stray double quote in the homepage `LocalBusiness` JSON-LD
(`""areaServed"`) that made the whole structured-data block invalid.

No Cloudflare Workers, Functions, `_redirects` or `_headers` existed, so nothing
had to be rewritten — the site is fully portable static HTML.

---

## Deploying

### Option A — GitHub Actions over FTP (automatic on every push)

1. In hPanel go to **Files → FTP Accounts** and note the FTP hostname, username
   and password (create an account if there isn't one).
2. In this repo go to **Settings → Secrets and variables → Actions → New
   repository secret** and add three secrets:

   | Secret | Example |
   |---|---|
   | `FTP_SERVER` | `ftp.nextstep3pl.com` |
   | `FTP_USERNAME` | `u123456789.nextstep3pl` |
   | `FTP_PASSWORD` | *(the FTP password)* |

3. Push to `main`. The workflow uploads changed files to `public_html/`.
   Watch it under the **Actions** tab.

If the domain is an addon rather than the primary domain, change `server-dir`
in `.github/workflows/deploy.yml` to `domains/nextstep3pl.com/public_html/`.

### Option B — Hostinger's built-in Git (pull-based)

1. hPanel → **Advanced → GIT**.
2. Repository: this repo's URL. Branch: `main`. Install path: `public_html`
   (leave the directory field empty for the web root).
3. Click **Create**, then use **Deploy** after each push — or copy the
   **auto-deployment webhook URL** and paste it into this repo under
   **Settings → Webhooks** so pushes deploy themselves.

Private repos require Hostinger's SSH key to be added to the GitHub account
(hPanel shows the key; add it under GitHub → Settings → SSH and GPG keys).

### Option C — Manual upload

Zip the repo contents (not the folder itself) and extract into `public_html`
via hPanel → **File Manager**. Make sure hidden files are shown so `.htaccess`
comes along — without it you lose HTTPS redirects, caching and the 404 page.

---

## After the DNS switch

- [ ] Point the domain's nameservers/A record at Hostinger.
- [ ] hPanel → **Security → SSL** → issue the free Let's Encrypt certificate.
- [ ] Confirm `http://` and `www.` both land on `https://nextstep3pl.com`.
- [ ] Visit a nonsense URL and confirm the styled 404 page appears.
- [ ] Once HTTPS is confirmed, uncomment the HSTS line in `.htaccess`.
- [ ] Resubmit `https://nextstep3pl.com/sitemap.xml` in Google Search Console.
- [ ] Submit a test quote and confirm the email arrives at contact@nextstep3pl.com.

---

## Things to know

**Quote form** — `assets/app.js` posts to [Web3Forms](https://web3forms.com)
(access key is in the file) and opens WhatsApp with a prefilled message. It is a
third-party API call from the browser, so it works on any host. If quote emails
stop arriving, check the Web3Forms account before suspecting Hostinger.

**Hero video** — the homepage video is hosted on an external CloudFront bucket
(`d8j0ntlcm91z4.cloudfront.net`), left over from the tool that generated the
site. It is 19 MB and set to `autoplay preload="auto"`. It is deliberately not
self-hosted: serving 19 MB per visit from shared hosting would be slower than a
CDN and eats bandwidth. The trade-off is that the URL belongs to someone else
and could disappear. To take control of it, compress the file (an H.264 720p
version should land around 2-3 MB), commit it to `assets/video/`, and update the
`<video src>` on `index.html:101`.

**Service card photos** — the original icon tiles were replaced with photography
from [Pexels](https://www.pexels.com), which is free for commercial use with no
attribution required. All are self-hosted in `assets/img/` at 1500×792 (the
`.svc-img` aspect ratio is `72/38`, so replacements should match or they will be
centre-cropped). Sources:

| File | Pexels photo |
|---|---|
| `warehousing.jpg` | [5156696](https://www.pexels.com/photo/boxes-on-shelves-inside-a-warehouse-5156696/) |
| `drayage.jpg` | [30517083](https://www.pexels.com/photo/containers-and-cranes-at-hamburg-port-30517083/) |
| `fba.jpg` | [4483941](https://www.pexels.com/photo/worker-in-a-warehouse-4483941/) |
| `kitting.jpg` | [7857523](https://www.pexels.com/photo/close-up-of-person-packing-an-order-into-a-cardboard-box-7857523/) |
| `fbm.jpg` | [4440800](https://www.pexels.com/photo/stacks-of-boxes-ready-for-delivery-4440800/) |
| `b2b.jpg` | [34585120](https://www.pexels.com/photo/forklift-operators-loading-pallets-on-truck-34585120/) |

**Returns Management was removed** as a service. The page, its cards, footer
links, sitemap entry and the copy that referenced it are all gone, and
`.htaccess` 301-redirects the old `/returns-management-houston/` URL to
`/#services` so the indexed link doesn't 404.

**Editing** — no build step. Edit HTML/CSS/JS directly and push. CSS and JS are
cached for a year by `.htaccess`, so after changing `style.css` or `app.js`,
bump the query string in the tag that loads it (`style.css?v=2`) to force
browsers to pick up the change.

**Local preview** — root-relative paths need a server, not `file://`:

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000>.
