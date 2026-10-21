# Launch checklist

What is left between the repository as it stands and AlgoTrace on the public internet.
Checked items are done and are listed so nobody redoes them. Everything unchecked is
work, and the first section says which of it is yours.

## Live

AlgoTrace is deployed on Render's free plan at **https://algotrace-zxiw.onrender.com**
(service `algotrace`, from the `main` branch of
https://github.com/Yash-Maithani/AlgoTrace, redeployed on every push). On the free plan the
service sleeps when idle and the first request after a pause can take up to a minute.

Smoke test of the live site, run after the first deploy: every page answered 200 and
`/nope` gave the site's 404; `robots.txt` and all 29 addresses in `sitemap.xml` use the
live address, as do the canonical and social image tags; `POST /run_sort`, `/run_search`,
`/run_bfs` and `/run_astar` returned valid steps; JSON and HTML came back gzipped with
`X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options` and the
Content-Security-Policy; and in a real browser at 1440 and 375 pixels the Home page, a
sort, BFS and A* ran with the first-visit tour, no console errors and no policy violations.

## What is left

Done:

- [x] **Render web service created from the GitHub repo**, with its environment variables
      set: `SITE_URL`, `SECRET_KEY` (generated), `TRUST_PROXY=1`, `FLASK_DEBUG=0`,
      `PYTHON_VERSION`, and optionally `RATE_LIMIT_PER_MINUTE` (30 if unset).
- [x] **The deployed site checked**: pages, 404, `robots.txt`, `sitemap.xml`, the run
      endpoints, compression and headers (see Live above).
- [x] **The Live demo line in `README.md`** has the deployed address.

Skipped for now (free onrender.com address):

- [ ] **Custom domain and DNS**: skipped for now (free onrender.com address). When you
      add one: in Render, Settings, Custom Domains, add the domain and `www`, create the
      DNS records Render shows (a `CNAME` for `www`, and the A records or an
      `ALIAS`/`ANAME` for the bare domain), wait for the certificate, choose the canonical
      host, then change `SITE_URL` to the new address so canonical links, the sitemap and
      the social card follow.
- [ ] **HSTS**: skipped for now (free onrender.com address). Turn it on in
      `algotrace/core/siteconfig.py` or at Render only once HTTPS is confirmed on the
      final domain.

Yours, optional:

1. **Set the repository's About box on GitHub** (the gear beside About on the repository
   page): website `https://algotrace-zxiw.onrender.com`; description "Step through 20
   sorting, searching and graph algorithms one move at a time, with the reason, the code
   line and the cost shown for every step."; topics `algorithms`, `data-structures`,
   `algorithm-visualization`, `sorting-algorithms`, `graph-algorithms`, `flask`,
   `education`, `big-o-notation`. Optionally upload `algotrace/static/og-image.png` under
   Settings, General, Social preview.
2. **Submit `https://algotrace-zxiw.onrender.com/sitemap.xml`** in Google Search Console
   (and Bing Webmaster Tools) if you want the pages indexed.
3. **Re-read `/privacy` and `/terms`** against what is deployed. The terms send questions
   to the repository's issues page; the privacy page lists Google Fonts as the one outside
   request.
4. **Proofread the twenty lesson files** once more. They are the only text that makes
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
- [x] **Rate limit the `/run_*` endpoints.** `algotrace/core/ratelimit.py`, standard library only: 30
      requests a minute per address (`RATE_LIMIT_PER_MINUTE`), then a JSON 429 with a
      `Retry-After` and a message every page shows to the student. It counts the address
      `TRUST_PROXY=1` reports, and ignores a forged `X-Forwarded-For` without it. The
      counts live in one process, so two gunicorn workers allow up to twice the limit;
      that stops a loop, which is the point. For a hard cap across workers, limit at
      the proxy as well.

## Domain and TLS

- [x] **HTTPS** on the free `onrender.com` address: Render terminates TLS.
- [ ] **Register the custom domain** and point it at the host: skipped for now (free
      onrender.com address).
- [ ] **Pick one canonical hostname** and redirect the other to it: skipped for now (free
      onrender.com address).
- [ ] **Add HSTS**: skipped for now (free onrender.com address).
- [x] **Canonical links built from `SITE_URL`**, so the domain is a setting, not a code
      change.

## Identity on the page

- [x] **The name is AlgoTrace** in the header, every page title, the meta tags and the
      README. The footer credit is `Yash Maithani`, unchanged.
- [x] **SVG favicon.** `static/favicon.svg`, linked from `templates/layout.html`.
- [x] **PNG icons and an apple-touch-icon**, drawn from `static/favicon.svg` by
      `tools/make_icons.py`: 32, 192 and 512 pixel PNGs and a 180 pixel touch icon,
      linked from the layout. (A 16 pixel PNG is not made; browsers take the SVG or the
      32 pixel file and scale it.)
- [x] **A web app manifest** at `/site.webmanifest`, with the name, the 192 and 512
      icons and the site's own colours, so the site can be added to a home screen. The
      Content-Security-Policy names `manifest-src 'self'`.
- [x] **A meta description on every page**, different on each.
- [x] **Open Graph and Twitter card tags** on every page, with a 1200 x 630 share image
      (`static/og-image.png`, drawn from `static/og-image.svg`).
- [x] **`robots.txt` and `sitemap.xml`**, generated from the routes using `SITE_URL`,
      with the algorithm deep links.
- [x] **Theme colour for the browser chrome**, set for light and dark in `layout.html`.

## Legal and honesty

- [x] **Privacy policy** at `/privacy`. It says what is collected (nothing), names the
      three small notes kept in the browser (`theme`, `pbl2.codeLanguage` and
      `pbl2.tourSeen` in localStorage, never sent to the server) and how to clear them, says what happens
      to what you type, and names the one outside service the pages call: Google Fonts.
      A test fails if the code starts using a key the page does not list.
- [x] **Terms and conditions** at `/terms`.
- [x] **MIT `LICENSE`** in Yash Maithani's name, and the README says so.
- [x] **No "made by AI" tag, badge or footer.** The footer credit is `Yash Maithani`.
- [ ] **Keep the credit line exactly as written** if the footer is ever touched. It is
      a project rule, not a preference.
- [x] **The Contact section in `/terms`** points to the repository's issues page, with no
      email address.

## Content

- [x] **`docs/project_documentation/` matches the site.** `Project_Summary.md` is written by
      hand; `Quick_Reference.md` and the `.txt` and `.html` documents are generated from
      the lesson files and the routes by `tools/generate_docs.py`, and
      a test fails if they go stale.
- [ ] **Proofread the lesson files once more.** Twenty of them in `static/js/lessons/`
      (the last item under What is left).

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

## The GitHub page

- [x] **README leads with the project**: what it does in one sentence, the demo GIF,
      screenshots, features, tech stack, how to run it and test it, structure, licence
      and author. The images are in `docs/screenshots/`, made by
      `tools/make_screenshots.py`.
- [x] **The Live demo line** in the README has the deployed address.
- [ ] **Set the About description and topics** on GitHub (first item under What is left;
      the GitHub CLI was not available here, so the values are listed for pasting).

## Before every deploy

- [ ] The browser tests are installed, so `pytest` runs them instead of skipping them
      with a warning: `python -m pip install -r requirements-dev.txt` and
      `python -m playwright install chromium`.
- [ ] `pytest -q` passes, run on its own (about 20 minutes with the browser tests; two
      runs at once starve each other and time out).
- [ ] `python tools/check_banned_patterns.py .` exits 0.
- [ ] `node tests/js/validate_lessons.js` reports every lesson file valid.
- [ ] `python tools/extract_code.py --check` says the C, C++ and Java listings are
      current. If it does not, run `python tools/extract_code.py` and commit the files it
      writes.
- [ ] `python tools/generate_docs.py --check` says the documents are
      current.
- [ ] The site runs under the production server locally:
      `waitress-serve --host=127.0.0.1 --port=8000 wsgi:app`.
- [ ] Every algorithm plays from the first step to the last, in both themes.
- [ ] No console errors on any page.
- [ ] The pages still hold at 375px, 768px and 1440px.
