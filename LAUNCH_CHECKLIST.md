# Launch checklist

What is left between the repository as it stands and a site on the public
internet. Checked items are already done and are listed so nobody redoes them.
Everything unchecked is work.

## Serving it

- [x] **`app.run` is guarded.** It sits under `if __name__ == "__main__":`, so
      importing `app` from a WSGI server or a test never starts the development
      server.
- [ ] **Stop using the development server, and its debug flag.** The guarded
      call is still `app.run(debug=True, port=5002)`. The debug flag ships an
      interactive Python console to anyone who can trigger a traceback, and
      Flask's own server is single threaded and not hardened. In production run
      the app through a WSGI server instead, for example
      `waitress-serve --port=8000 app:app` on Windows or
      `gunicorn -w 4 -b 0.0.0.0:8000 app:app` on Linux, and add that server to
      `requirements.txt`. Neither is installed or listed yet. Take
      `debug=True` out of the guarded call too, so running the file directly on
      a server is not a way back to the console.
- [ ] **Set `FLASK_DEBUG=0` and `FLASK_ENV=production`** in the deployment
      environment, so a stray default cannot turn the console back on.
- [ ] **Put a reverse proxy in front** (nginx, Caddy, or whatever the host
      provides) to terminate TLS, serve `static/` directly and set the cache
      headers. Flask should not be the thing on port 443. The app gzips its own
      JSON and HTML over 1 KB when the client asks; the proxy should compress
      `styles.css` and the scripts, which the app does not.
- [ ] **Decide the host.** Nothing in the app needs a database or background
      worker, so any platform that runs a Python process will do.
- [ ] **Cap the request size.** `app.config['MAX_CONTENT_LENGTH']` is unset.
      The graph endpoints parse whatever text arrives.
- [ ] **Rate limit the `/run_*` endpoints.** `/run_floyd_warshall` is cubic in
      the node count and `/run_sort` accepts up to 100 values; both are cheap
      to call and not free to answer.
- [ ] **Check the error pages.** There is no 404 or 500 handler, so Flask's
      plain defaults appear, outside the site's own layout.

## Domain and TLS

- [ ] **Register the custom domain** and point an A or CNAME record at the host.
- [ ] **Get a certificate** and force HTTPS, including a redirect from the
      bare domain or `www`, whichever is not canonical.
- [ ] **Pick one canonical hostname** and redirect the other to it, so the
      same page does not exist at two addresses.
- [ ] **Add HSTS** once HTTPS is confirmed working, not before.

## Identity on the page

- [x] **SVG favicon.** `static/favicon.svg`, four bars on a dark rounded
      square, linked from `templates/layout.html`.
- [ ] **A PNG fallback and an apple-touch-icon.** Safari and older Android do
      not use the SVG. 180x180 for the touch icon, 32x32 and 16x16 PNGs.
- [ ] **A `site.webmanifest`** with the name, the icons and the theme colour,
      so the site can be added to a home screen.
- [ ] **A `<meta name="description">` per page.** There is none anywhere, so
      search results and link previews will quote whatever text comes first.
- [ ] **Open Graph and Twitter card tags**, with a share image. A link to this
      site currently previews as a bare URL.
- [x] **Theme colour for the browser chrome**, set for light and dark in
      `layout.html`.

## Legal and honesty

- [x] **Privacy policy** at `/privacy`. It says what is collected (nothing),
      names the two preferences kept in the browser (`theme` and
      `pbl2.codeLanguage` in localStorage, never sent to the server) and how to
      clear them, says what happens to what you type, and names the two outside
      services the pages call: Google Fonts and the D3 CDN. A test
      (`tests/test_privacy.py`) fails if the code starts using a key the page
      does not list.
- [x] **Terms and conditions** at `/terms`, covering what the tool is for, the
      absence of warranty, acceptable use and availability.
- [ ] **Re-read both against the final deployment.** If analytics, a contact
      form, error reporting or a CDN are added, the privacy page has to say so
      before that feature ships, which is what it promises.
- [ ] **Give the Contact section a real channel.** `/terms` currently says to
      use "whichever channel you were given the link", which is fine for a
      shared link and not fine on a public domain.
- [ ] **Add a LICENSE file** and say which licence in `README.md`. There is
      none at present, which legally means all rights reserved.
- [x] **No "made by AI" tag, badge or footer.** There is none anywhere in
      `templates/`, `static/` or the Python, and none should be added. The
      footer credit is the one the project uses:
      `Yash Maithani`.
- [ ] **Keep the credit line exactly as written** if the footer is ever
      touched. It is a project rule, not a preference.

## Content

- [ ] **Retire or rewrite `project_documentation/`.** Those four files describe
      a 2025 version of the project with ten algorithms and four graph
      algorithms, and now contradict `README.md`. Two of them are empty.
      Nothing in the app references any of them.
- [ ] **Proofread the lesson files once more.** Twenty of them in
      `static/js/lessons/`, and they are the only text on the site that makes
      factual claims about complexity.

## Dependencies

- [ ] **Self-host D3, or add a subresource integrity hash.**
      `graph_base.html` loads `https://d3js.org/d3.v7.min.js` with no
      `integrity` or `crossorigin` attribute, so the graph pages execute
      whatever that host returns.
- [ ] **Consider self-hosting the three typefaces.** `styles.css` imports them
      from Google Fonts, which is the only reason the privacy policy has a
      "requests to other services" section at all, and the `@import` blocks
      rendering until it resolves.
- [x] **`requirements.txt` matches what is imported.** Flask and pytest.
      `flask-cors` and `python-dotenv` were listed and used by nothing.

## Before every deploy

- [ ] The browser tests are installed, so `pytest` runs them instead of
      skipping them with a warning:
      `python -m pip install -r requirements-dev.txt` and
      `python -m playwright install chromium`.
- [ ] `pytest -q` passes, run on its own (about 13 minutes with the browser
      tests; two runs at once starve each other and time out).
- [ ] `python tools/check_banned_patterns.py .` exits 0.
- [ ] `node tests/validate_lessons.js` reports every lesson file valid.
- [ ] `python tools/extract_code.py --check` says the C, C++ and Java listings
      are current. If it does not, run `python tools/extract_code.py` and commit
      the files it writes.
- [ ] Every algorithm plays from the first step to the last, in both themes.
- [ ] No console errors on any page.
- [ ] The pages still hold at 375px, 768px and 1440px.
