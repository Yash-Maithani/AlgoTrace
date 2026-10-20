# Launch checklist

What is left between the repository as it stands and AlgoTrace on the public internet.
Checked items are done and are listed so nobody redoes them. Everything unchecked is
work, and the first section says which of it is yours.

## What is left for you

The code side is finished. These are the steps only you can do, in order.

1. **Create the Render web service from the GitHub repo.** In Render: New, then
   Blueprint (it reads `render.yaml` from `main` of
   https://github.com/Yash-Maithani/AlgoTrace), or New, then Web Service and pick the
   repo with: runtime Python, build command `pip install -r requirements.txt`, start
   command `gunicorn wsgi:app --workers 2 --threads 2 --bind 0.0.0.0:$PORT --timeout 60`.
   Connect your GitHub account to Render when it asks. `autoDeploy` is on, so every
   `git push` to `main` redeploys.
2. **Set the environment variables** on the service (Environment tab):

   | Variable | Value |
   |---|---|
   | `SITE_URL` | `https://<your-service>.onrender.com` now, your custom domain later. No trailing slash. This is the only one you must type. |
   | `SECRET_KEY` | Render generates it from `render.yaml`. If you made the service by hand, paste any long random string. Nothing uses it today. |
   | `TRUST_PROXY` | `1` |
   | `FLASK_DEBUG` | `0` (or leave unset; never `1` in production) |
   | `PYTHON_VERSION` | `3.11.9` (`render.yaml` and `.python-version` already say so) |

3. **Check the deployed site**: `/`, `/robots.txt`, `/sitemap.xml` (every address in
   it should start with your `SITE_URL`), a graph page, and a 404 such as `/nope`.
   Paste the home page address into a social preview checker to see the card.
4. **Attach the custom domain.** In Render, Settings, Custom Domains, add the domain
   (and `www`). Render shows the DNS records to create: normally a `CNAME` for `www`
   pointing at `<your-service>.onrender.com`, and for the bare domain either the A
   records Render lists or an `ALIAS`/`ANAME` at registrars that offer one. Add them at
   your registrar, wait for Render to verify and issue the TLS certificate (minutes to a
   few hours), and choose the canonical host (bare or `www`) so the other redirects.
5. **Change `SITE_URL` to the custom domain** and let it redeploy, so canonical links,
   the sitemap and the social card use the new address.
6. **Turn on HSTS** at Render or in `siteconfig.py` once HTTPS is confirmed working on
   the final domain, and not before.
7. **Submit `https://<domain>/sitemap.xml`** in Google Search Console (and Bing
   Webmaster Tools) if you want the pages indexed.
8. **Give the Contact section in `/terms` a real channel** (an email address or the
   repository's issues page), and re-read `/privacy` and `/terms` against what you
   finally deployed.
9. **Proofread the twenty lesson files** once more. They are the only text that makes
   factual claims about complexity.

## Serving it

- [x] **`app.run` is guarded** by `if __name__ == "__main__":`, so importing `app`
      from a WSGI server or a test never starts the development server.
- [x] **Debug mode is off unless the environment turns it on.** The guarded call is
      `app.run(port=...)` with no `debug=True`; `FLASK_DEBUG=1` is the one switch, for
      your own machine.
- [x] **A production server.** `wsgi.py` is the entry point; `requirements.txt` installs
      `gunicorn` on Linux and `waitress` on Windows; `Procfile` and `render.yaml` start
      `gunicorn wsgi:app`. Locally on Windows: `waitress-serve --host=127.0.0.1
      --port=8000 wsgi:app` (README.md has the exact commands).
- [x] **`FLASK_DEBUG=0` is set in `render.yaml`**, so a stray default cannot turn the
      console back on.
- [x] **Secrets come from the environment.** `SECRET_KEY` is read from the environment
      and never has a literal in the code.
- [x] **Cap the request size.** `MAX_CONTENT_LENGTH` is 1 MB, and an oversized request
      is refused with a 413 before any endpoint reads it.
- [x] **Check the error pages.** `/nope` and an unhandled error give the site's own 404
      and 500 in its layout (JSON for the `/run_*` endpoints), marked `noindex`.
- [x] **Compression.** JSON and HTML over 1 KB are gzipped for clients that ask: a 100
      value bubble sort goes from 7.1 MB to about 256 KB.
- [ ] **Put a reverse proxy in front** if you host somewhere other than Render. Render
      already terminates TLS. Compress `styles.css` and the scripts there; the app only
      compresses JSON and HTML.
- [ ] **Rate limit the `/run_*` endpoints.** `/run_floyd_warshall` is cubic in the node
      count and `/run_sort` accepts up to 100 values; both are cheap to call and not
      free to answer. Render's free plan has no limiter; add one (for example
      Flask-Limiter, or the proxy's) before real traffic.

## Domain and TLS

- [ ] **Register the custom domain** and point it at the host (step 4 above).
- [ ] **Get a certificate** and force HTTPS. Render does both once the domain verifies.
- [ ] **Pick one canonical hostname** and redirect the other to it.
- [ ] **Add HSTS** once HTTPS is confirmed (step 6 above).
- [x] **Canonical links built from `SITE_URL`**, so the domain is a setting, not a code
      change.

## Identity on the page

- [x] **The name is AlgoTrace** in the header, every page title, the meta tags and the
      README. The footer credit is `Yash Maithani`, unchanged.
- [x] **SVG favicon.** `static/favicon.svg`, linked from `templates/layout.html`.
- [ ] **A PNG fallback and an apple-touch-icon.** Safari and older Android do not use
      the SVG. 180x180 for the touch icon, 32x32 and 16x16 PNGs.
- [ ] **A `site.webmanifest`** with the name, the icons and the theme colour, so the
      site can be added to a home screen.
- [x] **A meta description on every page**, different on each.
- [x] **Open Graph and Twitter card tags** on every page, with a 1200 x 630 share image
      (`static/og-image.png`, drawn from `static/og-image.svg`).
- [x] **`robots.txt` and `sitemap.xml`**, generated from the routes using `SITE_URL`,
      with the algorithm deep links.
- [x] **Theme colour for the browser chrome**, set for light and dark in `layout.html`.

## Legal and honesty

- [x] **Privacy policy** at `/privacy`. It says what is collected (nothing), names the
      two preferences kept in the browser (`theme` and `pbl2.codeLanguage` in
      localStorage, never sent to the server) and how to clear them, says what happens
      to what you type, and names the one outside service the pages call: Google Fonts.
      A test fails if the code starts using a key the page does not list.
- [x] **Terms and conditions** at `/terms`.
- [x] **MIT `LICENSE`** in Yash Maithani's name, and the README says so.
- [x] **No "made by AI" tag, badge or footer.** The footer credit is `Yash Maithani`.
- [ ] **Keep the credit line exactly as written** if the footer is ever touched. It is
      a project rule, not a preference.
- [ ] **Give the Contact section a real channel** (step 8 above).

## Content

- [x] **`project_documentation/` matches the site.** `Project_Summary.md` is written by
      hand; `Quick_Reference.md` and the `.txt` and `.html` documents are generated from
      the lesson files and the routes by `project_documentation/generate_docs.py`, and
      a test fails if they go stale.
- [ ] **Proofread the lesson files once more.** Twenty of them in `static/js/lessons/`
      (step 9 above).

## Dependencies

- [x] **D3 is self-hosted.** `static/vendor/d3.v7.min.js` is 7.9.0, the version the CDN
      served, with its ISC licence and its SHA-256 recorded in `static/vendor/README.md`.
      No page loads a script from another site, and the graph pages work with the
      network off.
- [x] **A Content-Security-Policy**: this site's scripts and styles and the Google Fonts
      it imports, a nonce on every inline script and style block, no inline event
      handlers, and `X-Content-Type-Options`, `Referrer-Policy` and `X-Frame-Options`.
      A browser test runs every page and every algorithm with the policy on and fails on
      any violation.
- [x] **Static files are cache busted** (`?v=` plus a content hash) and cached for a
      year; pages are revalidated on every visit.
- [ ] **Consider self-hosting the three typefaces.** `styles.css` imports them from
      Google Fonts, which is the only reason the privacy policy has a "requests to other
      services" section, and the `@import` blocks rendering until it resolves. They fall
      back to system fonts if the request fails.
- [x] **`requirements.txt` matches what is imported.** Flask, plus the production server
      for the platform. Test tools are in `requirements-dev.txt`.

## Before every deploy

- [ ] The browser tests are installed, so `pytest` runs them instead of skipping them
      with a warning: `python -m pip install -r requirements-dev.txt` and
      `python -m playwright install chromium`.
- [ ] `pytest -q` passes, run on its own (about 13 minutes with the browser tests; two
      runs at once starve each other and time out).
- [ ] `python tools/check_banned_patterns.py .` exits 0.
- [ ] `node tests/validate_lessons.js` reports every lesson file valid.
- [ ] `python tools/extract_code.py --check` says the C, C++ and Java listings are
      current. If it does not, run `python tools/extract_code.py` and commit the files it
      writes.
- [ ] `python project_documentation/generate_docs.py --check` says the documents are
      current.
- [ ] The site runs under the production server locally:
      `waitress-serve --host=127.0.0.1 --port=8000 wsgi:app`.
- [ ] Every algorithm plays from the first step to the last, in both themes.
- [ ] No console errors on any page.
- [ ] The pages still hold at 375px, 768px and 1440px.
